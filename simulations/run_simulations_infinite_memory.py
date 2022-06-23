from datetime import datetime, timedelta
from TCPTraceConst import TCPTraceConst
import pickle
import os

##################################################

def compare_tcptrace_and_dartmeminf_rtts(dart_rtts):

    TCPTRACE_ALL_RTTS_PATH = "/home/ubuntu/sigcomm22-paper67-artifacts/simulations/intermediate/tcptrace_rtts_all.pickle"
    with open(TCPTRACE_ALL_RTTS_PATH, "rb") as fp:
        tcptrace_rtts = pickle.load(fp)

    for fkey in tcptrace_rtts:
        missing_rtts = set(tcptrace_rtts[fkey]) - set(dart_rtts[fkey])
        if len(missing_rtts) > 0:
            print(missing_rtts)
            break

    return

##################################################

def main():

    t_format = "%Y-%m-%d %H:%M:%S"
    t_start  = datetime.now()
    print("Starting simulations at time: {}".format(t_start.strftime(t_format)))

    local_path = "/home/ubuntu/sigcomm22-paper67-artifacts/simulations/intermediate/dart_simulations_infmem"

    tcptrace_const_syn   = TCPTraceConst(local_path, 2000)
    tcptrace_const_nosyn = TCPTraceConst(local_path, 2000)
    
    process_packets_path = "/home/ubuntu/sigcomm22-paper67-artifacts/simulations/intermediate/smallFlows.pickle"
    with open(process_packets_path, "rb") as packets_fp:
        packets = pickle.load(packets_fp)
    
    packets_count = 0

    for packet_data in packets:

        packet = {}
        packet["pktno"], packet["timestamp"], packet["ipsrc"], packet["ipdst"], packet["tcpsrc"], \
            packet["tcpdst"], packet["tcpflags"], packet["seqno"], packet["ackno"], packet["pktsize"] = packet_data
        packet["tcpflags"] = packet["tcpflags"][2:]

        if packets_count == 0:
            tcptrace_const_syn._firstEntryTime   = packet["timestamp"]
            tcptrace_const_nosyn._firstEntryTime = packet["timestamp"]
            
        tcptrace_const_syn.process_tcptrace_SEQ(packet, allow_syn=True)
        tcptrace_const_nosyn.process_tcptrace_SEQ(packet, allow_syn=False)

        tcptrace_const_syn.process_tcptrace_ACK(packet, allow_syn=True)
        tcptrace_const_nosyn.process_tcptrace_ACK(packet, allow_syn=False)

        # print("tcptrace with SYN:")
        # print(tcptrace_const_syn._tcptrace_flow_table)
        # print(tcptrace_const_syn._tcptrace_packet_table)
        # print(tcptrace_const_syn._tcptrace_sample_count)
        # print(tcptrace_const_syn._tcptrace_rtt_samples)

        # print("tcptrace with no SYN:")
        # print(tcptrace_const_nosyn._tcptrace_flow_table)
        # print(tcptrace_const_nosyn._tcptrace_packet_table)
        # print(tcptrace_const_nosyn._tcptrace_sample_count)
        # print(tcptrace_const_nosyn._tcptrace_rtt_samples)

        # if packets_count == 10:
        #     break
            
        packets_count += 1
    
    tcptrace_const_syn.concludeRTTDict()
    tcptrace_const_nosyn.concludeRTTDict()

    tcptrace_syn_rtt_all = []
    for flow_key in tcptrace_const_syn._tcptrace_rtt_samples:
        tcptrace_syn_rtt_all.extend([t[1] for t in tcptrace_const_syn._tcptrace_rtt_samples[flow_key]])
    
    tcptrace_nosyn_rtt_all = []
    for flow_key in tcptrace_const_nosyn._tcptrace_rtt_samples:
        tcptrace_nosyn_rtt_all.extend([t[1] for t in tcptrace_const_nosyn._tcptrace_rtt_samples[flow_key]])

    with open(os.path.join(local_path, "rtt_samples_tcptrace_const_syn.txt"), "w") as fp:
        lines = ["{}".format(point) for point in tcptrace_syn_rtt_all]
        fp.write("\n".join(lines))
    
    with open(os.path.join(local_path, "rtt_samples_tcptrace_const_nosyn.txt"), "w") as fp:
        lines = ["{}".format(point) for point in tcptrace_nosyn_rtt_all]
        fp.write("\n".join(lines))

    t_end = datetime.now()
    t_elapsed = round((t_end - t_start)/timedelta(minutes=1), 2)
    print("Simulations complete at time: {}".format(t_end.strftime(t_format)))
    print("Time elapsed: {} mins.".format(t_elapsed))

    compare_tcptrace_and_dartmeminf_rtts(tcptrace_const_syn._tcptrace_rtt_samples)

##################################################

if __name__ == "__main__":
    main()

##################################################
