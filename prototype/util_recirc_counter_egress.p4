Register<bit<16>, bit<1>>(1) counter_seq_packets;
Register<bit<16>, bit<1>>(1) counter_recirc_packets;
Register<bit<8>,  bit<1>>(1) counter_ack_packets;


// Counter: SEQ packets
RegisterAction<bit<16>, bit<1>, bit<16>>(counter_seq_packets) counter_seq_packets_get_and_clear = {
    void apply(inout bit<16> mem_cell, out bit<16> ret_val) {
        ret_val = mem_cell;
        mem_cell = 0;
    } };
RegisterAction<bit<16>, bit<1>, bool>(counter_seq_packets) counter_seq_packets_increment = {
    void apply(inout bit<16> mem_cell, out bool ret_val) {
        ret_val = true;
        mem_cell = mem_cell + 1;
    } };
action act_counter_seq_packets_increment()     { counter_seq_packets_increment.execute(0); }
action act_counter_seq_packets_get_and_clear() { eg_md.counter_seq_pkts = counter_seq_packets_get_and_clear.execute(0); }


// Counter: Recirculated packets
RegisterAction<bit<16>, bit<1>, bit<16>>(counter_recirc_packets) counter_recirc_packets_get_and_clear = {
    void apply(inout bit<16> mem_cell, out bit<16> ret_val) {
        ret_val = mem_cell;
        mem_cell = 0;
    } };
RegisterAction<bit<16>, bit<1>, bool>(counter_recirc_packets) counter_recirc_packets_increment = {
    void apply(inout bit<16> mem_cell, out bool ret_val) {
        ret_val = true;
        mem_cell = mem_cell + 1;
    } };
action act_counter_recirc_packets_increment()     { counter_recirc_packets_increment.execute(0); }
action act_counter_recirc_packets_get_and_clear() { eg_md.counter_recirc_pkts = counter_recirc_packets_get_and_clear.execute(0); }


// Counter: ACK packets
RegisterAction<bit<8>, bit<1>, bit<8>>(counter_ack_packets) counter_ack_packets_get_and_clear = {
    void apply(inout bit<8> mem_cell, out bit<8> ret_val) {
        ret_val = mem_cell;
        mem_cell = 0;
    } };
RegisterAction<bit<8>, bit<1>, bool>(counter_ack_packets) counter_ack_packets_increment = {
    void apply(inout bit<8> mem_cell, out bool ret_val) {
        ret_val = true;
        mem_cell = mem_cell + 1;
    } };
action act_counter_ack_packets_increment()     { counter_ack_packets_increment.execute(0); }
action act_counter_ack_packets_get_and_clear() { eg_md.counter_ack_pkts = counter_ack_packets_get_and_clear.execute(0); }


// SEQ packet counter decision
table tab_process_counter_seq_packets {
    const size = 2;
    key = {
        eg_md.packet_status: ternary;
        eg_md.packet_type: ternary;
    }
    actions = { act_counter_seq_packets_increment; act_counter_seq_packets_get_and_clear; no_action; }
    const default_action = no_action();
    const entries = {
        ( 86, _ )                : act_counter_seq_packets_get_and_clear();
        ( _,  PKT_TYPE_TCP_SEQ ) : act_counter_seq_packets_increment();
    }
}


// Recirculated packet counter decision
table tab_process_counter_action_recirc_packets {
    const size = 2;
    key = {
        eg_md.packet_status: ternary;
        eg_md.p4rtt_recirc_valid: exact;
    }
    actions = { act_counter_recirc_packets_increment; act_counter_recirc_packets_get_and_clear; no_action; }
    const default_action = no_action();
    const entries = {
        ( 86, false ) : act_counter_recirc_packets_get_and_clear();
        ( _,  true  ) : act_counter_recirc_packets_increment();
    }
}


// ACK packet counter decision
table tab_process_counter_ack_packets {
    const size = 3;
    key = {
        eg_md.packet_status: ternary;
        eg_md.packet_type: ternary;
    }
    actions = { act_counter_ack_packets_increment; act_counter_ack_packets_get_and_clear; no_action; }
    const default_action = no_action();
    const entries = {
        ( 86, _ )                : act_counter_ack_packets_get_and_clear();
        ( _,  PKT_TYPE_TCP_BTH ) : act_counter_ack_packets_increment();
        ( _,  PKT_TYPE_TCP_ACK ) : act_counter_ack_packets_increment();
    }
}