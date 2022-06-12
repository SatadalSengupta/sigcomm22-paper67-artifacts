from datetime import timedelta
from ipaddress import IPv4Address
import itertools
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import os

##################################################

class TCPTraceConst(object):

    ##################################################

    def __init__(self, simulation_dir, log_interval, test=False):

        self._test = test
        
        self._tcptrace_flow_table   = {}
        self._tcptrace_packet_table = {}
        self._tcptrace_sample_count = 0
        self._tcptrace_rtt_samples  = {}

        self._resultsPath = os.path.join(simulation_dir, "tcptrace_const")
        if not os.path.exists(self._resultsPath):
            os.makedirs(self._resultsPath)

        ## Accounting
        self._logInterval              = log_interval # in ms
        self._firstEntryTime           = None
        self._latestEntryRound         = 0
        self._snapshotTime             = []
        self._intervalPacketsProcessed = 0
        self._intervalActiveFlows      = []
        self._intervalActivePackets    = []
        self._flowTableSize            = []
        self._packetTableSize          = []

        self.populate_missing_flows()

    ##################################################

    def _custom_print(self, text="", flush=True):
        print(text, flush=flush)

    ##################################################

    def _create_tcptrace_snapshot(self, t, explicit=False):

        # print("Creating snapshot at {}".format(t))

        if self._firstEntryTime is None:
            return

        ms_elapsed = (t - self._firstEntryTime)/timedelta(milliseconds=1)
        if len(self._snapshotTime) == 0:
            ms_cutoff  = (self._latestEntryRound + 1) * self._logInterval
        else:
            ms_cutoff  = max(self._snapshotTime[-1] + self._logInterval, (self._latestEntryRound + 1) * self._logInterval)

        # self._custom_print("In createSnapshot:: Entry round: {}; Cutoff: {}, Check for snapshot at time: {} ms".format(self._latestEntryRound, ms_cutoff, ms_elapsed))

        if ms_elapsed >= ms_cutoff or explicit:
            ## Record time
            self._snapshotTime.append(ms_elapsed)

            ## Record params
            self._intervalActivePackets.append(len(self._tcptrace_packet_table))
            
            flow_table_size_count = len(self._tcptrace_flow_table)
            for flow_key in self._tcptrace_flow_table:
                if self._tcptrace_flow_table[flow_key][0] == self._tcptrace_flow_table[flow_key][1]:
                    flow_table_size_count -= 1
            self._intervalActiveFlows.append(flow_table_size_count)

            ## Increment round
            self._latestEntryRound += 1

    ##################################################

    def _is_collapsed(self, flow_key):
        return self._tcptrace_flow_table[flow_key][0] == self._tcptrace_flow_table[flow_key][1]

    ##################################################

    def process_tcptrace_SEQ(self, packet):

        ## Logging
        self._create_tcptrace_snapshot(packet["timestamp"])

        ## Prep. flow key
        flow_key = (packet["ipsrc"], packet["ipdst"], packet["tcpsrc"], packet["tcpdst"])

        ### Handle flow table action

        ### Case 0: Drop if SYN packet or pure ACK
        is_syn = "S" in packet["tcpflags"]
        is_fin = "F" in packet["tcpflags"]
        is_rst = "R" in packet["tcpflags"]
        is_pure_ack = packet["tcpflags"] == "-A----" and packet["pktsize"] == 0
        
        # if is_syn or is_fin or is_rst or is_pure_ack: # No SYN and no FIN
        # if is_rst or is_pure_ack: # SYN allowed
        if is_syn or is_rst or is_pure_ack: # SYN not allowed
            if self._test: self._custom_print("TCPTRACE SEQ FT:: Packet is either a SYN, FIN, or RST packet or a pure ACK; DROP: {}".format(flow_key))
            ## Set action
            actionable_ft2pt = ("drop", None)
        
        else:
            ## Compute expected ACK
            exp_ack = packet["seqno"] + packet["pktsize"]
            if "S" in packet["tcpflags"] or "F" in packet["tcpflags"]: exp_ack += 1

            ## Cases: 1. Flow record for this flow exists; 2: Flow record for this flow doesn't exist

            ## Case 1: Flow record exists in the flow table and measurement range is open
            if flow_key in self._tcptrace_flow_table and not self._is_collapsed(flow_key):
                highest_byte_acked_or_rexmited, highest_expected_ack = self._tcptrace_flow_table[flow_key]
                if self._test: self._custom_print("TCPTRACE SEQ FT:: Flow record for key {} is found, retrieved record is: {}".format(
                                                    flow_key, self._tcptrace_flow_table[flow_key]))

                ## Case 1.1: Packet is either an extension to measurement range or ahead of the measurement range
                if packet["seqno"] >= highest_expected_ack:

                    ## Case 1.1.1: The new packet is an extension to the measurement range
                    if packet["seqno"] == highest_expected_ack:
                        self._tcptrace_flow_table[flow_key] = (highest_byte_acked_or_rexmited, exp_ack)
                    
                    ## Case 1.1.2: Restart the measurement range with latest packet since there's a gap in the sequence no. space
                    else:
                        self._tcptrace_flow_table[flow_key] = (packet["seqno"], exp_ack)
                    
                    if self._test: self._custom_print("TCPTRACE SEQ FT:: Extension to MR: Updated record for key {} is: {}".format(
                                                        flow_key, self._tcptrace_flow_table[flow_key]))

                    ## Actionable for PT is to insert the record
                    actionable_ft2pt = ("insert", "packet_record")
                
                ## Case 1.2: Collapse since violation to measurement range
                else:
                    self._tcptrace_flow_table[flow_key] = (exp_ack, exp_ack)

                    if self._test: self._custom_print("TCPTRACE SEQ FT:: Collapse MR: Updated record for key {} is: {}".format(
                                                        flow_key, self._tcptrace_flow_table[flow_key]))

                    ## Actionable for PT is to insert the record
                    actionable_ft2pt = ("drop", None)
        
            ## Case 2: Flow record does not exist in FT or collapsed FT; need to insert it
            else:
                self._tcptrace_flow_table[flow_key] = (packet["seqno"], exp_ack)

                if self._test: self._custom_print("TCPTRACE SEQ FT:: Insert into FT: Updated record for key {} is: {}".format(
                                                    flow_key, self._tcptrace_flow_table[flow_key]))

                ## Actionable for PT is to insert the record
                actionable_ft2pt = ("insert", "packet_record")

        if self._test: self._custom_print("TCPTRACE SEQ FT:: Actionable for PT: {}".format(actionable_ft2pt))
        
        ### Handle packet table action

        ## PT action is insert
        if actionable_ft2pt[0] == "insert":
            packet_key = (packet["ipsrc"], packet["ipdst"], packet["tcpsrc"], packet["tcpdst"], exp_ack)
            self._tcptrace_packet_table[packet_key] = (packet["timestamp"], packet["seqno"])
            if self._test: self._custom_print("TCPTRACE SEQ PT:: Flow key: {} || Packet record {} inserted".format(flow_key, packet_key))

        return

    ##################################################

    def process_tcptrace_ACK(self, packet):

        ## Logging
        self._create_tcptrace_snapshot(packet["timestamp"])

        # Handle ACK direction

        ## Identify 3 conditions:
        ## (1) Packets that slide without effect (Packets with neither ACK nor RST flags set)
        ## (2) Packets that result in removing flow entry (RST packets; when conf. interval collapses due to ACKs, entries are removed during contention)
        ## (3) Packets that result in RTT samples (RST packets with ACK set also count)

        ## Prep. flow key
        flow_key = (packet["ipdst"], packet["ipsrc"], packet["tcpdst"], packet["tcpsrc"])


        ## Case 0: Perform flow table processing
        # if "A" not in packet["tcpflags"] and "R" not in packet["tcpflags"]:
        is_syn = "S" in packet["tcpflags"]
        is_pure_syn = is_syn and "A" not in packet["tcpflags"]
        is_fin = "F" in packet["tcpflags"]
        is_rst = "R" in packet["tcpflags"]
        is_not_ack = "A" not in packet["tcpflags"]

        # if is_pure_syn or is_rst or is_not_ack: # SYN-ACK allowed
        # if is_syn or is_fin or is_rst or is_not_ack: # No SYN, no FIN
        if is_syn or is_rst or is_not_ack: # SYN-ACK not allowed
            if self._test: self._custom_print("TCPTRACE ACK FT:: Flow key: {} || Either SYN, FIN, RST ACK set or ACK not set; DROP".format(flow_key))
            actionables_ft2pt = ("drop", None)
        
        ## Case 1: RST is set but ACK is not: Collapse flow table record
        # elif "A" not in packet["tcpflags"] and "R" in packet["tcpflags"]:
            
        #     ## Case 1.1: Flow record exists and measurement range is open; collapse measurement range
        #     if flow_key in self._tcptrace_flow_table and not self._is_collapsed(flow_key):
        #         _, highest_expected_ack  = self._tcptrace_flow_table[flow_key]
        #         self._tcptrace_flow_table[flow_key] = (highest_expected_ack, highest_expected_ack)
        #         if self._test: self._custom_print("TCPTRACE ACK FT:: Flow key: {} || RST set but not ACK, collapse MR: {}".format(
        #                                             flow_key, self._tcptrace_flow_table[flow_key]))
        #         actionables_ft2pt = ("delete", flow_key + (highest_expected_ack, ))
            
        #     ## Case 1.2: Flow record doesn't exist; insert
        #     else:
        #         self._tcptrace_flow_table[flow_key] = (packet["ackno"], packet["ackno"])
        #         if self._test: self._custom_print("TCPTRACE ACK FT:: Flow key: {} || RST set but not ACK, insert collapsed MR: {}".format(
        #                                             flow_key, self._tcptrace_flow_table[flow_key]))
        #         actionables_ft2pt = ("drop", None)
        
        ## Case 2: ACK is set
        elif "A" in packet["tcpflags"]:

            ## Case 2.1: Haven't seen this flow yet or collapsed measurement range; insert collapsed record
            if flow_key not in self._tcptrace_flow_table or self._is_collapsed(flow_key):
                self._tcptrace_flow_table[flow_key] = (packet["ackno"], packet["ackno"])
                if self._test: self._custom_print("TCPTRACE ACK FT:: Flow record for key {} is NONE or MR is closed, DROP".format(flow_key))
                actionables_ft2pt = ("drop", None)
            
            ## Case 2.2: Flow record exists and measurement range is open
            else:
                highest_byte_acked_or_rexmited, highest_expected_ack = self._tcptrace_flow_table[flow_key]

                ## Case 2.2.1: Collapse flow table record if RST is set or ACK beyond measurement range
                # if "R" in packet["tcpflags"] or packet["ackno"] > highest_expected_ack or packet["ackno"] <= highest_byte_acked_or_rexmited:
                if packet["ackno"] < highest_byte_acked_or_rexmited or packet["ackno"] > highest_expected_ack:
                    if self._test: self._custom_print("TCPTRACE ACK FT:: Flow record for key {} shows that ACK is outside MR, DROP".format(flow_key))
                    actionables_ft2pt = ("drop", None)

                elif packet["ackno"] == highest_byte_acked_or_rexmited:
                    ## Duplicate ACK: delete flow table record
                    # new_highest_expected_ack = max(highest_expected_ack, packet["ackno"])
                    self._tcptrace_flow_table[flow_key] = (highest_expected_ack, highest_expected_ack)
                    # if "R" not in packet["tcpflags"]:
                    #     actionables_ft2pt = ("delete", flow_key + (highest_expected_ack, ))
                    # else:
                    #     actionables_ft2pt = ("match", "packet_record")
                    actionables_ft2pt = ("delete", flow_key + (highest_expected_ack, ))

                    if self._test:
                        # if "R" in packet["tcpflags"]:
                        #     self._custom_print("TCPTRACE ACK FT:: Flow key: {} || Deleted FT record since RST is set".format(flow_key))
                        if packet["ackno"] > highest_expected_ack:
                            self._custom_print("TCPTRACE ACK FT:: Flow key: {} || Deleted FT record since ACK# > highest eACK: {} > {}".format(
                                                flow_key, packet["ackno"], highest_expected_ack))
                        if packet["ackno"] <= highest_byte_acked_or_rexmited:
                            self._custom_print("TCPTRACE ACK FT:: Flow key: {} || Deleted FT record since ACK# <= highest byte ACKed/reTxed/affected (reordering): {} <= {}".format(
                                                flow_key, packet["ackno"], highest_byte_acked_or_rexmited))

                ## Case 2.2.2: Update flow table with ACK no. since ACK within measurement range
                elif highest_byte_acked_or_rexmited < packet["ackno"] and packet["ackno"] <= highest_expected_ack:
                    self._tcptrace_flow_table[flow_key] = (packet["ackno"], highest_expected_ack)
                    actionables_ft2pt = ("match", "packet_record")
                    if self._test: self._custom_print("TCPTRACE ACK FT:: Flow key: {} || ACK# within measurement range; updated measurement range is: {}".format(
                                                        flow_key, self._tcptrace_flow_table[flow_key]))
        
        else:
            actionables_ft2pt = ("drop", None)
               
        # Handle packet table action
        match_key = (packet["ipdst"], packet["ipsrc"], packet["tcpdst"], packet["tcpsrc"], packet["ackno"])

        ## Case 1: Action is delete
        if actionables_ft2pt[0] == "delete":
            if actionables_ft2pt[1] in self._tcptrace_packet_table:
                del self._tcptrace_packet_table[actionables_ft2pt[1]]
                if self._test: self._custom_print("TCPTRACE ACK PT:: Flow key: {} || Action is delete; packet record deleted: {}".format(flow_key, actionables_ft2pt[1]))
            else:
                if self._test: self._custom_print("TCPTRACE ACK PT:: Flow key: {} || Action is delete; packet record not found: {}".format(flow_key, actionables_ft2pt[1]))
        
        ## Case 2: Action is match
        elif actionables_ft2pt[0] == "match":
            if match_key in self._tcptrace_packet_table:
                ## Packet record exists: Delete packet record, compute RTT sample, and report
                packet_tstamp, packet_seqno = self._tcptrace_packet_table[match_key]
                del self._tcptrace_packet_table[match_key]
                rtt = (packet["timestamp"] - packet_tstamp)/timedelta(milliseconds=1)
                if flow_key not in self._tcptrace_rtt_samples:
                    self._tcptrace_rtt_samples[flow_key] = []
                self._tcptrace_rtt_samples[flow_key].append((packet_seqno, rtt))
                self._tcptrace_sample_count += 1
                if self._test: self._custom_print("TCPTRACE ACK PT:: Flow key: {} || Match key found: {}; RTT sample collected: {}".format(flow_key, match_key, rtt))
            else:
                if self._test: self._custom_print("TCPTRACE ACK PT:: Flow key: {} || Match key NOT found: {}".format(flow_key, match_key))

        return

    ##################################################

    def concludeRTTDict(self):
        for flow_key in self._tcptrace_flow_table:
            if flow_key not in self._tcptrace_rtt_samples:
                self._tcptrace_rtt_samples[flow_key] = []

    ##################################################

    def plot_tcptrace_stats(self, latest_tstamp):

        self._create_tcptrace_snapshot(latest_tstamp, True)
        
        sns_colors = itertools.cycle(sns.color_palette("bright"))
            
        plt.figure(figsize=(6,4))
        time_x = [t/1000 for t in self._snapshotTime]
        color = next(sns_colors)
        plt.plot(time_x, self._intervalActiveFlows, color=color, linestyle="-")
        plt.xlabel("Time (sec.)")
        plt.ylabel("No. of flow records")
        plt.title("No. of flow records vs. time")
        plt.tight_layout()
        plot_path = os.path.join(self._resultsPath, "tcptrace_flows_records.png")
        plt.savefig(plot_path, dpi=300)
        plt.clf()
        plt.close("all")

        plt.figure(figsize=(6,4))
        time_x = [t/1000 for t in self._snapshotTime]
        color = next(sns_colors)
        plt.plot(time_x, self._intervalActivePackets, color=color, linestyle="-")
        plt.xlabel("Time (sec.)")
        plt.ylabel("No. of packet records")
        plt.title("No. of packet records vs. time")
        plt.tight_layout()
        plot_path = os.path.join(self._resultsPath, "tcptrace_packet_records.png")
        plt.savefig(plot_path, dpi=300)
        plt.clf()
        plt.close("all")

    ##################################################

    def investigate_bias(self, flow_table):

        missing_flow = False
        for flow_key in self._tcptrace_rtt_samples:
            if len(self._tcptrace_rtt_samples[flow_key]) > 0:
                for (seqno, rtt) in self._tcptrace_rtt_samples[flow_key]:
                    if rtt >= 1000:
                        flow_record = flow_table.lookup(flow_key)
                        if flow_record is None:
                            self._custom_print("Investigation:: RTT is {} and flow record not in FT: {}".format(rtt, flow_key))
                            missing_flow = True
        if not missing_flow:
            self._custom_print("Investigation: All flows for RTT >= 1000 ms were found in the FT")

    ##################################################

    def populate_missing_flows(self):

        missing_flow_keys = []
        missing_flow_keys.append((IPv4Address('10.9.9.173'), IPv4Address('204.141.30.124'), 50276, 443))
        self._missing_flow_keys = missing_flow_keys

    ##################################################

    def spot_discrepancy(self, p4rtt_rtt_samples):

        ## Compare tcptrace_const and P4RTT sample counts and report where P4RTT > tcptrace_const which shouldn't happen
        flow_keys = self._tcptrace_flow_table.keys()
        for flow_key in flow_keys:
            if flow_key not in self._tcptrace_rtt_samples and flow_key in p4rtt_rtt_samples:
                self._custom_print("DISCREPANCY:: Flow key: {} in P4RTT but not in tcptrace_const")
            elif flow_key in self._tcptrace_rtt_samples and flow_key in p4rtt_rtt_samples:
                if len(p4rtt_rtt_samples[flow_key]) > len(self._tcptrace_rtt_samples[flow_key]):
                    self._custom_print("DISCREPANCY:: Flow key: {}; P4RTT count {} > tcptrace_const count {}".format(
                                        flow_key, len(p4rtt_rtt_samples[flow_key]), len(self._tcptrace_rtt_samples[flow_key])))                
    
    ##################################################

    # DISCREPANCY:: Flow key: (IPv4Address('10.9.254.219'), IPv4Address('64.125.62.185'), 53891, 443); P4RTT count 81 > tcptrace_const count 80
    # DISCREPANCY:: Flow key: (IPv4Address('10.9.50.173'), IPv4Address('50.239.204.25'), 58032, 443); P4RTT count 52 > tcptrace_const count 50
    # DISCREPANCY:: Flow key: (IPv4Address('10.9.235.215'), IPv4Address('51.255.75.36'), 52570, 443); P4RTT count 5 > tcptrace_const count 4
    # DISCREPANCY:: Flow key: (IPv4Address('10.9.198.166'), IPv4Address('13.224.215.103'), 49659, 443); P4RTT count 5 > tcptrace_const count 4
    # DISCREPANCY:: Flow key: (IPv4Address('140.180.238.63'), IPv4Address('37.49.230.124'), 25, 57023); P4RTT count 2 > tcptrace_const count 1
    # DISCREPANCY:: Flow key: (IPv4Address('140.180.238.63'), IPv4Address('117.64.235.221'), 25, 58394); P4RTT count 2 > tcptrace_const count 1
    # DISCREPANCY:: Flow key: (IPv4Address('140.180.238.63'), IPv4Address('117.64.235.221'), 25, 60716); P4RTT count 2 > tcptrace_const count 1

##################################################
