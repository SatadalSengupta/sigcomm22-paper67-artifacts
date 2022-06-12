from ipaddress import IPv4Address
import os, pickle

seq_pickle_path  = "/n/fs/anonflow/p4rtt_sata/tcptrace_parsed_data/packets_meandata_00.pickle"
sampled_test_pickle_path = "/n/fs/anonflow/p4rtt_sata/tcptrace_parsed_data/test_packets_sampled.pickle"
one_conn_test_pickle_path = "/n/fs/anonflow/p4rtt_sata/tcptrace_parsed_data/test_packets_one_conn.pickle"

print("Loading data...")
with open(seq_pickle_path, "rb") as read_fp:
    seq_data = pickle.load(read_fp)
print("Loaded data")

conn_info = {}

print("Creating connection dict...")
for packet_data in seq_data:

    packet = {}
    packet["pktno"], packet["timestamp"], packet["ipsrc"], packet["ipdst"], packet["tcpsrc"], \
        packet["tcpdst"], packet["tcpflags"], packet["seqno"], packet["ackno"], packet["pktsize"] = packet_data
    
    if packet["ipsrc"] <= packet["ipdst"]:
        ip1 = packet["ipsrc"]
        ip2 = packet["ipdst"]
    else:
        ip1 = packet["ipdst"]
        ip2 = packet["ipsrc"]
    
    if packet["tcpsrc"] <= packet["tcpdst"]:
        port1 = packet["tcpsrc"]
        port2 = packet["tcpdst"]
    else:
        port1 = packet["tcpdst"]
        port2 = packet["tcpsrc"]
    
    conn_key = (ip1, ip2, port1, port2)

    if conn_key not in conn_info:
        conn_info[conn_key] = [0, 0]
    
    if ip1 == packet["ipsrc"]:
        conn_info[conn_key][0] += 1
    else:
        conn_info[conn_key][1] += 1

print("Created connection dict")

print("Restructuring connection dict...")
for key in conn_info:
    conn_info[key] = min(conn_info[key][0], conn_info[key][1])
print("Restructed connection dict")

print("Sorting connection dict...")
sorted_conns = sorted(conn_info.items(), key=lambda x: x[1], reverse=True)
print("Sorted connection dict...")

print("Connection with highest no. of packets in both directions: {}".format(sorted_conns[0]))
selected_conn_key = sorted_conns[0][0]

print("Collecting packets from selected connection...")
packets_list = []

for packet_data in seq_data:

    packet = {}
    packet["pktno"], packet["timestamp"], packet["ipsrc"], packet["ipdst"], packet["tcpsrc"], \
        packet["tcpdst"], packet["tcpflags"], packet["seqno"], packet["ackno"], packet["pktsize"] = packet_data
    
    if packet["ipsrc"] <= packet["ipdst"]:
        ip1 = packet["ipsrc"]
        ip2 = packet["ipdst"]
    else:
        ip1 = packet["ipdst"]
        ip2 = packet["ipsrc"]
    
    if packet["tcpsrc"] <= packet["tcpdst"]:
        port1 = packet["tcpsrc"]
        port2 = packet["tcpdst"]
    else:
        port1 = packet["tcpdst"]
        port2 = packet["tcpsrc"]
    
    conn_key = (ip1, ip2, port1, port2)
    if conn_key == selected_conn_key:
        packets_list.append(packet_data)

print("Collected packets from selected connection")

print("Identifying retransmission event...")
packet_dict = {}
pure_ack_count = 0
duplicate_count = 0
sfr_count = 0
first_dup_index = 0

for i, packet_data in enumerate(packets_list):
    
    packet = {}
    packet["pktno"], packet["timestamp"], packet["ipsrc"], packet["ipdst"], packet["tcpsrc"], \
        packet["tcpdst"], packet["tcpflags"], packet["seqno"], packet["ackno"], packet["pktsize"] = packet_data
    
    if packet["tcpflags"][2:] == "-A----" and packet["pktsize"] == 0:
        pure_ack_count += 1
        continue

    if "S" in packet["tcpflags"][2:] or "F" in packet["tcpflags"][2:] or "R" in packet["tcpflags"][2:]:
        sfr_count += 1
        continue
    
    packet_key = (packet["ipsrc"], packet["ipdst"], packet["tcpsrc"], packet["tcpdst"], packet["seqno"])
    if packet_key in packet_dict:
        if duplicate_count <= 10:
            first_dup_index = int(i)
            print("Duplicate found in packet counts {} and {}, packet key: {}".format(packet_dict[packet_key], i, packet_key))
        duplicate_count += 1
    else:
        packet_dict[packet_key] = i

print("Pure ACKs: {}, Special flags: {}, Duplicates: {}".format(pure_ack_count, sfr_count, duplicate_count))


# Duplicate found in packet counts 105718 and 106778, packet key: (IPv4Address('17.253.15.203'), IPv4Address('10.8.152.240'), 443, 51506, 1958735154)
# Duplicate found in packet counts 105727 and 106779, packet key: (IPv4Address('17.253.15.203'), IPv4Address('10.8.152.240'), 443, 51506, 1958736528)
# Duplicate found in packet counts 105728 and 106780, packet key: (IPv4Address('17.253.15.203'), IPv4Address('10.8.152.240'), 443, 51506, 1958737902)
# Duplicate found in packet counts 105729 and 106781, packet key: (IPv4Address('17.253.15.203'), IPv4Address('10.8.152.240'), 443, 51506, 1958739276)
# Duplicate found in packet counts 105730 and 106782, packet key: (IPv4Address('17.253.15.203'), IPv4Address('10.8.152.240'), 443, 51506, 1958740650)
# Duplicate found in packet counts 105731 and 106783, packet key: (IPv4Address('17.253.15.203'), IPv4Address('10.8.152.240'), 443, 51506, 1958742024)
# Duplicate found in packet counts 105732 and 106784, packet key: (IPv4Address('17.253.15.203'), IPv4Address('10.8.152.240'), 443, 51506, 1958743398)
# Duplicate found in packet counts 105733 and 106785, packet key: (IPv4Address('17.253.15.203'), IPv4Address('10.8.152.240'), 443, 51506, 1958744772)
# Duplicate found in packet counts 105734 and 106786, packet key: (IPv4Address('17.253.15.203'), IPv4Address('10.8.152.240'), 443, 51506, 1958746146)
# Duplicate found in packet counts 105735 and 106787, packet key: (IPv4Address('17.253.15.203'), IPv4Address('10.8.152.240'), 443, 51506, 1958747520)
# Duplicate found in packet counts 105736 and 106788, packet key: (IPv4Address('17.253.15.203'), IPv4Address('10.8.152.240'), 443, 51506, 1958748894)


print("Creating select packets list...")
select_packets_list = []
for packet_data in packets_list:#[105000:107000]:
    select_packets_list.append(packet_data)
print("Created select packets list; length: {}".format(len(select_packets_list)))

print("Dumping to test file...")
with open(one_conn_test_pickle_path, "wb") as write_fp:
    pickle.dump(select_packets_list, write_fp)
print("Dumped to test file")