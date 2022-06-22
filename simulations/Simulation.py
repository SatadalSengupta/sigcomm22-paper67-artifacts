from defined_subnets import PU_SNETS, DEFINED_SUBNETS
from ipaddress import IPv4Address, ip_network
from datetime import datetime, timedelta
from PacketTable import PacketTable
from FlowTable import FlowTable
from ApproxFlowTable import ApproxFlowTable
from TCPTraceConst import TCPTraceConst
from Plotter import Plotter
from shutil import copy, move
import itertools
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import scipy.stats as st
import pickle
import json
import sys
import os

##################################################

class Simulation(object):

    ##################################################

    def __init__(self, simulation_params, test=True):

        if False:
            self._custom_print("RECHECK:: Simulation params received: {}".format(simulation_params))

        ## Unique flows
        self._all_flows_seq_pkts = {}
        self._all_flows_ack_pkts = {}

        ## Common params
        self._test                 = test
        self._sim_start_time       = simulation_params["sim_params"]["start_time"]
        self._tcptrace_data_paths  = simulation_params["sim_params"]["tcptrace_data_paths"]
        self._simulation_batch_dir = simulation_params["sim_params"]["sim_batch_dir"]
        self._round_number         = simulation_params["sim_params"]["round_number"]
        self._max_round_number     = simulation_params["sim_params"]["combinations_count"] - 1
        self._total_packets_count  = simulation_params["sim_params"]["tcptrace_data_paths"]["total_packets_count"]
        self._packets_count        = 0
        self._packets              = None
        self._curr_packets_count   = None
        self._enable_apxft         = simulation_params["sim_params"]["enable_apxft"]

        str_len = len(str(simulation_params["sim_params"]["combinations_count"]))
        self._simulation_dir = os.path.join(self._simulation_batch_dir, "simulation_round_{}".format(str(self._round_number).zfill(str_len)))

        ## Create simulation directory
        if not os.path.exists(self._simulation_dir):
            self._custom_print("{} Round {}/{}: Create directory: {}".format(self._time_elapsed(), self._round_number, self._max_round_number, self._simulation_dir))
            os.makedirs(self._simulation_dir)

        # ## Populate packets data
        # self._build_packets_data()

        ## Add extra params
        simulation_params["flowtab_params"]["round_num"]        = self._round_number
        simulation_params["packettab_params"]["round_num"]      = self._round_number
        simulation_params["flowtab_params"]["max_round_num"]    = self._max_round_number
        simulation_params["packettab_params"]["max_round_num"]  = self._max_round_number
        simulation_params["flowtab_params"]["results_path"]     = self._simulation_dir
        simulation_params["packettab_params"]["results_path"]   = self._simulation_dir
        simulation_params["flowtab_params"]["total_packets"]    = self._total_packets_count
        simulation_params["packettab_params"]["total_packets"]  = self._total_packets_count
        
        if self._enable_apxft:
            simulation_params["apxflowtab_params"]["round_num"]     = self._round_number
            simulation_params["apxflowtab_params"]["max_round_num"] = self._max_round_number
            simulation_params["apxflowtab_params"]["results_path"]  = self._simulation_dir
            simulation_params["apxflowtab_params"]["total_packets"] = self._total_packets_count

        ## Table params
        self._flowtab_params    = simulation_params["flowtab_params"]
        self._packettab_params  = simulation_params["packettab_params"]
        if self._enable_apxft: self._apxflowtab_params = simulation_params["apxflowtab_params"]
        
        if False:
            self._custom_print("{} Round {}/{}: RECHECK:: Flowtab params: {}".format(self._time_elapsed(), self._round_number, self._max_round_number, self._flowtab_params))
            self._custom_print("{} Round {}/{}: RECHECK:: Packettab params: {}".format(self._time_elapsed(), self._round_number, self._max_round_number, self._packettab_params))
            if self._enable_apxft:
                self._custom_print("{} Round {}/{}: RECHECK:: Apxflowtab params: {}".format(self._time_elapsed(), self._round_number, self._max_round_number, self._apxflowtab_params))
        
        ## Initialize tables
        self._custom_print("{} Round {}/{}: Initialize the flow table".format(self._time_elapsed(), self._round_number, self._max_round_number))
        self._flow_table    = FlowTable(self._flowtab_params, self._test)
        self._custom_print("{} Round {}/{}: Initialize the packet table".format(self._time_elapsed(), self._round_number, self._max_round_number))
        self._packet_table  = PacketTable(self._packettab_params, self._test)
        if self._enable_apxft:
            self._custom_print("{} Round {}/{}: Initialize the approx. flow table".format(self._time_elapsed(), self._round_number, self._max_round_number))
            self._apxflow_table = ApproxFlowTable(self._apxflowtab_params, self._test)

        ## Record RTT samples
        self._p4rtt_sample_count = 0
        self._p4rtt_rtt_samples = {}

        ## Plotter
        self._plotter = Plotter(self._simulation_dir)

        ## Create parameters file
        params_lines = []
        params_lines.append("##################################################")
        params_lines.append("Simulation No.: {}".format(self._round_number))
        params_lines.append("")
        params_lines.append("##### Flow Table Parameters #####")
        params_lines.append("num_stages: {}".format(self._flowtab_params["num_stages"]))
        if False:
            self._custom_print("{} Round {}/{}: RECHECK:: Num stages: {}".format(self._time_elapsed(), self._round_number,
                            self._max_round_number, self._flowtab_params["num_stages"]))
        params_lines.append("max_size: {}".format(self._flowtab_params["max_size"]))
        params_lines.append("recirculations: {}".format(self._flowtab_params["recirculations"]))
        params_lines.append("prefer_new: {}".format(self._flowtab_params["prefer_new"]))
        params_lines.append("eviction_stage: {}".format(self._flowtab_params["eviction_stage"]))
        params_lines.append("entry_timeout: {}".format(self._flowtab_params["entry_timeout"]))
        params_lines.append("sampling_threshold: {}".format(self._flowtab_params["sampling_threshold"]))
        params_lines.append("sampling_rate: {}".format(self._flowtab_params["sampling_rate"]))
        params_lines.append("syn_action: {}".format(self._flowtab_params["syn_action"]))
        params_lines.append("syn_timeout_entry_timeout: {}".format(self._flowtab_params["syn_timeout_entry_timeout"]))
        params_lines.append("syn_staging_num_stages: {}".format(self._flowtab_params["syn_staging_num_stages"]))
        params_lines.append("syn_staging_max_size: {}".format(self._flowtab_params["syn_staging_max_size"]))
        params_lines.append("syn_staging_recirculations: {}".format(self._flowtab_params["syn_staging_recirculations"]))
        params_lines.append("syn_staging_prefer_new: {}".format(self._flowtab_params["syn_staging_prefer_new"]))
        params_lines.append("syn_staging_eviction_stage: {}".format(self._flowtab_params["syn_staging_eviction_stage"]))
        params_lines.append("syn_staging_entry_timeout: {}".format(self._flowtab_params["syn_staging_entry_timeout"]))
        params_lines.append("log_interval: {}".format(self._flowtab_params["log_interval"]))
        params_lines.append("")
        params_lines.append("##### Packet Table Parameters #####")
        params_lines.append("num_stages: {}".format(self._packettab_params["num_stages"]))
        if False:
            self._custom_print("{} Round {}/{}: RECHECK:: Num stages: {}".format(self._time_elapsed(), self._round_number,
                            self._max_round_number, self._packettab_params["num_stages"]))
        params_lines.append("max_size: {}".format(self._packettab_params["max_size"]))
        params_lines.append("recirculations: {}".format(self._packettab_params["recirculations"]))
        params_lines.append("prefer_new: {}".format(self._packettab_params["prefer_new"]))
        params_lines.append("eviction_stage: {}".format(self._packettab_params["eviction_stage"]))
        params_lines.append("entry_timeout: {}".format(self._packettab_params["entry_timeout"]))
        params_lines.append("sampling_threshold: {}".format(self._packettab_params["sampling_threshold"]))
        params_lines.append("sampling_rate: {}".format(self._packettab_params["sampling_rate"]))
        params_lines.append("log_interval: {}".format(self._packettab_params["log_interval"]))
        params_lines.append("")
        if self._enable_apxft:
            params_lines.append("##### Approx. Flow Table Parameters #####")
            params_lines.append("num_stages: {}".format(self._apxflowtab_params["num_stages"]))
            if False:
                self._custom_print("{} Round {}/{}: RECHECK:: Num stages: {}".format(self._time_elapsed(), self._round_number,
                                self._max_round_number, self._apxflowtab_params["num_stages"]))
            params_lines.append("max_size: {}".format(self._apxflowtab_params["max_size"]))
            params_lines.append("recirculations: {}".format(self._apxflowtab_params["recirculations"]))
            params_lines.append("prefer_new: {}".format(self._apxflowtab_params["prefer_new"]))
            params_lines.append("eviction_stage: {}".format(self._apxflowtab_params["eviction_stage"]))
            params_lines.append("entry_timeout: {}".format(self._apxflowtab_params["entry_timeout"]))
            params_lines.append("sampling_threshold: {}".format(self._apxflowtab_params["sampling_threshold"]))
            params_lines.append("sampling_rate: {}".format(self._apxflowtab_params["sampling_rate"]))
            params_lines.append("log_interval: {}".format(self._apxflowtab_params["log_interval"]))
            params_lines.append("")
        params_lines.append("##################################################")

        params_text = "\n".join(params_lines)
        params_path = os.path.join(self._simulation_dir, "simulation_parameters.txt")
        self._custom_print("{} Round {}/{}: Write parameters to {}".format(self._time_elapsed(), self._round_number, self._max_round_number, params_path))
        with open(params_path, "w") as fp:
            fp.write(params_text)
        
        ## Initialize tcptrace_const
        self._tcptrace_const = TCPTraceConst(self._simulation_dir, self._flowtab_params["log_interval"])

    ##################################################

    def _time_elapsed(self):
        time_now     = int((datetime.now() - datetime.utcfromtimestamp(0)).total_seconds())
        elapsed_secs = time_now - int(self._sim_start_time)
        hours        = elapsed_secs//3600
        mins         = (elapsed_secs - (hours*3600))//60
        secs         = elapsed_secs - (hours*3600) - (mins*60)
        return "Elapsed {}h:{}m:{}s ::".format(str(hours).zfill(2), str(mins).zfill(2), str(secs).zfill(2))

    ##################################################

    def _custom_print(self, text="", flush=True):
        print(text, flush=flush)

    ##################################################

    def _retrieve_packets_data(self, count_data):

        t_format = "%Y-%m-%d %H:%M:%S"
        t_start  = datetime.now()
        self._custom_print("{} Round {}/{}: Build packets data part {}/{} starts at time: {}".format(
                            self._time_elapsed(), self._round_number, self._max_round_number, count_data,
                            self._tcptrace_data_paths["part_pkts_count"]-1, t_start.strftime(t_format)))
        
        ## Load packets
        # process_packets_path = os.path.join(self._tcptrace_data_paths["local_directory"], "local_packets_round_{}.pickle".format(
        #                             str(count_data).zfill(2)))
        process_packets_path = self._tcptrace_data_paths["part_pkts_pickle"]
        with open(process_packets_path, "rb") as packets_fp:
            self._packets = pickle.load(packets_fp)

        ## Populate counts
        self._curr_packets_count = len(self._packets)

        t_end     = datetime.now()
        t_elapsed = round((t_end - t_start)/timedelta(minutes=1), 2)
        self._custom_print("{} Round {}/{}: Build packets data part {}/{} complete at time: {}; time elapsed: {} mins.".format(
                            self._time_elapsed(), self._round_number, self._max_round_number, count_data,
                            self._tcptrace_data_paths["part_pkts_count"]-1, t_end.strftime(t_format), t_elapsed))

    ##################################################

    def _is_home(self, ipv4):

        is_home = False
        ipv4 = IPv4Address(ipv4)
        for snet in PU_SNETS[:17]:
            if ipv4 in snet:
                is_home = True
                break
        if is_home:
            for snet in PU_SNETS[17:]:
                if ipv4 in snet:
                    is_home = False
                    break
    
        return is_home
    
    ##################################################

    def _handle_SEQ_direction(self, packet):
        '''Handle SEQ direction'''
        ## This proceeds in 4 steps: (1) FT processing, (2) AFT processing, (3) PT processing, (4) AFT processing
        ## In the actual data plane (DP) implementation, these steps are intertwined. To help simulate that, in each step, we accumulate actionables for subsequent steps.
        ## So while we execute actions in a convenient order in simulation (to the extent possible), the final state in each of the 3 data structures is the same as when done in the DP impl.
        ## The accounting/logging is done in a way such that it reflects how things would have happened in the DP impl. The plots are therefore faithful to the actual DP impl.

        # Prep flow key
        flow_key = (packet["ipsrc"], packet["ipdst"], packet["tcpsrc"], packet["tcpdst"])
        
        # Step 1: Peform flow table (FT) processing

        ## Initialize actionables for next steps
        actionables_ft2pt = ("drop", None)
        actionables_ft2aft = ("drop", None)

        ## Account for packet processing
        self._flow_table.accountant.accountForProcessing()
        
        ## Case 0: Drop if SYN packet with IGNORE option or a pure ACK
        is_syn = "S" in packet["tcpflags"] and self._flowtab_params["syn_action"] == "ignore"
        is_fin = "F" in packet["tcpflags"] and self._flowtab_params["syn_action"] == "ignore"
        is_rst = "R" in packet["tcpflags"] and self._flowtab_params["syn_action"] == "ignore"
        is_pure_ack = packet["tcpflags"] == "-A----" and packet["pktsize"] == 0
        # if is_syn or is_fin or is_rst or is_pure_ack:
        if is_syn or is_rst or is_pure_ack:
            ## Account for packet drop
            self._flow_table.accountant.accountForDrop()
            if self._test: self._custom_print("SEQ FT:: Packet is either a SYN, FIN, or RST packet with SYN IGNORE on, or a pure ACK; DROP: {}".format(flow_key))
            ## Set actionables for next steps
            actionables_ft2pt  = ("drop", None)
            actionables_ft2aft = ("drop", None)
        
        ## Cases: 1. Flow record for this flow exists, 2. Flow record for this flow doesn't exist
        else:
            ## Compute expected ACK
            exp_ack = packet["seqno"] + packet["pktsize"]
            if "S" in packet["tcpflags"] or "F" in packet["tcpflags"]: exp_ack += 1

            ## Lookup the flow record
            flow_record = self._flow_table.lookup(flow_key)
            if self._test: self._custom_print("SEQ FT:: Lookup: Retrieved record for key {} is {}".format(flow_key, flow_record))

            ## Case 1: The flow record was found; need to check for validity and either update or delete the record
            if flow_record is not None:
                _, (highest_byte_acked_or_rexmited, highest_expected_ack), _, _, _, _ = flow_record
                if self._test: self._custom_print("SEQ FT:: Flow record for key {} is found, retrieved record is: {}".format(flow_key, flow_record))

                ## Case 1.1: The flow record is valid; the new packet is either an extension to the measurement range, or ahead of the measurement range
                if packet["seqno"] >= highest_expected_ack:
            
                    ## Case 1.1.1: The new packet is an extension to the measurement range
                    if packet["seqno"] == highest_expected_ack:
                        updated_record = (flow_key, (highest_byte_acked_or_rexmited, exp_ack), None, packet["timestamp"], None, packet["tcpflags"])
                    
                    ## Case 1.1.2: Restart the measurement range with latest packet since there's a gap in the sequence no. space
                    else:
                        updated_record = (flow_key, (packet["seqno"], exp_ack), None, packet["timestamp"], None, packet["tcpflags"])

                    ## Delete if collapsed interval, or update if interval is still open
                    if updated_record[1][0] == updated_record[1][1]:
                        update_success = self._flow_table.delete(flow_key, packet["timestamp"])
                        if self._test: self._custom_print("SEQ FT:: Delete record since closed interval: {} || Flow key: {}".format(
                                                            (updated_record[1][0], updated_record[1][1]), flow_key))
                    else:
                        update_success = self._flow_table.update(flow_key, updated_record, packet["timestamp"])
                        if self._test: self._custom_print("SEQ FT:: Updated record with: {} || Flow key: {}".format(
                                                            (updated_record[1][0], updated_record[1][1]), flow_key))
                    
                    self._flow_table.accountant.accountForUpdateAttempt()
                    if update_success: self._flow_table.accountant.accountForUpdateSuccess()
                    else: self._flow_table.accountant.accountForUpdateFailure()

                    actionables_ft2pt  = ("insert", "packet_record")
                    actionables_ft2aft = ("update_or_insert", [updated_record, ])
                
                ## Case 1.2: Delete since violation to measurement range
                else:
                    
                    update_success = self._flow_table.delete(flow_key, packet["timestamp"])
                    self._flow_table.accountant.accountForUpdateAttempt()
                    if update_success: self._flow_table.accountant.accountForUpdateSuccess()
                    else: self._flow_table.accountant.accountForUpdateFailure()

                    ### Create record with a collapsed measurement range to insert into/update AFT
                    aft_record = (flow_key, (exp_ack, exp_ack), packet["timestamp"], packet["timestamp"], packet["tcpflags"], packet["tcpflags"])

                    actionables_ft2pt  = ("drop", None)
                    actionables_ft2aft = ("update_or_insert", [aft_record, ])

                    if self._test: self._custom_print("SEQ FT: Deleted record since packet seq. no. {} < {} highest expected ACK || Flow key: {}".format(
                                                        packet["seqno"], highest_expected_ack, flow_key))

            ## Case 2: Flow record does not exist in FT; need to insert it
            else:
                ## Case 2.1: Flow record got forcefully evicted but current packet is a retransmission
                ## Actions: Lookup PT; if record with same eACK exists then don't insert into FT and drop PT record
                packet_key = flow_key + (exp_ack, )
                packet_record = self._flow_table.lookup(packet_key)
                if self._test: self._custom_print("SEQ PT (FT):: Flow record not found; packet record looked up: {}".format(packet_record))

                if packet_record is not None:
                    aft_record = (flow_key, (exp_ack, exp_ack), packet["timestamp"], packet["timestamp"], packet["tcpflags"], packet["tcpflags"])
                    actionables_ft2pt  = ("delete", packet_key)
                    actionables_ft2aft = ("update_or_insert", [aft_record, ])

                    if self._test: self._custom_print("SEQ FT:: Flow record not found but packet record found; retransmission: {}".format(packet_key))
                
                ## Case 2.2: The PT record doesn't exist, so normal insertion can proceed
                else:
                    # ## Check exhaustively to see if the PT record actually exists but didn't get found because of the reinsertion anomaly
                    # exhaustive_rec = self._packet_table.exhaustive_lookup(packet_key)
                    # if self._test: self._custom_print("SEQ PT (FT):: Exhaustive record is: {}".format(exhaustive_rec))

                    ## Create new flow record
                    new_flow_record = (flow_key, (packet["seqno"], exp_ack), packet["timestamp"], packet["timestamp"], packet["tcpflags"], packet["tcpflags"])
                    _, touched_records = self._flow_table.insert(record=new_flow_record, timestamp=packet["timestamp"])
                    
                    actionables_ft2pt  = ("insert", "packet_record")
                    ## touched_records is a list of flow records that could be inserted into the AFT
                    ## The rationale is that in each pass/(re)circulation, there is one opportunity to write to the AFT
                    actionables_ft2aft = ("update_or_insert", touched_records)

                    if self._test: self._custom_print("SEQ FT:: New flow record inserted: {}".format(new_flow_record))
        
        if self._test:
            self._custom_print("SEQ FT:: Actionables for PT: {}".format(actionables_ft2pt))
            self._custom_print("SEQ FT:: Actionables for AFT: {}".format(actionables_ft2aft))

        
        # Step 2: Peform FT2AFT actions to sync chances since these will affect PT evictions
        if self._enable_apxft:
            self._apxflow_table.accountant.accountForProcessing()

            if actionables_ft2aft[0] == "drop":
                self._apxflow_table.accountant.accountForDrop()
                if self._test: self._custom_print("SEQ AFT:: Packet is either a SYN packet with IGNORE on, or a pure ACK; DROP || Flow key: {}".format(flow_key))
            
            elif actionables_ft2aft[0] == "update_or_insert":
                if len(actionables_ft2aft[1]) > 1:
                    for record in actionables_ft2aft[1][:-1]:
                        ## Update AFT record if exists or insert
                        if self._apxflow_table.insert_or_update(record, timestamp=record[3]):
                            if self._test: self._custom_print("SEQ AFT:: Flow record successfully inserted/updated: {}".format(record))
                        else:
                            if self._test: self._custom_print("SEQ AFT:: Flow record insertion/update failed: {}".format(record))        
        
        
        # Step 3: Peform packet table (PT) processing
        ## Account for packet processing
        actionables_pt2aft = ("drop", None)
        self._packet_table.accountant.accountForProcessing()

        if actionables_ft2pt[0] == "drop":
            self._packet_table.accountant.accountForDrop()
            actionables_pt2aft = ("drop", None)
            if self._test: self._custom_print("SEQ PT:: Packet is either a SYN packet with IGNORE on, or a pure ACK; DROP || Flow key: {}".format(flow_key))
        
        elif actionables_ft2pt[0] == "delete":
            self._packet_table.accountant.accountForUpdateAttempt()
            if self._packet_table.delete(actionables_ft2pt[1], packet["timestamp"]):
                self._packet_table.accountant.accountForUpdateSuccess()
            else:
                self._packet_table.accountant.accountForUpdateFailure()
            if self._test: self._custom_print("SEQ PT:: Flow key: {} || FT2PT action is delete; deleted packet record: {}".format(flow_key, actionables_ft2pt[1]))

        elif actionables_ft2pt[0] == "insert":
            ## Insert into packet table
            packet_key = (packet["ipsrc"], packet["ipdst"], packet["tcpsrc"], packet["tcpdst"], exp_ack)
            new_packet_record = (packet_key, packet["timestamp"], packet["seqno"])
            if not self._enable_apxft: self._apxflow_table = None
            eviction_code = self._packet_table.insert(record=new_packet_record, timestamp=packet["timestamp"], flow_table=self._flow_table, apxflow_table=self._apxflow_table)
            if self._test:
                if eviction_code: self._custom_print("SEQ PT:: Flow key: {} || Packet record {} inserted, eviction code is {}".format(flow_key, packet_key, eviction_code))
                else: self._custom_print("SEQ PT:: Flow key: {} || Packet record {} insertion FAILED, eviction code is {}".format(flow_key, packet_key, eviction_code))
            if len(actionables_ft2aft[1]) >= 1:
                actionables_pt2aft = ("update_or_insert", actionables_ft2aft[1][-1])
        
        if self._enable_apxft and self._test: self._custom_print("SEQ PT:: Flow key: {} || Actionables for AFT: {}".format(flow_key, actionables_pt2aft))
        
        # Step 4: Peform PT2AFT action
        if self._enable_apxft:
            ## Account for packet processing
            self._apxflow_table.accountant.accountForProcessing()

            if actionables_pt2aft[0] == "drop":
                self._apxflow_table.accountant.accountForDrop()
                if self._test: self._custom_print("SEQ AFT:: Instruction from FT is to drop, so drop")
            
            elif actionables_pt2aft[0] == "update_or_insert":
                ## Update AFT record if exists or insert
                record = actionables_pt2aft[1]
                self._apxflow_table.accountant.accountForUpdateAttempt()
                if self._apxflow_table.insert_or_update(record, timestamp=record[3]):
                    self._apxflow_table.accountant.accountForUpdateSuccess()
                    if self._test: self._custom_print("SEQ AFT:: Flow record successfully inserted/updated: {}".format(record))
                else:
                    self._apxflow_table.accountant.accountForUpdateFailure()
                    if self._test: self._custom_print("SEQ AFT:: Flow record insertion/update failed: {}".format(record))

        return

    ##################################################

    def _handle_ACK_direction(self, packet):

        # Handle ACK direction

        ## Identify 3 conditions:
        ## (1) Packets that slide without effect (Packets with neither ACK nor RST flags set)
        ## (2) Packets that result in removing flow entry (RST packets; when conf. interval collapses due to ACKs, entries are removed during contention)
        ## (3) Packets that result in RTT samples (The following isn't true anymore: RST packets with ACK set also count)

        ## Prep. flow key
        flow_key = (packet["ipdst"], packet["ipsrc"], packet["tcpdst"], packet["tcpsrc"])

        # Step 1: Peform flow table (FT) processing

        ## Account for packet processing
        self._flow_table.accountant.accountForProcessing("ACK")

        ## Case 0: Drop packet if SYN, FIN, or RST packet and SYN IGNORE is on; or not an ACK
        is_syn = "S" in packet["tcpflags"] and self._flowtab_params["syn_action"] == "ignore"
        is_fin = "F" in packet["tcpflags"] and self._flowtab_params["syn_action"] == "ignore"
        is_rst = "R" in packet["tcpflags"] and self._flowtab_params["syn_action"] == "ignore"
        is_not_ack = "A" not in packet["tcpflags"]
        # if is_syn or is_fin or is_rst or is_not_ack:
        if is_syn or is_rst or is_not_ack:
            ## Account for packet drop
            self._flow_table.accountant.accountForDrop("ACK")
            if self._test: self._custom_print(
                "ACK FT:: Flow key: {} || Either SYN, FIN, or RST set and SYN IGNORE on, or not an ACK; DROP".format(flow_key))
            ## Set actionables for next steps
            actionables_ft2pt  = ("drop", None)
            actionables_ft2aft = ("drop", None)
            
        # ## Case 1: RST is set but ACK is not: Delete flow table record
        # elif "A" not in packet["tcpflags"] and "R" in packet["tcpflags"]:
        #     ft_record_to_delete = self._flow_table.lookup(flow_key)
        #     ## Account for flow table record deletion
        #     self._flow_table.accountant.accountForUpdateAttempt("ACK")
        #     if self._flow_table.delete(flow_key, packet["timestamp"]):
        #         self._flow_table.accountant.accountForUpdateSuccess("ACK")
        #     else:
        #         self._flow_table.accountant.accountForUpdateFailure("ACK")
        #     if self._test: self._custom_print("ACK FT:: Flow key: {} || RST set but not ACK, delete flow record".format(flow_key))
        #     ## Set actionables for next steps
        #     if ft_record_to_delete is not None:
        #         eACK_to_delete     = ft_record_to_delete[1][1]
        #         pt_key_to_delete   = flow_key + (eACK_to_delete, )
        #         updated_ft_record  = (flow_key, (eACK_to_delete, eACK_to_delete), None, packet["timestamp"], None, packet["tcpflags"])
        #         actionables_ft2pt  = ("delete", pt_key_to_delete)
        #         actionables_ft2aft = ("update_or_insert", updated_ft_record)
        #     else:
        #         actionables_ft2pt  = ("drop", None)
        #         actionables_ft2aft = ("drop", None)
        
        ## Case 2: ACK is set
        elif "A" in packet["tcpflags"]:
            flow_record = self._flow_table.lookup(flow_key)
            
            ## Case 2.1: Flow record does not exist, drop packet
            if flow_record is None:
                self._flow_table.accountant.accountForDrop("ACK")
                if self._test: self._custom_print("ACK FT:: Flow record for key {} is NONE, DROP".format(flow_key))
                actionables_ft2pt  = ("drop", None)
                actionables_ft2aft = ("drop", None)
            
            ## Case 2.2: Flow record exists
            else:
                _, (highest_byte_acked_or_rexmited, highest_expected_ack), _, _, _, _ = flow_record
                if self._test: self._custom_print("ACK FT:: Flow record for key {}: {}".format(flow_key, flow_record))

                ## Case 2.2.1: Delete flow table record if (RST is set or) ACK beyond measurement range
                # if "R" in packet["tcpflags"] or packet["ackno"] > highest_expected_ack or packet["ackno"] <= highest_byte_acked_or_rexmited:
                # if packet["ackno"] > highest_expected_ack or packet["ackno"] <= highest_byte_acked_or_rexmited:

                if packet["ackno"] < highest_byte_acked_or_rexmited or packet["ackno"] > highest_expected_ack:
                    ## ACK in future = optimistic ACK; ACK in past = ACK for past SEQ packet not tracked due to MR collapse OR ACK reordered
                    self._flow_table.accountant.accountForDrop("ACK")
                    actionables_ft2pt  = ("drop", None)
                    actionables_ft2aft = ("drop", None)
                
                elif packet["ackno"] == highest_byte_acked_or_rexmited:
                    ## Duplicate ACK: delete flow table record
                    self._flow_table.accountant.accountForUpdateAttempt("ACK")
                    if self._flow_table.delete(flow_key, packet["timestamp"]):
                        self._flow_table.accountant.accountForUpdateSuccess("ACK")
                    else:
                        self._flow_table.accountant.accountForUpdateFailure("ACK")
                    actionables_ft2pt  = ("drop", None)
                    actionables_ft2aft = ("drop", None)
                    
                    # ## Set actionables for next steps
                    # new_highest_expected_ack = max(highest_expected_ack, packet["ackno"])
                    # pt_key_to_delete   = flow_key + (highest_expected_ack, )
                    # updated_ft_record  = (flow_key, (new_highest_expected_ack, new_highest_expected_ack),
                    #   None, packet["timestamp"], None, packet["tcpflags"])
                    # # if "R" not in packet["tcpflags"]:
                    # #     actionables_ft2pt  = ("delete", pt_key_to_delete)
                    # # else:
                    # #     actionables_ft2pt  = ("match", "packet_record")
                    # actionables_ft2pt  = ("delete", pt_key_to_delete)
                    # actionables_ft2aft = ("update_or_insert", updated_ft_record)

                ## Case 2.2.2: Update flow table with ACK no. since ACK within measurement range            
                elif highest_byte_acked_or_rexmited < packet["ackno"] and packet["ackno"] <= highest_expected_ack:

                    updated_record = (flow_key, (packet["ackno"], highest_expected_ack), None, packet["timestamp"], None, packet["tcpflags"])
                    self._flow_table.accountant.accountForUpdateAttempt("ACK")
                    if packet["ackno"] == highest_expected_ack:
                        update_success = self._flow_table.delete(flow_key, packet["timestamp"])
                        if self._test: self._custom_print("ACK FT:: Flow key: {} || ACK# within measurement range; updated measurement range closed now ({} == {}), deleted".format(
                                                            flow_key, packet["ackno"], highest_expected_ack))
                    else:
                        update_success = self._flow_table.update(flow_key, updated_record, packet["timestamp"])
                        if self._test: self._custom_print("ACK FT:: Flow key: {} || ACK# within measurement range; updated measurement range is: {}".format(
                                                            flow_key, updated_record[1]))
                    
                    if update_success: self._flow_table.accountant.accountForUpdateSuccess("ACK")
                    else: self._flow_table.accountant.accountForUpdateFailure("ACK")
                    actionables_ft2pt  = ("match", "packet_record")
                    actionables_ft2aft = ("update_or_insert", updated_record)
                
                if self._test:
                    # if "R" in packet["tcpflags"]:
                    #     self._custom_print("ACK FT:: Flow key: {} || Deleted FT record since RST is set".format(flow_key))
                    if packet["ackno"] > highest_expected_ack:
                        self._custom_print("ACK FT:: Flow key: {} || Ignored since optimistic ACK: ACK# > highest eACK: {} > {}".format(
                                            flow_key, packet["ackno"], highest_expected_ack))
                    elif packet["ackno"] == highest_byte_acked_or_rexmited:
                        self._custom_print("ACK FT:: Flow key: {} || Deleted FT record since ACK# == highest byte affected (dupACK): {} <= {}".format(
                                            flow_key, packet["ackno"], highest_byte_acked_or_rexmited))
                    elif packet["ackno"] < highest_byte_acked_or_rexmited:
                        self._custom_print("ACK FT:: Flow key: {} || Ignored since ACK to untracked SEQ packet: ACK# < highest eACK: {} > {}".format(
                                            flow_key, packet["ackno"], highest_expected_ack))
        
        else:
            self._flow_table.accountant.accountForDrop("ACK")
            actionables_ft2pt  = ("drop", None)
            actionables_ft2aft = ("drop", None)
            
        if self._test: self._custom_print("ACK FT:: Actionables: FT2PT: {}, FT2AFT: {}".format(actionables_ft2pt, actionables_ft2aft))


        # Step 2: Handle packet table action
        self._packet_table.accountant.accountForProcessing("ACK")

        ## Case 0: Action is drop
        if actionables_ft2pt[0] == "drop":
            self._packet_table.accountant.accountForDrop("ACK")
            if self._test: self._custom_print("ACK PT:: Flow key: {} || FT2PT action is drop; DROPPED".format(flow_key))
        
        ## Case 1: Action is delete
        elif actionables_ft2pt[0] == "delete":
            self._packet_table.accountant.accountForUpdateAttempt("ACK")
            if self._packet_table.delete(actionables_ft2pt[1], packet["timestamp"]):
                self._packet_table.accountant.accountForUpdateSuccess("ACK")
            else:
                self._packet_table.accountant.accountForUpdateFailure("ACK")
            if self._test: self._custom_print("ACK PT:: Flow key: {} || FT2PT action is delete; deleted packet record".format(flow_key))
        
        ## Case 2: Action is match
        elif actionables_ft2pt[0] == "match":
            match_key     = (packet["ipdst"], packet["ipsrc"], packet["tcpdst"], packet["tcpsrc"], packet["ackno"])
            packet_record = self._packet_table.lookup(match_key)

            ## Case 2.1: If packet record doesn't exist, drop packet
            if packet_record is None:
                self._packet_table.accountant.accountForDrop("ACK")
                if self._test: self._custom_print("ACK PT:: Packet record for key {} is NONE, drop".format(flow_key))
            
            ## Case 2.2: Packet record exists: Delete packet record, compute RTT sample, and report
            else:
                self._packet_table.accountant.accountForUpdateAttempt("ACK")
                if self._packet_table.delete(match_key, packet["timestamp"]):
                    self._packet_table.accountant.accountForUpdateSuccess("ACK")
                else:
                    self._packet_table.accountant.accountForUpdateFailure("ACK")
                
                if self._test: self._custom_print("ACK PT:: Flow key: {} || Deleted PT record since match is found for ACK#: {}".format(flow_key, packet["ackno"]))
                
                _, packet_tstamp, packet_seqno = packet_record
                rtt = (packet["timestamp"] - packet_tstamp)/timedelta(milliseconds=1)
                if flow_key not in self._p4rtt_rtt_samples:
                    self._p4rtt_rtt_samples[flow_key] = []
                self._p4rtt_rtt_samples[flow_key].append((packet_seqno, rtt))
                self._p4rtt_sample_count += 1
                
                if self._test: self._custom_print("ACK FT:: Flow key: {} || RTT sample collected is {}".format(flow_key, rtt))


        # Step 3: Handle approx. flow table action

        if self._enable_apxft:
            ## Account for packet processing
            self._apxflow_table.accountant.accountForProcessing("ACK")

            ## Case 0: Action is drop
            if actionables_ft2aft[0] == "drop":
                self._apxflow_table.accountant.accountForDrop("ACK")
                if self._test: self._custom_print("ACK AFT:: Flow key: {} || FT2AFT action is drop; DROPPED".format(flow_key))
            
            ## Case 1: Action is update or insert
            elif actionables_ft2aft[0] == "update_or_insert":
                ## Update AFT record if exists or insert
                record = actionables_ft2aft[1]
                self._apxflow_table.accountant.accountForUpdateAttempt("ACK")
                if self._apxflow_table.insert_or_update(record, timestamp=record[3]):
                    self._apxflow_table.accountant.accountForUpdateSuccess("ACK")
                    if self._test: self._custom_print("SEQ AFT:: Flow record successfully inserted/updated: {}".format(record))
                else:
                    self._apxflow_table.accountant.accountForUpdateFailure("ACK")
                    if self._test: self._custom_print("SEQ AFT:: Flow record insertion/update failed: {}".format(record))

        return

    ##################################################

    def run_p4rtt_simulation(self):

        t_format = "%Y-%m-%d %H:%M:%S"
        t_start  = datetime.now()
        self._custom_print("{} Round {}/{}: Start simulation for round {} at time {}".format(
                            self._time_elapsed(), self._round_number, self._max_round_number, self._round_number, t_start.strftime(t_format)))
        latest_tstamp = None

        # time_seq_tcptrace = []
        # time_seq_p4rtt = []
        # time_ack_tcptrace = []
        # time_ack_p4rtt = []

        for count_data in range(self._tcptrace_data_paths["part_pkts_count"]):

            ## Load packets from current part file into self._packets
            self._retrieve_packets_data(count_data)

            for count_packet, packet_data in enumerate(self._packets):

                self._packets_count += 1

                packet = {}
                packet["pktno"], packet["timestamp"], packet["ipsrc"], packet["ipdst"], packet["tcpsrc"], \
                    packet["tcpdst"], packet["tcpflags"], packet["seqno"], packet["ackno"], packet["pktsize"] = packet_data
                packet["tcpflags"] = packet["tcpflags"][2:]

                if self._test:
                    self._custom_print("##################################################\n")
                    self._custom_print("Packet {}: {}".format(self._packets_count, packet))

                if count_data == 0 and count_packet == 0:
                    self._firstEntryTime                 = packet["timestamp"]
                    self._tcptrace_const._firstEntryTime = packet["timestamp"]

                latest_tstamp = packet["timestamp"]

                if (self._packets_count+1)%1000000 == 0:
                    self._custom_print("{} Round {}/{}: Processed {}M/{}M packets in this simulation".format(
                                            self._time_elapsed(), self._round_number, self._max_round_number,
                                            round((self._packets_count+1)/1000000, 2), round(self._total_packets_count/1000000, 2)))
                
                ## Handle SEQ direction if source IP is within campus and destination IP is NOT within campus
                if self._is_home(packet["ipsrc"]) and not self._is_home(packet["ipdst"]):
                    if self._test:
                        self._custom_print("\nHandle SEQ direction")
                    
                    # dbg_time_start = datetime.now()
                    self._tcptrace_const.process_tcptrace_SEQ(packet)
                    # dbg_time_end = datetime.now()
                    # time_seq_tcptrace.append((dbg_time_end-dbg_time_start)/timedelta(microseconds=1))
                    
                    # dbg_time_start = datetime.now()
                    self._handle_SEQ_direction(packet)
                    # dbg_time_end = datetime.now()
                    # time_seq_p4rtt.append((dbg_time_end-dbg_time_start)/timedelta(microseconds=1))

                ## Handle ACK direction if source IP is NOT within campus and destination IP is within campus
                if not self._is_home(packet["ipsrc"]) and self._is_home(packet["ipdst"]):
                    if self._test:
                        self._custom_print("\nHandle ACK direction")

                    # dbg_time_start = datetime.now()
                    self._tcptrace_const.process_tcptrace_ACK(packet)
                    # dbg_time_end = datetime.now()
                    # time_ack_tcptrace.append((dbg_time_end-dbg_time_start)/timedelta(microseconds=1))

                    # dbg_time_start = datetime.now()
                    self._handle_ACK_direction(packet)
                    # dbg_time_end = datetime.now()
                    # time_ack_p4rtt.append((dbg_time_end-dbg_time_start)/timedelta(microseconds=1))
                
                ## Log state of data structures
                if self._test:
                    self._custom_print("\nState of tables after processing packet no. {}:\n".format(self._packets_count))
                    self._custom_print(self._flow_table)
                    self._custom_print()
                    self._custom_print(self._packet_table)
                    self._custom_print()
                    if self._enable_apxft:
                        self._custom_print(self._apxflow_table)
                        self._custom_print()
                    self._flow_table.accountant.stateMismatchInfo(self._packets_count)
                    self._packet_table.accountant.stateMismatchInfo(self._packets_count)

        self._custom_print("{} Round {}/{}: Processing complete; processed {}M/{}M packets in this simulation".format(
                                self._time_elapsed(), self._round_number, self._max_round_number, round((self._packets_count+1)/1000000, 2),
                                round(self._total_packets_count/1000000, 2)))
        
        # print("Total time taken per SEQ packet (tcptrace): {}".format(round(np.sum(time_seq_tcptrace))))
        # print("Total time taken per SEQ packet (p4rtt): {}".format(round(np.sum(time_seq_p4rtt))))
        # print("Total time taken per ACK packet (tcptrace): {}".format(round(np.sum(time_ack_tcptrace))))
        # print("Total time taken per ACK packet (p4rtt): {}".format(round(np.sum(time_ack_p4rtt))))
        
        
        ## Logging

        ## Last snapshot is explicit
        self._custom_print("{} Round {}/{}: Trigger last snapshot explicitly".format(self._time_elapsed(), self._round_number, self._max_round_number))
        self._flow_table.accountant.explicitSnapshot(latest_tstamp)
        if self._flow_table._synAction == "staging":
            self._flow_table._syn_table.accountant.explicitSnapshot(latest_tstamp)
        self._packet_table.accountant.explicitSnapshot(latest_tstamp)

        ## Save snapshots
        self._custom_print("{} Round {}/{}: Save all snapshots".format(self._time_elapsed(), self._round_number, self._max_round_number))
        self._flow_table.accountant.saveSnapshots()
        if self._flow_table._synAction == "staging":
            self._flow_table.accountant._syn_table.saveSnapshots()
        self._packet_table.accountant.saveSnapshots()

        ## Plot snapshots
        self._custom_print("{} Round {}/{}: Plot all snapshots".format(self._time_elapsed(), self._round_number, self._max_round_number))
        self._flow_table.accountant.plotSnapshots()
        if self._flow_table._synAction == "staging":
            self._flow_table._syn_table.accountant.plotSnapshots()
        self._packet_table.accountant.plotSnapshots()
        
        ## Plot RTT distribution
        self._custom_print("{} Round {}/{}: Plot RTT distribution".format(self._time_elapsed(), self._round_number, self._max_round_number))
        ### P4RTT
        p4rtt_rtt_all = []
        for flow_key in self._p4rtt_rtt_samples:
            p4rtt_rtt_all.extend([t[1] for t in self._p4rtt_rtt_samples[flow_key]])
        ## tcptrace
        tcptrace_rtt_all = []
        for flow_key in self._tcptrace_const._tcptrace_rtt_samples:
            tcptrace_rtt_all.extend([t[1] for t in self._tcptrace_const._tcptrace_rtt_samples[flow_key]])
        
        self._flow_table.accountant._plotMetricCDF(p4rtt_rtt_all, "rtt_samples_cdf", "red", "-", "RTT (ms) CDF ({} Samples)".format(
                                                    self._p4rtt_sample_count))
    
        ## Validation
        # self._flow_table.accountant.stateValidationInfo(self._time_elapsed())
        # self._packet_table.accountant.stateValidationInfo(self._time_elapsed())

        ## Plot RTT comparison
        self._tcptrace_const.concludeRTTDict()
        # self._plotter.plotPerformanceComparison(self._tcptrace_const._tcptrace_rtt_samples, self._p4rtt_rtt_samples,
        #                                         self._tcptrace_const._tcptrace_sample_count, self._p4rtt_sample_count)
        
        ## Save RTT Samples
        ### P4RTT
        with open(os.path.join(self._simulation_dir, "rtt_samples_p4rtt.txt"), "w") as fp:
            lines = ["{}".format(point) for point in p4rtt_rtt_all]
            fp.write("\n".join(lines))
        ## tcptrace
        with open(os.path.join(self._simulation_dir, "rtt_samples_tcptrace_const.txt"), "w") as fp:
            lines = ["{}".format(point) for point in tcptrace_rtt_all]
            fp.write("\n".join(lines))
        
        # num_seq_pkts = 0
        # num_ack_pkts = 0
        # for k in self._all_flows_seq_pkts:
        #     num_seq_pkts += self._all_flows_seq_pkts[k]
        # for k in self._all_flows_ack_pkts:
        #     num_ack_pkts += self._all_flows_ack_pkts[k]

        # print("{0} Round {1}/{2}: No. of unique SEQ flows: {3}".format(self._time_elapsed(), self._round_number, self._max_round_number, len(self._all_flows_seq_pkts)))
        # print("{0} Round {1}/{2}: No. of unique ACK flows: {3}".format(self._time_elapsed(), self._round_number, self._max_round_number, len(self._all_flows_ack_pkts)))
        # print("{0} Round {1}/{2}: No. of SEQ packets: {3}".format(self._time_elapsed(), self._round_number, self._max_round_number, num_seq_pkts))
        # print("{0} Round {1}/{2}: No. of ACK packets: {3}".format(self._time_elapsed(), self._round_number, self._max_round_number, num_ack_pkts))
        # print("{0} Round {1}/{2}: Flow records: Mean: {3}, Stdv.: {4}".format(self._time_elapsed(), self._round_number, self._max_round_number,
        #         np.mean(self._tcptrace_const._intervalActiveFlows), np.std(self._tcptrace_const._intervalActiveFlows) ))
        # print("{0} Round {1}/{2}: Packet records: Mean: {3}, Stdv.: {4}".format(self._time_elapsed(), self._round_number, self._max_round_number,
        #         np.mean(self._tcptrace_const._intervalActivePackets), np.std(self._tcptrace_const._intervalActivePackets) ))

        self._tcptrace_const.plot_tcptrace_stats(latest_tstamp)

        # self._tcptrace_const.investigate_bias(self._flow_table)
        
        
        t_end = datetime.now()
        t_elapsed = round((t_end - t_start)/timedelta(minutes=1), 2)
        self._custom_print("{0} Round {1}/{2}: Finished simulation for round {1} at time {3}. Time elapsed: {4} mins.".format(
                                self._time_elapsed(), self._round_number, self._max_round_number, t_end.strftime(t_format), t_elapsed))

        return
    
    ##################################################

##################################################

def main():

    simulation_params = json.loads(sys.argv[1])
    is_test          = simulation_params["sim_params"]["is_test"]
    round_num        = simulation_params["sim_params"]["round_number"]
    num_combinations = simulation_params["sim_params"]["combinations_count"]
    print("Round {}/{}: Create simulation object with current set of params".format(round_num, num_combinations-1))
    simulation = Simulation(simulation_params, is_test)
    print("Round {}/{}: Start P4RTT simulations with created packets list".format(round_num, num_combinations-1))
    simulation.run_p4rtt_simulation()

##################################################

if __name__ == "__main__":
    main()

##################################################
