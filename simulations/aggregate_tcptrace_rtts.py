from ipaddress import IPv4Address
import numpy as np
import pickle
import os

########################################

def aggregate_rtts():

    PICKLE_PATH  = "/home/ubuntu/sigcomm22-paper67-artifacts/simulations/intermediate/smallFlows.pickle"
    TCPTRACE_SMY = "/home/ubuntu/sigcomm22-paper67-artifacts/simulations/intermediate/tcptrace_nlrZ.txt"
    TCPTRACE_DIR = "/home/ubuntu/sigcomm22-paper67-artifacts/simulations/intermediate/rtts"
    OUTPUT_PATH  = "/home/ubuntu/sigcomm22-paper67-artifacts/simulations/intermediate"

    rtt_files_map = {}
    for f in os.listdir(TCPTRACE_DIR):
        tokens = f.split("_")[0].split("2")
        rtt_files_map[(tokens[0], tokens[1])] = f

    connection_map = {}
    with open(TCPTRACE_SMY) as fp:
        lines = [r.strip() for r in fp.readlines()]
    lc = 0
    while lc < len(lines):
        if "TCP connection " in lines[lc] and "TCP connection info:" not in lines[lc]:
            host1 = lines[lc+1].split()[1].replace(":", "")
            host2 = lines[lc+2].split()[1].replace(":", "")
            ip1   = IPv4Address(lines[lc+1].split()[2].split(":")[0])
            ip2   = IPv4Address(lines[lc+2].split()[2].split(":")[0])
            port1 = int(lines[lc+1].split()[2].split(":")[1])
            port2 = int(lines[lc+2].split()[2].split(":")[1])
            if (host1, host2) in rtt_files_map:
                connection_map[(ip1, ip2, port1, port2)] = rtt_files_map[(host1, host2)]
            if (host2, host1) in rtt_files_map:
                connection_map[(ip2, ip1, port2, port1)] = rtt_files_map[(host2, host1)]
            lc += 3
        lc += 1

    tcptrace_rtts_all   = {}
    tcptrace_rtts_nosyn = {}
    tcptrace_rtts_syn   = {}
    
    with open(PICKLE_PATH, "rb") as fp:
        packets = pickle.load(fp)
    for packet in packets:
        (_, _, src_ip, dst_ip, src_port, dst_port, tcp_flgs, seq_num, _, _) = packet
        conn_tuple = (src_ip, dst_ip, src_port, dst_port)
        if conn_tuple not in connection_map:
            continue
        with open(os.path.join(TCPTRACE_DIR, connection_map[conn_tuple])) as fp:
            lines = [l.strip() for l in fp.readlines()]
            for line in lines:
                tokens  = line.split(" ")
                rtt_seq = int(tokens[0])
                rtt     = int(tokens[1])
                if seq_num == rtt_seq:
                    
                    # All RTTs
                    if conn_tuple not in tcptrace_rtts_all:
                        tcptrace_rtts_all[conn_tuple] = []
                    tcptrace_rtts_all[conn_tuple].append((seq_num, rtt))

                    if "S" in tcp_flgs:
                        # Handshake RTTs
                        if conn_tuple not in tcptrace_rtts_syn:
                            tcptrace_rtts_syn[conn_tuple] = []
                        tcptrace_rtts_syn[conn_tuple].append((seq_num, rtt))
                    else:
                        # Non-handshake RTTs
                        if conn_tuple not in tcptrace_rtts_nosyn:
                            tcptrace_rtts_nosyn[conn_tuple] = []
                        tcptrace_rtts_nosyn[conn_tuple].append((seq_num, rtt))

    with open(os.path.join(OUTPUT_PATH, "tcptrace_rtts_all.pickle"), "wb") as fp:
        pickle.dump(tcptrace_rtts_all, fp)

    with open(os.path.join(OUTPUT_PATH, "tcptrace_rtts_syn.pickle"), "wb") as fp:
        pickle.dump(tcptrace_rtts_syn, fp)

    with open(os.path.join(OUTPUT_PATH, "tcptrace_rtts_nosyn.pickle"), "wb") as fp:
        pickle.dump(tcptrace_rtts_nosyn, fp)

########################################

def main():
    aggregate_rtts()

########################################

if __name__ == "__main__":
    main()

########################################