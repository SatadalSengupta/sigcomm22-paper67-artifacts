from ipaddress import IPv4Address
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pickle
import os

########################################

sns.set()
sns.set_style("whitegrid")
font = {'family' : 'serif',
        # 'weight' : 'bold',
        'size'   : 25}
matplotlib.rc('font', **font)
plt.rc('xtick',labelsize=23)
plt.rc('ytick',labelsize=25)
plt.rc('axes',labelsize=30)
plt.rc('legend',fontsize=23)

########################################

def count_successful_handshakes():

    PICKLE_PATH = "/home/ubuntu/sigcomm22-paper67-artifacts/simulations/intermediate/smallFlows.pickle"
    with open(PICKLE_PATH, "rb") as fp:
        packets = pickle.load(fp)
    
    handshake_status = {}
    
    for packet_data in packets:
        packet = {}
        packet["pktno"], packet["timestamp"], packet["ipsrc"], packet["ipdst"], packet["tcpsrc"], \
            packet["tcpdst"], packet["tcpflags"], packet["seqno"], packet["ackno"], packet["pktsize"] = packet_data
        packet["tcpflags"] = packet["tcpflags"][2:]

        conn_tuple_fwd = (packet["ipsrc"], packet["ipdst"], packet["tcpsrc"], packet["tcpdst"])
        conn_tuple_rev = (packet["ipdst"], packet["ipsrc"], packet["tcpdst"], packet["tcpsrc"])

        if conn_tuple_fwd in handshake_status and handshake_status[conn_tuple_fwd] == 2:
            continue
        
        if conn_tuple_rev in handshake_status and handshake_status[conn_tuple_rev] == 2:
            continue

        if conn_tuple_fwd not in handshake_status and conn_tuple_rev not in handshake_status:
            handshake_status[conn_tuple_fwd] = -1 #Initialize
        
        if conn_tuple_fwd in handshake_status:
            ## SEQ direction
            if handshake_status[conn_tuple_fwd] == -1:
                if "S" in packet["tcpflags"] and "A" not in packet["tcpflags"]:
                    handshake_status[conn_tuple_fwd] = 0 #SYN
                else:
                    handshake_status[conn_tuple_fwd] = 3 #Other
            elif handshake_status[conn_tuple_fwd] == 1:
                if "S" not in packet["tcpflags"] and "A" in packet["tcpflags"]:
                    handshake_status[conn_tuple_fwd] = 2 #3WHS
                else:
                    handshake_status[conn_tuple_fwd] = 4 #Failure
        
        elif conn_tuple_rev in handshake_status:
            ## ACK direction
            if handshake_status[conn_tuple_rev] == 0:
                if "S" in packet["tcpflags"] and "A" in packet["tcpflags"]:
                    handshake_status[conn_tuple_rev] = 1 #SYNACK
                else:
                    handshake_status[conn_tuple_fwd] = 4 #Failure
    
    conn_count = 0
    fail_count = 0
    succ_count = 0

    for conn_tuple in handshake_status:
        if handshake_status[conn_tuple] == 4:
            fail_count += 1
        elif handshake_status[conn_tuple] == 2:
            succ_count += 1
        conn_count += 1
    
    print(f"Total no. of connections: {conn_count}")
    print(f"Successful handshakes: {succ_count}")
    print(f"Failed handshakes: {fail_count}")

    return conn_count, fail_count, succ_count

########################################

def collect_rtts():

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

    tcptrace_rtts_all   = []
    tcptrace_rtts_nosyn = []
    tcptrace_rtts_syn   = []
    
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
                    tcptrace_rtts_all.append(rtt)
                    if "S" in tcp_flgs:
                        tcptrace_rtts_syn.append(rtt)
                    else:
                        tcptrace_rtts_nosyn.append(rtt)

    lines = "\n".join([str(rtt) for rtt in tcptrace_rtts_all])
    with open(os.path.join(OUTPUT_PATH, "tcptrace_rtts_all.txt"), "w") as fp:
        fp.write(lines)

    lines = "\n".join([str(rtt) for rtt in tcptrace_rtts_nosyn])
    with open(os.path.join(OUTPUT_PATH, "tcptrace_rtts_nosyn.txt"), "w") as fp:
        fp.write(lines)
                    
    lines = "\n".join([str(rtt) for rtt in tcptrace_rtts_syn])
    with open(os.path.join(OUTPUT_PATH, "tcptrace_rtts_syn.txt"), "w") as fp:
        fp.write(lines)
    
    return len(tcptrace_rtts_all), len(tcptrace_rtts_syn)

########################################

def compare_handshake_rtts(conn_count, succ_count, all_rtts_count, handshake_rtts_count):

    PLOT_PATH = "/home/ubuntu/sigcomm22-paper67-artifacts/plots"

    plt.figure(figsize=(12,8))
    x = ["All\nConnections", "Missing\nHandshakes", "All\nRTTs", "Handshake\nRTTs"]
    y1 = [100, 100]
    y2 = [(conn_count-succ_count)/conn_count*100, (handshake_rtts_count/all_rtts_count)*100]
    val = [str(conn_count), f"{round(all_rtts_count/1000, 2)} K",
            str(conn_count-succ_count), f"{round(handshake_rtts_count/1000, 2)} K"]

    ind = np.arange(1, 3)
    width = 0.35
    rects1 = plt.bar(ind, y1, width)
    rects2 = plt.bar(ind+width, y2, width)

    for i, rect in enumerate(rects1):
        height = rect.get_height()
        plt.text(rect.get_x() + rect.get_width()/2., 1.05*height,
                    val[i],
                    ha='center', va='bottom')
    for i, rect in enumerate(rects2):
        height = rect.get_height()
        plt.text(rect.get_x() + rect.get_width()/2., 1.05*height,
                    val[2+i],
                    ha='center', va='bottom')

    plt.ylabel("Percentage")
    plt.xticks([1, 1.4, 2, 2.35], x)
    plt.tight_layout()
    plot_filepath = os.path.join(PLOT_PATH, "figure_12_equivalent.pdf")
    plt.savefig(plot_filepath, format="pdf", dpi=300)
    plt.close()
    plt.clf()

    print(f"Plot saved in: {plot_filepath}")

########################################

def main():
    conn_count, fail_count, succ_count   = count_successful_handshakes()
    all_rtts_count, handshake_rtts_count = collect_rtts()
    compare_handshake_rtts(conn_count, succ_count, all_rtts_count, handshake_rtts_count)

########################################

if __name__ == "__main__":
    main()

########################################
