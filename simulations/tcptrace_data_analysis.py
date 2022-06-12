import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import math
import pickle
import os

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

def collect_rtts():

    PATH = "/u/satadals/mnt/tcptrace_base_data/tcptrace_raw_data/tcptrace_populated_flows_rtt"
    OUT_PATH = "/u/satadals/scratch/trace_04_07_2020"

    tcptrace_rtts_all = []
    tcptrace_rtts_nosyn = []
    tcptrace_rtts_syn = []

    for fc, filename in enumerate(os.listdir(PATH)):
        pathname = os.path.join(PATH, filename)
        print("File count: {} :: Path: {}".format(fc, pathname))
        tcptrace_data = None
        with open(pathname, "rb") as fp:
            tcptrace_data = pickle.load(fp)
        for cc, conn in enumerate(tcptrace_data):
            if (cc+1)%1000000 == 0:
                print("\t Connections processed: {}M".format((cc+1)//1000000))
            ext_leg_pkts = conn["leg_external"]["combined_data"]
            for pkt in ext_leg_pkts:
                rtt_val = pkt["rtt"]
                if rtt_val is not None:
                    tcptrace_rtts_all.append(rtt_val)
                    if "S" not in pkt["tcpflags"]:
                        tcptrace_rtts_nosyn.append(rtt_val)
                    else:
                        tcptrace_rtts_syn.append(rtt_val)

    lines = "\n".join([str(rtt) for rtt in tcptrace_rtts_all])
    with open(os.path.join(OUT_PATH, "tcptrace_rtts_all.txt"), "w") as fp:
        fp.write(lines)

    lines = "\n".join([str(rtt) for rtt in tcptrace_rtts_nosyn])
    with open(os.path.join(OUT_PATH, "tcptrace_rtts_nosyn.txt"), "w") as fp:
        fp.write(lines)
                    
    lines = "\n".join([str(rtt) for rtt in tcptrace_rtts_syn])
    with open(os.path.join(OUT_PATH, "tcptrace_rtts_syn.txt"), "w") as fp:
        fp.write(lines)

########################################

def count_packets():

    PATH = "/u/satadals/mnt/tcptrace_base_data/tcptrace_raw_data/tcptrace_packet_data/all_packets_meandata.pickle"

    with open(PATH, "rb") as fp:
        packets = pickle.load(fp)
    syn_counter = 0

    print("Will start counting")

    for count_packet, packet_data in enumerate(packets):

        if (count_packet+1)%1000 == 0:
            print("{} K packets processed".format((count_packet+1)//1000))
            print("Total packets: {}".format(count_packet+1))
            print("SYN packets: {}".format(syn_counter))
            print("Percentage: {}".format(round(syn_counter*100/(count_packet+1), 2)))

        packet = {}
        packet["pktno"], packet["timestamp"], packet["ipsrc"], packet["ipdst"], packet["tcpsrc"], \
            packet["tcpdst"], packet["tcpflags"], packet["seqno"], packet["ackno"], packet["pktsize"] = packet_data
        packet["tcpflags"] = packet["tcpflags"][2:]
        
        if "S" in packet["tcpflags"]:
            syn_counter += 1
    
    print("Total packets: {}".format(count_packet+1))
    print("SYN packets: {}".format(syn_counter))
    print("Percentage: {}".format(round(syn_counter*100/(count_packet+1), 2)))

########################################

def syn_comparison():

    plt.figure(figsize=(12,8))
    x = ["All\nConnections", "Incomplete\nHandshakes", "All\nRTTs", "Handshake\nRTTs"]
    y1 = [100, 100]
    y2 = [(1003.75/1384.446)*100, (319.845/7529.477)*100]
    val = ["1.38 M", "7.5 M", "1.0 M", "0.3 M"]

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
    # plt.xlabel("SYN-only Flows vs. Handshake RTTs")
    plt.xticks([1, 1.4, 2, 2.35], x)
    plt.tight_layout()
    # plt.savefig("/u/satadals/scratch/trace_04_07_2020/tcptrace_inf_mem_count.png", format="png", dpi=300)
    plt.savefig("/u/satadals/scratch/trace_04_07_2020/syn_comparison.pdf", format="pdf", dpi=300)
    plt.close()
    plt.clf()

########################################

def main():
    # collect_rtts()
    # count_packets()
    syn_comparison()

########################################

if __name__ == "__main__":
    main()

########################################
