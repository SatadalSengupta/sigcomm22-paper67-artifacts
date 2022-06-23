from ipaddress import IPv4Address
from datetime import datetime, timedelta
from scapy.all import *
import pickle
import sys

########################################

def get_flags(flags):
    flags_str = list("--------")
    if "U" in flags:
        flags_str[2] = "U"
    if "A" in flags:
        flags_str[3] = "A"
    if "P" in flags:
        flags_str[4] = "P"
    if "R" in flags:
        flags_str[5] = "R"
    if "S" in flags:
        flags_str[6] = "S"
    if "F" in flags:
        flags_str[7] = "F"
    return "".join(flags_str)

########################################

def parse_trace(src_trace_path, dst_trace_path):

    packets = PcapReader(src_trace_path)
    data = []
    count = 0

    for i, packet in enumerate(packets):
    
        if TCP in packet:
            us_time  = int((float(packet.time) - int(packet.time)) * 1000000)
            pkt_time = datetime.fromtimestamp(int(packet.time)) + timedelta(microseconds=us_time)
            src_ip   = IPv4Address(packet[IP].src)
            dst_ip   = IPv4Address(packet[IP].dst)
            src_port = int(packet[TCP].sport)
            dst_port = int(packet[TCP].dport)
            tcp_flgs = get_flags(str(packet[TCP].flags))
            seq_num  = int(packet[TCP].seq)
            ack_num  = int(packet[TCP].ack)
            tcp_len  = len(packet[TCP].payload)

            data.append((count, pkt_time, src_ip, dst_ip, src_port, dst_port, tcp_flgs, seq_num, ack_num, tcp_len))
            count += 1
    
    with open(dst_trace_path, "wb") as fp:
        pickle.dump(data, fp)

    return

########################################

def main():

    if len(sys.argv) < 3:
        raise Exception("2 arguments expected")
    
    src_trace_path = sys.argv[1]
    dst_trace_path = sys.argv[2]

    parse_trace(src_trace_path, dst_trace_path)

    return

########################################

if __name__ == "__main__":
    main()

########################################
