// Flow table stage 0 resources

Hash<ft_addr_wsz>(HashAlgorithm_t.CRC16,
        CRCPolynomial<ft_addr_wsz>(CRC_POLY_0,false,false,false,0,0)) flow_table_stage_0_hash;
action act_compute_index_flow_table_stage_0() {
    ig_md.ft_stage_0_index = (ft_addr_wsz)flow_table_stage_0_hash.get({
        seed_stage_0,
        ig_md.curr_flow_rec.flow_sign
    });
    // Test case to test collision in the FT
    // ig_md.ft_stage_0_index = 0x1;
}

Register<flow_sign_t, ft_addr_wsz>(FLOW_TABLE_STAGE_SIZE) flow_table_stage_0_flow_signature;
Register<mr_edge_t,   ft_addr_wsz>(FLOW_TABLE_STAGE_SIZE) flow_table_stage_0_mr_right_edge;
Register<mr_edge_t,   ft_addr_wsz>(FLOW_TABLE_STAGE_SIZE) flow_table_stage_0_mr_left_edge;


/* FT Flow Signature Register Actions */

// (1) FT0GetFlowSigMatch:: FT Stage 0 Register Action: Check flow signature match
RegisterAction<flow_sign_t, ft_addr_wsz, bool>(flow_table_stage_0_flow_signature) get_match_ft_stage_0_flow_signature = {
    void apply(inout flow_sign_t mem_cell, out bool do_flow_signatures_match) {
        do_flow_signatures_match = false;
        if (mem_cell == ig_md.curr_flow_rec.flow_sign) {
            do_flow_signatures_match = true;
        }
    } };
action act_get_match_flow_table_stage_0_flow_signature() {
    ig_md.do_flow_signatures_match = get_match_ft_stage_0_flow_signature.execute(ig_md.ft_stage_0_index);
}

// (2) FT0SetFlowSig:: FT Stage 0 Register Action: Set flow signature
RegisterAction<flow_sign_t, ft_addr_wsz, flow_sign_t>(flow_table_stage_0_flow_signature) set_ft_stage_0_flow_signature = {
    void apply(inout flow_sign_t mem_cell, out flow_sign_t ret_val) {
        ret_val  = mem_cell;
        mem_cell = ig_md.curr_flow_rec.flow_sign;
    } };
action act_set_flow_table_stage_0_flow_signature() {
    ig_md.curr_flow_rec.flow_sign = set_ft_stage_0_flow_signature.execute(ig_md.ft_stage_0_index);
}


/* FT Flow MR Right Edge Register Actions */

// (1) FT0GetRightMR:: FT Stage 0 Register Action: Get MR right edge
RegisterAction<mr_edge_t, ft_addr_wsz, mr_edge_t>(flow_table_stage_0_mr_right_edge) get_ft_stage_0_mrr = {
    void apply(inout mr_edge_t mem_cell, out mr_edge_t ret_val) {
        ret_val  = mem_cell;
    } };
action act_get_flow_table_stage_0_mrr() {
    ig_md.curr_flow_rec.right_edge = get_ft_stage_0_mrr.execute(ig_md.ft_stage_0_index);
}
action act_get_flow_table_stage_0_mrr_ack() {
    ig_md.read_flow_rec.right_edge = get_ft_stage_0_mrr.execute(ig_md.ft_stage_0_index);
}

// (2) FT0SetRightMR:: FT Stage 0 Register Action: Set MR right edge
RegisterAction<mr_edge_t, ft_addr_wsz, mr_edge_t>(flow_table_stage_0_mr_right_edge) set_ft_stage_0_mrr = {
    void apply(inout mr_edge_t mem_cell, out mr_edge_t ret_val) {
        ret_val  = mem_cell;
        mem_cell = ig_md.curr_flow_rec.right_edge;
    } };
action act_set_flow_table_stage_0_mrr() {
    ig_md.curr_flow_rec.right_edge = set_ft_stage_0_mrr.execute(ig_md.ft_stage_0_index);
}

// (3) FT0UpdateRightMR0: FT Stage 0 Register Action: Update MR right edge for SEQ direction: Set to value if value is greater than existing
RegisterAction<mr_edge_t, ft_addr_wsz, mr_edge_t>(flow_table_stage_0_mr_right_edge) update_ft_stage_0_seq_mrr_setmax = {
    void apply(inout mr_edge_t mem_cell, out mr_edge_t ret_val) {
        ret_val = mem_cell;
        if (mem_cell < ig_md.curr_flow_rec.right_edge) {
            mem_cell = ig_md.curr_flow_rec.right_edge;
        }
    } };
action act_update_flow_table_stage_0_seq_mrr_setmax() {
    ig_md.read_flow_rec.right_edge = update_ft_stage_0_seq_mrr_setmax.execute(ig_md.ft_stage_0_index);
}


/* FT Flow MR Left Edge Register Actions */

// Attempt at debugging; not sure if it will work yet
// (0) Get or set left MR based on condition
RegisterAction<mr_edge_t, ft_addr_wsz, mr_edge_t>(flow_table_stage_0_mr_left_edge) get_ft_stage_0_mrl = {
    void apply(inout mr_edge_t mem_cell, out mr_edge_t ret_val) {
        ret_val = mem_cell;
    } };
action act_get_flow_table_stage_0_mrl() {
    ig_md.curr_flow_rec.left_edge = get_ft_stage_0_mrl.execute(ig_md.ft_stage_0_index);
}

RegisterAction<mr_edge_t, ft_addr_wsz, mr_edge_t>(flow_table_stage_0_mr_left_edge) set_ft_stage_0_mrl = {
    void apply(inout mr_edge_t mem_cell, out mr_edge_t ret_val) {
        ret_val = mem_cell;
        mem_cell = ig_md.comp_left_edge;
    } };
action act_set_flow_table_stage_0_mrl() {
    ig_md.curr_flow_rec.left_edge = set_ft_stage_0_mrl.execute(ig_md.ft_stage_0_index);
}
// action act_set_internal_flow_table_stage_0_mrl() {
//     ig_md.curr_flow_rec.left_edge = set_ft_stage_0_mrl.execute(ig_md.ft_stage_0_index);
// }
// action act_set_flow_table_stage_0_mrl() {
//     ig_md.ft_left_edge_get = 0;
//     act_set_internal_flow_table_stage_0_mrl();
// }
// action act_get_flow_table_stage_0_mrl() {
//     ig_md.ft_left_edge_get = 1;
//     act_set_internal_flow_table_stage_0_mrl();
// }

action act_update_ft_stage_0_mrl_setnull() {
    ig_md.comp_left_edge = NULL;
    act_set_flow_table_stage_0_mrl();
}

/* Commenting out for now to debug
// (1) FT0GetLeftMR:: FT Stage 0 Register Action: Get MR left edge
RegisterAction<mr_edge_t, ft_addr_wsz, mr_edge_t>(flow_table_stage_0_mr_left_edge) get_ft_stage_0_mrl = {
    void apply(inout mr_edge_t mem_cell, out mr_edge_t ret_val) {
        ret_val = mem_cell;
    } };
action act_get_flow_table_stage_0_mrl() {
    ig_md.curr_flow_rec.left_edge = get_ft_stage_0_mrl.execute(ig_md.ft_stage_0_index);
}

// (2) FT0SetLeftMR:: FT Stage 0 Register Action: Set MR left edge
RegisterAction<mr_edge_t, ft_addr_wsz, mr_edge_t>(flow_table_stage_0_mr_left_edge) set_ft_stage_0_mrl = {
    void apply(inout mr_edge_t mem_cell, out mr_edge_t ret_val) {
        ret_val = mem_cell;
        mem_cell = ig_md.comp_left_edge;
    } };
action act_set_flow_table_stage_0_mrl() {
    ig_md.curr_flow_rec.left_edge = set_ft_stage_0_mrl.execute(ig_md.ft_stage_0_index);
}
action act_update_ft_stage_0_mrl_setnull() {
    ig_md.comp_left_edge = NULL;
    ig_md.curr_flow_rec.left_edge = set_ft_stage_0_mrl.execute(ig_md.ft_stage_0_index);
}
action act_set_flow_table_stage_0_mrl_fte_pin() {
    ig_md.curr_flow_rec.left_edge = set_ft_stage_0_mrl.execute(ig_md.ft_stage_0_index);
}
*/

// (3) FT0UpdateLeftMR0: FT Stage 0 Register Action: Update MR left edge for SEQ direction: Set to value if existing is NULL
// @stage(9)
RegisterAction<mr_edge_t, ft_addr_wsz, mr_edge_t>(flow_table_stage_0_mr_left_edge) update_ft_stage_0_seq_mrl_setinifnull = {
    void apply(inout mr_edge_t mem_cell, out mr_edge_t ret_val) {
        ret_val = mem_cell;
        if (mem_cell == NULL) {
            mem_cell = ig_md.comp_left_edge;
        }
    } };
// @stage(9)
action act_update_flow_table_stage_0_seq_mrl_setinifnull() {
    update_ft_stage_0_seq_mrl_setinifnull.execute(ig_md.ft_stage_0_index);
}

// (4) FT0UpdateLeftMR1: FT Stage 0 Register Action: Update MR left edge for ACK direction: Set to value if it is larger, else set to NULL
// @stage(9)
RegisterAction<mr_edge_t, ft_addr_wsz, mr_edge_t>(flow_table_stage_0_mr_left_edge) update_ft_stage_0_ack_mrl_setnewifmaxornull = {
    void apply(inout mr_edge_t mem_cell, out mr_edge_t ret_val) {
        ret_val = mem_cell;
        // bit<32> sub_result = ig_md.comp_left_edge - mem_cell;
        // if ( sub_result > 0 ) {
        if ( ig_md.curr_flow_rec.right_edge > mem_cell ) {
            mem_cell = ig_md.curr_flow_rec.right_edge;
        } else if ( ig_md.curr_flow_rec.right_edge == mem_cell ) {
            mem_cell = NULL;
        }
    } };
// @stage(9)
action act_update_flow_table_stage_0_ack_mrl_setnewifmaxornullifequal() {
    ig_md.read_flow_rec.left_edge = update_ft_stage_0_ack_mrl_setnewifmaxornull.execute(ig_md.ft_stage_0_index);
}

// Table for FT flow signature action
table tab_execute_ft_flow_sign_action {
    const size = 4;
    key = {
        ig_md.packet_status: exact;
    }
    actions = { act_get_match_flow_table_stage_0_flow_signature; act_set_flow_table_stage_0_flow_signature; no_action; }
    const default_action = no_action;
    const entries = {
        ( 50 ) : act_set_flow_table_stage_0_flow_signature();
        ( 60 ) : act_get_match_flow_table_stage_0_flow_signature();
        ( 70 ) : act_get_match_flow_table_stage_0_flow_signature();
        ( 80 ) : act_get_match_flow_table_stage_0_flow_signature();
    }
}

// Table for FT right edge action
table tab_execute_ft_right_edge_action {
    const size = 5;
    key = {
        ig_md.packet_status: exact;
    }
    actions = { act_get_flow_table_stage_0_mrr; act_set_flow_table_stage_0_mrr; act_update_flow_table_stage_0_seq_mrr_setmax;
                act_get_flow_table_stage_0_mrr_ack; no_action; }
    const default_action = no_action;
    const entries = {
        ( 50 ) : act_set_flow_table_stage_0_mrr();
        ( 61 ) : act_get_flow_table_stage_0_mrr();
        ( 71 ) : act_set_flow_table_stage_0_mrr();
        ( 72 ) : act_update_flow_table_stage_0_seq_mrr_setmax();
        ( 81 ) : act_get_flow_table_stage_0_mrr_ack();
    }
}

// Table for FT left edge action
table tab_execute_ft_left_edge_action {
    const size = 9;
    key = {
        ig_md.packet_status: exact;
    }
    actions = { act_get_flow_table_stage_0_mrl; act_set_flow_table_stage_0_mrl; act_update_ft_stage_0_mrl_setnull;
                act_update_flow_table_stage_0_seq_mrl_setinifnull; act_update_flow_table_stage_0_ack_mrl_setnewifmaxornullifequal; no_action; }
    const default_action = no_action;
    const entries = {
        ( 50 ) : act_set_flow_table_stage_0_mrl();
        ( 61 ) : act_get_flow_table_stage_0_mrl();
        ( 73 ) : act_set_flow_table_stage_0_mrl();
        ( 74 ) : act_update_ft_stage_0_mrl_setnull();
        ( 75 ) : act_update_flow_table_stage_0_seq_mrl_setinifnull();
        ( 76 ) : act_update_ft_stage_0_mrl_setnull();
        ( 77 ) : act_set_flow_table_stage_0_mrl();
        ( 83 ) : act_update_ft_stage_0_mrl_setnull();
        ( 84 ) : act_update_flow_table_stage_0_ack_mrl_setnewifmaxornullifequal();
    }
}