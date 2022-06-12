// Packet table stage 0 resources

Hash<pt_addr_wsz>(HashAlgorithm_t.CRC16,
        CRCPolynomial<pt_addr_wsz>(CRC_POLY_1,false,false,false,0,0)) packet_table_stage_0_hash;
action act_compute_index_packet_table_stage_0() {
    eg_md.pt_stage_0_index = (pt_addr_wsz)packet_table_stage_0_hash.get({
        seed_stage_0,
        eg_md.curr_flow_rec.flow_sign,
        eg_md.curr_packet_rec.eack
    });
    // Test case to test collision in the PT
    // eg_md.pt_stage_0_index = 0x1;
}

Register<flow_sign_t, pt_addr_wsz>(PACKET_TABLE_STAGE_SIZE) packet_table_stage_0_packet_signature;
Register<eack_t,      pt_addr_wsz>(PACKET_TABLE_STAGE_SIZE) packet_table_stage_0_eack;
Register<timestamp_t, pt_addr_wsz>(PACKET_TABLE_STAGE_SIZE) packet_table_stage_0_timestamp;


/* PT Packet Signature Register Actions */

// (1) PT0GetPacketSig:: PT Stage 0 Register Action: Check packet signature match
RegisterAction<flow_sign_t, pt_addr_wsz, bool>(packet_table_stage_0_packet_signature) get_match_pt_stage_0_packet_signature = {
    void apply(inout flow_sign_t mem_cell, out bool do_packet_signatures_match) {
        do_packet_signatures_match = false;
        if (mem_cell == eg_md.curr_flow_rec.flow_sign) {
            do_packet_signatures_match = true;
        }
    } };
action act_get_match_packet_table_stage_0_packet_signature() {
    eg_md.do_packet_signatures_match = get_match_pt_stage_0_packet_signature.execute(eg_md.pt_stage_0_index);
}

// (2) PT0SetPacketSig:: PT Stage 0 Register Action: Set packet signature
RegisterAction<flow_sign_t, pt_addr_wsz,
    flow_sign_t>(packet_table_stage_0_packet_signature) set_pt_stage_0_packet_signature = {
    void apply(inout flow_sign_t mem_cell, out flow_sign_t ret_val) {
        ret_val  = mem_cell;
        mem_cell = eg_md.curr_flow_rec.flow_sign;
    } };
action act_set_packet_table_stage_0_packet_signature() {
    eg_md.curr_flow_rec.flow_sign = set_pt_stage_0_packet_signature.execute(eg_md.pt_stage_0_index);
}


/* PT Packet eACK Register Actions */

// (1) PT0SeteACK:: PT Stage 0 Register Actions: Set packet eACK
RegisterAction<eack_t, pt_addr_wsz, eack_t>(packet_table_stage_0_eack) set_pt_stage_0_eack = {
    void apply(inout eack_t mem_cell, out eack_t ret_val) {
        ret_val  = mem_cell;
        mem_cell = eg_md.curr_packet_rec.eack;
    } };
action act_set_packet_table_stage_0_eack() {
    eg_md.curr_packet_rec.eack = set_pt_stage_0_eack.execute(eg_md.pt_stage_0_index);
}

// (2) PT0GetPacketeACK:: PT Stage 0 Register Action: Check packet eACK match
RegisterAction<eack_t, pt_addr_wsz, bool>(packet_table_stage_0_eack) get_match_pt_stage_0_eack = {
    void apply(inout eack_t mem_cell, out bool do_packet_eacks_match) {
        do_packet_eacks_match = false;
        if (mem_cell == eg_md.curr_packet_rec.eack) {
            do_packet_eacks_match = true;
        }
    } };
action act_get_match_packet_table_stage_0_eack() {
    eg_md.do_packet_eacks_match = get_match_pt_stage_0_eack.execute(eg_md.pt_stage_0_index);
}


/* PT Packet Timestamp Register Actions */

// (1) PT0SetTimestamp:: PT Stage 0 Register Actions: Set packet timestamp
RegisterAction<timestamp_t, pt_addr_wsz, timestamp_t>(packet_table_stage_0_timestamp) set_pt_stage_0_timestamp = {
    void apply(inout timestamp_t mem_cell, out timestamp_t ret_val) {
        ret_val  = mem_cell;
        mem_cell = eg_md.curr_packet_rec.timestamp;
    } };
action act_set_packet_table_stage_0_timestamp() {
    eg_md.curr_packet_rec.timestamp = set_pt_stage_0_timestamp.execute(eg_md.pt_stage_0_index);
}

// (2) PT0SampleRTT:: PT Stage 0 Register Actions: Sample RTT
RegisterAction<timestamp_t, pt_addr_wsz, timestamp_t>(packet_table_stage_0_timestamp) delete_pt_stage_0_timestamp_sample_rtt = {
    void apply(inout timestamp_t mem_cell, out timestamp_t ret_val) {
        ret_val  = mem_cell;
        mem_cell = NULL;
    } };
action act_delete_packet_table_stage_0_timestamp_sample_rtt() {
    eg_md.curr_packet_rec.timestamp = delete_pt_stage_0_timestamp_sample_rtt.execute(eg_md.pt_stage_0_index);
}


// Table for PT packet signature action
table tab_execute_pt_packet_sign_action {
    const size = 4;
    key = {
        eg_md.packet_status: exact;
    }
    actions = { act_get_match_packet_table_stage_0_packet_signature; act_set_packet_table_stage_0_packet_signature; no_action; }
    const default_action = no_action;
    const entries = {
        ( 52 ) : act_set_packet_table_stage_0_packet_signature();
        ( 62 ) : act_set_packet_table_stage_0_packet_signature();
        ( 79 ) : act_set_packet_table_stage_0_packet_signature();
        ( 85 ) : act_get_match_packet_table_stage_0_packet_signature();
    }
}

// Table for PT eACK action
table tab_execute_pt_packet_eack_action {
    const size = 4;
    key = {
        eg_md.packet_status: exact;
    }
    actions = { act_get_match_packet_table_stage_0_eack; act_set_packet_table_stage_0_eack; no_action; }
    const default_action = no_action;
    const entries = {
        ( 52 ) : act_set_packet_table_stage_0_eack();
        ( 62 ) : act_set_packet_table_stage_0_eack();
        ( 79 ) : act_set_packet_table_stage_0_eack();
        ( 85 ) : act_get_match_packet_table_stage_0_eack();
    }
}

// Table for PT timestamp action
table tab_execute_pt_packet_timestamp_action {
    const size = 4;
    key = {
        eg_md.packet_status: exact;
    }
    actions = { act_delete_packet_table_stage_0_timestamp_sample_rtt; act_set_packet_table_stage_0_timestamp; no_action; }
    const default_action = no_action;
    const entries = {
        ( 52 ) : act_set_packet_table_stage_0_timestamp();
        ( 62 ) : act_set_packet_table_stage_0_timestamp();
        ( 79 ) : act_set_packet_table_stage_0_timestamp();
        ( 86 ) : act_delete_packet_table_stage_0_timestamp_sample_rtt();
    }
}
