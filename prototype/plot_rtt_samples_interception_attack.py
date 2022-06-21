from scapy.all import *
import sys

import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

sns.set()
sns.set_style("whitegrid")
font = {'family' : 'serif',
        # 'weight' : 'bold',
        'size'   : 52}
matplotlib.rc('font', **font)
plt.rc('xtick',labelsize=25)
plt.rc('ytick',labelsize=25)
plt.rc('axes',labelsize=30)
plt.rc('legend',fontsize=23)

########################################

def extract_tcptrace_samples(bgp_samples_path):

    tcptrace_samples = []
    tcptrace_seqnos  = []
    with open(bgp_samples_path, "r") as fp:
        lines = [l.strip() for l in fp.readlines()]
        for line in lines:
            tokens = line.split()
            tcptrace_seqnos.append(int(tokens[0]))
            tcptrace_samples.append(int(tokens[1]))

    return tcptrace_samples, tcptrace_seqnos

########################################

def extract_rtt_samples(src_trace_path):

    packets = PcapReader(src_trace_path)
    rtt_samples = []
    pkt_timestamps = []
    pkt_acknos = []

    for i, packet in enumerate(packets):

        src_ip   = packet[IP].src
        dst_ip   = packet[IP].dst
        src_port = packet[UDP].sport
        dst_port = packet[UDP].dport
        c_seq    = packet[IP].id
        c_ack    = packet[IP].tos
        c_recirc = packet[UDP].chksum

        payload  = packet[UDP].payload
        ack_no   = int.from_bytes(bytes(payload)[:4], byteorder="big")
        pkt_ts   = int.from_bytes(bytes(payload)[4:8], byteorder="big")
        rtt      = int.from_bytes(bytes(payload)[8:12], byteorder="big")

        # print(src_ip, dst_ip, src_port, dst_port, c_seq, c_ack, c_recirc, ack_no, pkt_ts, rtt)
        # if (i==5): break
        rtt_samples.append(rtt)
        pkt_timestamps.append(pkt_ts)
        pkt_acknos.append(ack_no)

    return rtt_samples, pkt_timestamps, pkt_acknos

########################################

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

########################################

def plot_attack_detection(rtt_samples, pkt_timestamps):

    rtt_samples = [r/1000 for r in rtt_samples]
    pkt_timestamps = [t/1000000 for t in pkt_timestamps]

    window_size  = 8
    
    rtt_windows  = chunks(rtt_samples, window_size)
    time_windows = chunks(pkt_timestamps, window_size)
    
    rtt_window_mins  = [min(rw) for rw in rtt_windows]
    time_window_mins = [min(tw) for tw in time_windows]

    plt.figure(figsize=(12,8))
    sns.lineplot(pkt_timestamps, rtt_samples, marker="o", markersize=10,
                    markeredgecolor=None, label="P4RTT RTT Samples")
    ax = sns.lineplot(time_window_mins, rtt_window_mins, marker="x", markersize=16,
                        markeredgecolor=None, label="Minimum RTT (Window=8)")

    plt.scatter(x=time_window_mins[35], y=rtt_window_mins[35], color="darkorange", marker="*",
                zorder=10, alpha=1, s=600, label="Attack Suspected")
    plt.scatter(x=time_window_mins[36], y=rtt_window_mins[36], color="red", marker="*",
                zorder=10, alpha=1, s=600, label="Attack Confirmed")
    
    ax.get_lines()[0].set_linewidth(2)
    ax.get_lines()[1].set_linewidth(1.5)
    ax.get_lines()[1].set_linestyle("--")

    plt.xlabel("Time (s)")
    plt.ylabel("RTT (ms)")
    plt.xlim(25, 50)
    plt.ylim(0, 230)

    plt.legend()
    plt.tight_layout()
    # plt.savefig("bgp_attack_rtts.png", format="png", dpi=300)
    plt.savefig("~/sigcomm22-paper67-artifacts/plots/bgp_attack_rtts.pdf", format="pdf", dpi=300)

########################################

def plot_comparison_with_tcptrace(rtt_samples, pkt_timestamps, pkt_acknos, tcptrace_samples, tcptrace_seqnos):

    print("tcptrace len: {}, p4rtt len: {}".format(len(tcptrace_samples), len(rtt_samples)))
    print(rtt_samples[1], pkt_timestamps[1], pkt_acknos[1], tcptrace_samples[1], tcptrace_seqnos[1])

    rtt_samples = [r/1000 for r in rtt_samples]

    sns.lineplot(pkt_acknos, rtt_samples, label="P4RTT")
    sns.lineplot(tcptrace_seqnos, tcptrace_samples, label="tcptrace")

    plt.xlabel("TCP Sequence/ACK number")
    plt.ylabel("RTT (ms)")

    plt.tight_layout()
    plt.savefig("bgp_attack_rtts_tcptrace_comparison.png", format="png", dpi=300)
    # plt.savefig("bgp_attack_rtts.pdf", format="pdf", dpi=300)

########################################

def main():
    if len(sys.argv) < 2:
        raise Exception("1 argument expected")
    
    src_trace_path   = sys.argv[1]
    # bgp_samples_path = sys.argv[2]
    # output_plot_path = sys.argv[2]

    # tcptrace_samples, tcptrace_seqnos = extract_tcptrace_samples(bgp_samples_path)
    rtt_samples, pkt_timestamps, pkt_acknos = extract_rtt_samples(src_trace_path)
    # plot_comparison_with_tcptrace(rtt_samples, pkt_timestamps, pkt_acknos, tcptrace_samples, tcptrace_seqnos)
    plot_attack_detection(rtt_samples, pkt_timestamps)

########################################

if __name__ == "__main__":
    main()

########################################
