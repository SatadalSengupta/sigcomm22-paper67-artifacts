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

def collect_rtts_counts():

    ALL_RTTS_PATH = "/home/ubuntu/sigcomm22-paper67-artifacts/simulations/intermediate/tcptrace_rtts_all.pickle"
    HSK_RTTS_PATH = "/home/ubuntu/sigcomm22-paper67-artifacts/simulations/intermediate/tcptrace_rtts_syn.pickle"

    all_rtts_count       = 0
    handshake_rtts_count = 0

    with open(ALL_RTTS_PATH, "rb") as fp:
        data = pickle.load(fp)
        for conn_tuple in data:
            all_rtts_count += len(data[conn_tuple])
    
    with open(HSK_RTTS_PATH, "rb") as fp:
        data = pickle.load(fp)
        for conn_tuple in data:
            handshake_rtts_count += len(data[conn_tuple])

    return all_rtts_count, handshake_rtts_count

########################################

def compare_handshake_rtts(conn_count, succ_count, all_rtts_count, handshake_rtts_count):

    PLOT_PATH = "/home/ubuntu/sigcomm22-paper67-artifacts/plots"

    print(f"No. of connections: {conn_count}")
    print(f"No. of missing handshakes: {conn_count-succ_count}")
    print(f"No. of RTT samples: {all_rtts_count}")
    print(f"No. of handshake RTTs: {handshake_rtts_count}")

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
    all_rtts_count, handshake_rtts_count = collect_rtts_counts()
    compare_handshake_rtts(conn_count, succ_count, all_rtts_count, handshake_rtts_count)

########################################

if __name__ == "__main__":
    main()

########################################
