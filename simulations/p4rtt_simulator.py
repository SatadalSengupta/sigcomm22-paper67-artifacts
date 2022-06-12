import tcptrace_analysis.CuckooHashTable as CHT
from ipaddress import IPv4Address, ip_network
from datetime import datetime, timedelta
import importlib
import pickle
import os
importlib.reload(CHT)

MAX_SEQNUM = 2**32

##################################################

TIMESTAMP_START = datetime(2020, 4, 7, 19, 0, 0, 0)

def time_abs2rel(ts_abs):
    return int((ts_abs - TIMESTAMP_START)/timedelta(microseconds=1))

def time_rel2abs(ts_rel):
    return TIMESTAMP_START + timedelta(microseconds=ts_rel)

##################################################

def logging(text, flag):
    if flag: print(text)

##################################################

def print_dict(sdict, flag):
    if flag:
        for key in sdict: print(key, ": ", sdict[key])

##################################################

def get_pkt_info_dict():
    pkt_info_dict = {
        "pktno"     : None,
        "savedlen"  : None,
        "timestamp" : None,
        "ipvers"    : None,
        "ipsrc"     : None,
        "ipdst"     : None,
        "transtype" : None,
        "iphdrlen"  : None,
        "ttl"       : None,
        "iplen"     : None,
        "ipid"      : None,
        "ipchksum"  : None,
        "offset"    : None,
        "tcpsrc"    : None,
        "tcpdst"    : None,
        "tcpflags"  : None,
        "seqno"     : None,
        "ackno"     : None,
        "tcpwindow" : None,
        "tcphdrlen" : None,
        "tcpchksum" : None,
        "pktsize"   : None,
        "optslen"   : None,
        "tcpopts"   : None,
        "datalen"   : None,
        "rtt"       : None
    }
    return pkt_info_dict

##################################################

def get_resolved_tcpflags(tcp_flags):
    ''' Return the proper tcp flags corresponding to a flags string '''
    res_flags = {}
    # Flags format = CEUAPRSF
    res_flags["??----S"]  = "CE----S-"
    res_flags["?"]        = "-E-A--S-"
    res_flags["?-AP---"]  = "C--AP---"
    res_flags["?-A----"]  = "C--A----"
    res_flags["?-AP--F"]  = "C--AP--F"
    res_flags["?-A-R--"]  = "C--A-R--"
    res_flags["??-A--S-"] = "CE--A-S-"
    if tcp_flags in res_flags:
        ret_flags = res_flags[tcp_flags]
    else:
        ret_flags = "--" + tcp_flags
    return ret_flags

##################################################

def collect_all_packets_sequentially(tcptrace_data_paths):
    ''' Collect all packet data output by tcptrace in order of arrival '''

    print("Collect all packet data output by tcptrace in order of arrival...", flush=True)

    print("\t Parsing tcptrace packet data file...", flush=True)
    tcptrace_packet_data_path = os.path.join(tcptrace_data_paths["packets_data"])
    all_packets = []
    seq_count = 0

    with open(tcptrace_packet_data_path, "r") as packet_data_fp:

        print("\t\t Starting to go through the tcptrace packet data file...", flush=True)
        pkt_count = 0
        is_tcp = False
        pkt_no = 0
        last_pkt_no = 0
        opts_len = None
        tcp_opts = None
        data_len = None

        for line in packet_data_fp:

            if "Packet " in line:
                pkt_count += 1

                # Do every 10 M packets
                if pkt_count%10000000 == 0:
                    print("\t\t Parsed {} M packets so far...".format(int(pkt_count/1000000)), flush=True)
                    with open(tcptrace_data_paths["all_pkts_pickle"].format(str(seq_count).zfill(2)), "wb") as packets_fp:
                        pickle.dump(all_packets, packets_fp)
                    seq_count += 1
                    all_packets = []

                last_pkt_no = pkt_no
                pkt_no = int(line.strip().split()[1])

            # if packet_data_flag:
            elif "Saved Length: " in line:
                saved_len = int(line.strip().split()[2])
            elif "Collected: " in line:
                tstamp_str = " ".join(line.strip().split()[1:])
                tstamp = datetime.strptime(tstamp_str, "%a %b %d %H:%M:%S.%f %Y")
                time_elapsed = int((tstamp - TIMESTAMP_START)/timedelta(microseconds=1))
            elif "IP  VERS: " in line:
                ip_vers = int(line.strip().split()[2])
            elif "IP  Srce: " in line:
                ip_src = IPv4Address(line.strip().split()[2])
            elif "IP  Dest: " in line:
                ip_dst = IPv4Address(line.strip().split()[2])
                is_tcp = False
            elif "Type: " in line:
                ip_type = line.strip().split("(")[1].split(")")[0]
            elif "HLEN: " in line and not is_tcp:
                ip_hdrlen = int(line.strip().split()[1])
            elif "TTL: " in line:
                ttl = int(line.strip().split()[1])
            elif "LEN: " in line and "HLEN: " not in line and "DLEN: " not in line:
                ip_len = int(line.strip().split()[1])
            elif "ID: " in line:
                ip_id  = int(line.strip().split()[1])
            elif "CKSUM: " in line and not is_tcp:
                ip_chksum = line.strip().split()[1]
            elif "OFFSET: " in line:
                ip_offset = " ".join(line.strip().split()[1:])
            elif "TCP SPRT: " in line:
                tcp_src = int(line.strip().split()[2])
                is_tcp = True
            elif "DPRT: " in line:
                tcp_dst = int(line.strip().split()[1])
            elif "FLG: " in line:
                tcp_flg = get_resolved_tcpflags(line.strip().split()[1])
            elif "SEQ: " in line:
                seq_no = int(line.strip().split()[1])
            elif "ACK: " in line:
                ack_no = int(line.strip().split()[1])
            elif "WIN: " in line:
                tcp_window = int(line.strip().split()[1])
            elif "HLEN: " in line and is_tcp:
                tcp_hdrlen = int(line.strip().split()[1])
            elif "CKSUM: " in line and is_tcp:
                tcp_chksum = line.strip().split()[1]
            elif "DLEN: " in line:
                pkt_size = int(line.strip().split()[1])
            elif "OPTS: " in line:
                opts_len = int(line.strip().split()[1])
                tcp_opts = " ".join(line.strip().split()[3:])
            elif "data: " in line:
                data_len = int(line.strip().split()[1])
            
            if ("Packet " in line and pkt_count>1) or (" packets seen, " in line and " TCP packets traced" in line):
                if " packets seen, " in line and " TCP packets traced" in line:
                    last_pkt_no = pkt_no # Handle packet no. for the last packet in the packet data
                pkt_info = get_pkt_info_dict()
                pkt_info["pktno"]     = last_pkt_no
                pkt_info["savedlen"]  = saved_len
                pkt_info["timestamp"] = tstamp
                pkt_info["ipvers"]    = ip_vers
                pkt_info["ipsrc"]     = ip_src
                pkt_info["ipdst"]     = ip_dst
                pkt_info["transtype"] = ip_type
                pkt_info["iphdrlen"]  = ip_hdrlen
                pkt_info["ttl"]       = ttl
                pkt_info["iplen"]     = ip_len
                pkt_info["ipid"]      = ip_id
                pkt_info["ipchksum"]  = ip_chksum
                pkt_info["offset"]    = ip_offset
                pkt_info["tcpsrc"]    = tcp_src
                pkt_info["tcpdst"]    = tcp_dst
                pkt_info["tcpflags"]  = tcp_flg
                pkt_info["seqno"]     = seq_no
                pkt_info["ackno"]     = ack_no
                pkt_info["tcpwindow"] = tcp_window
                pkt_info["tcphdrlen"] = tcp_hdrlen
                pkt_info["tcpchksum"] = tcp_chksum
                pkt_info["pktsize"]   = pkt_size
                pkt_info["optslen"]   = opts_len
                pkt_info["tcpopts"]   = tcp_opts
                pkt_info["datalen"]   = data_len

                all_packets.append(pkt_info)

                opts_len = None
                tcp_opts = None
                data_len = None

    print("\t\t Parsed {} M packets so far...".format(int(pkt_count/1000000)), flush=True)
    with open(tcptrace_data_paths["all_pkts_pickle"].format(str(seq_count).zfill(2)), "wb") as packets_fp:
        pickle.dump(all_packets, packets_fp)
    
    print("Done!", flush=True)

##################################################

def send_traffic_through_p4rtt(tcptrace_data_paths, flowtab_params, pkttab_params):
    ''' Compute valid RTT samples on the entire dataset based on our algorithm '''

    def flowShouldExpire(evicted_record, expiry_check_arg=None):

        _, (highest_byte_acked_or_rexmited, highest_byte_transmitted) = evicted_record
        if highest_byte_acked_or_rexmited == highest_byte_transmitted and highest_byte_acked_or_rexmited > -1:
            return True

        return False
    
    def packetShouldExpire(evicted_record, highest_byte_acked_or_rexmited):

        (_, _, _, _, exp_ack), _ = evicted_record
        # print("exp ack: {}, hb_ar: {}".format(exp_ack, highest_byte_acked_or_rexmited))
        if exp_ack <= highest_byte_acked_or_rexmited:
            return True

        return False

    print("Compute valid RTT samples using Cuckoo hashing and the confidence interval method...", flush=True)

    flow_table   = CHT.CuckooHashTable(num_stages=flowtab_params["num_stages"], max_size=flowtab_params["max_size"],
                                       recirculations=flowtab_params["recirculations"], prefer_new=flowtab_params["prefer_new"],
                                       log_interval=flowtab_params["log_interval"], shouldExpire=flowShouldExpire)
    packet_table = CHT.CuckooHashTable(num_stages=pkttab_params["num_stages"], max_size=pkttab_params["max_size"],
                                       recirculations=pkttab_params["recirculations"], prefer_new=pkttab_params["prefer_new"],
                                       log_interval=pkttab_params["log_interval"], shouldExpire=packetShouldExpire)

    seq_count = 0
    rtt_samples = {}
    rtt_samples_count = 0
    report_count = 0

    while seq_count < 14:

        print("\t Proceeding for trace partition {} out of {}...".format(seq_count+1, 14), flush=True)

        with open(tcptrace_data_paths["all_pkts_pickle"].format(str(seq_count).zfill(2)), "rb") as packets_fp:
            packets = pickle.load(packets_fp)
        
        print("\t\t Loaded current trace partition...", flush=True)

        uniq_flows = {}
        
        for count_packet, packet in enumerate(packets):

            flow_key = (packet["ipsrc"], packet["ipdst"], packet["tcpsrc"], packet["tcpdst"])

            # Account for flow in unique flows dictionary
            if flow_key not in uniq_flows:
                uniq_flows[flow_key] = 0
            uniq_flows[flow_key] += 1
            
            # Initialize flow if not present; fetch confidence interval
            flow_key = (packet["ipsrc"], packet["ipdst"], packet["tcpsrc"], packet["tcpdst"])
            flow_record = flow_table.lookup(flow_key)
            if flow_record is None:
                highest_byte_acked_or_rexmited, highest_byte_transmitted = -1, -1
                flow_table.insert(flow_key, (-1, -1), None, packet["timestamp"])
            else:
                _, (highest_byte_acked_or_rexmited, highest_byte_transmitted) = flow_record

            
            ## Handle SEQ direction
            
            # Compute packet key (4-tuple, eACK)
            packet["tcpflags"] = packet["tcpflags"][2:]
            exp_ack = packet["seqno"] + packet["pktsize"]
            if "S" in packet["tcpflags"] or "F" in packet["tcpflags"]: exp_ack += 1
            packet_key = (packet["ipsrc"], packet["ipdst"], packet["tcpsrc"], packet["tcpdst"], exp_ack)

            # Basic check before insertion into packet table (not pure ACK, not RESET)
            if not (packet["tcpflags"] == "-A----" and packet["pktsize"] == 0) and "R" not in packet["tcpflags"]:
                packet_record = packet_table.lookup(packet_key)
                if packet_record is None:
                    # New packet in confidence interval: Extend confidence interval
                    # print("SEQ insert:: key={}, data={}, expiry_arg={}".format(packet_key, packet["timestamp"], highest_byte_acked_or_rexmited))
                    packet_table.insert(packet_key, packet["timestamp"], highest_byte_acked_or_rexmited, packet["timestamp"])
                    flow_table.update(flow_key, (highest_byte_acked_or_rexmited, exp_ack))
                else:
                    # Retransmitted packet: Collapse confidence interval
                    flow_table.update(flow_key, (highest_byte_transmitted, highest_byte_transmitted))

            
            ## Handle ACK direction
            
            ack_key = (packet["ipdst"], packet["ipsrc"], packet["tcpdst"], packet["tcpsrc"], packet["ackno"])
            packet_record = packet_table.lookup(ack_key)

            # If match exists and the ACK is within confidence interval, compute RTT sample and update confidence interval
            if packet_record is not None:
                if packet["ackno"] > highest_byte_acked_or_rexmited:
                    _, insertion_timestamp = packet_record
                    rtt = (packet["timestamp"] - insertion_timestamp)/timedelta(milliseconds=1)
                    flow_table.update(flow_key, (packet["ackno"], highest_byte_transmitted))
                    # packet_table.update(ack_key, None)

                    # Send to collector
                    if flow_key not in rtt_samples:
                        rtt_samples[flow_key] = []
                    rtt_samples[flow_key].append(rtt)
                    rtt_samples_count += 1
            
            ## Report stats
            if (count_packet+1) % 100000 == 0:
                report_count += 1
                print("Report count: {}\n\t FT occupancy = {}%; FT failure rate = {}%; FT recirculation rate = {}%; FT insertion load = {}%; FT expiration rate = {}%".format(
                        report_count, flow_table.getOccupancy(), flow_table.getFailureRate(), flow_table.getRecirculationRate(), flow_table.getInsertionLoad(), flow_table.getExpirationRate()
                ))
                print("\t PT occupancy = {}%; PT failure rate = {}%; PT recirculation rate = {}%; PT insertion load = {}%; PT expiration rate = {}%".format(
                        packet_table.getOccupancy(), packet_table.getFailureRate(), packet_table.getRecirculationRate(), packet_table.getInsertionLoad(), packet_table.getExpirationRate()
                ))
                print("\t RTT samples: {}\n".format(rtt_samples_count))
            
            # Test
            if (count_packet+1) % 200000 == 0:
                break

        print("\t Plot CHT stats...", flush=True)
        packet_table.plot_logs(tcptrace_data_paths, "Packet Table")
        flow_table.plot_logs(tcptrace_data_paths, "Flow Table")
        
        print("\t Done for trace partition {} out of {}...".format(seq_count+1, 14), flush=True)
        seq_count += 1

        break

    print("Unique flows", len(uniq_flows))
    
    # print("Storing RTT samples to pickle file...", flush=True)
    # with open(tcptrace_data_paths["rtt_samples_pickle"], "wb") as rtt_fp:
    #     pickle.dump(rtt_samples, rtt_fp)
    
    print("Done!", flush=True)

##################################################

def main():
    return

##################################################

if __name__ == "__main__":
    main()

##################################################
