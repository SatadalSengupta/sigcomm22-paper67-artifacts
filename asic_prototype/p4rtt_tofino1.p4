#include <core.p4>
#if __TARGET_TOFINO__ == 2
#include <t2na.p4>
#else
#include <tna.p4>
#endif

#if __TARGET_TOFINO__ != 1
#define RECIRCULATION_PORT 6
#define REPORT_RTT_PORT 16
#else
// #define RECIRCULATION_PORT 68
// #define REPORT_RTT_PORT 8
#define RECIRCULATION_PORT 196
#define REPORT_RTT_PORT 128
#endif

#define TCP_PAYLOAD_SIZE_TAB_FULL 16384
#define TCP_PAYLOAD_SIZE_TAB_SHORT 16

#define NULL 0

#define FLOW_TABLE_SIGN_WSZ 32
#define PACKET_TABLE_SIGN_WSZ 32

#define FLOW_TABLE_STAGE_SIZE 65536
#define PACKET_TABLE_STAGE_SIZE 65536
// Log base 2 of the previous values
#define FLOW_TABLE_ADDR_WSZ 16
#define PACKET_TABLE_ADDR_WSZ 16

#define CRC_POLY_0 0x8005
#define CRC_POLY_1 0x0589
#define CRC_POLY_2 0x3D65
#define CRC_POLY_3 32w0x1021
#define CRC_POLY_4 0x8BB7
#define CRC_POLY_5 0xA097

// Typedefs
typedef bit<FLOW_TABLE_ADDR_WSZ>   ft_addr_wsz;
typedef bit<PACKET_TABLE_ADDR_WSZ> pt_addr_wsz;

typedef bit<48>  mac_addr_t;
typedef bit<32>  ipv4_addr_t;
// typedef bit<128> ipv6_addr_t;

typedef bit<16> ether_type_t;
const ether_type_t ETHERTYPE_IPV4 = 16w0x0800;
const ether_type_t ETHERTYPE_IPV6 = 16w0x86dd;
const ether_type_t ETHERTYPE_PRTT = 16w0x9000; // Repurposing "LOOP" ethertype 9000 for P4RTT recirculation

typedef bit<8> ip_protocol_t;
const ip_protocol_t IP_PROTOCOL_ICMP = 1;
const ip_protocol_t IP_PROTOCOL_TCP  = 6;
const ip_protocol_t IP_PROTOCOL_UDP  = 17;

typedef bit<8>   packet_type_t;
typedef bit<16>  tcp_port_t;
typedef bit<32>  mr_edge_t;
typedef bit<32>  eack_t;
typedef bit<32>  timestamp_t;
typedef bit<32>  flow_sign_t;
typedef bit<8>   recirc_count_t;
typedef bit<16>  table_index_t;

const recirc_count_t FLOW_TABLE_MAX_RECIRC   = 3;
const recirc_count_t PACKET_TABLE_MAX_RECIRC = 3;

// Incoming packet types
const packet_type_t PKT_TYPE_TCP_PIN = 1; // TCP Packet In
const packet_type_t PKT_TYPE_FTS_PIN = 2; // TCP Copy Packet In (SEQ direction because ACK direction already processed)
const packet_type_t PKT_TYPE_FTI_PIN = 3; // FT Insert Packet In (comes in with precomputed left and right edges)
const packet_type_t PKT_TYPE_FTE_PIN = 4; // FT Evicted In
const packet_type_t PKT_TYPE_FTE_PRE = 5; // PKT_TYPE_FTE_PIN with pending PT processing
const packet_type_t PKT_TYPE_PTE_PIN = 6; // PT Evicted In
const packet_type_t PKT_TYPE_RTT_OUT = 7; // RTT Report Out

// TCP packet direction match types (before validity check)
const packet_type_t SQPM_SEQ = 16; // TCP SEQ Priority Table Match: SEQ Direction
const packet_type_t SQPM_ACK = 17; // TCP SEQ Priority Table Match: ACK Direction
const packet_type_t AKPM_SEQ = 18; // TCP ACK Priority Table Match: SEQ Direction
const packet_type_t AKPM_ACK = 19; // TCP ACK Priority Table Match: ACK Direction

// Valid TCP packet direction match types
const packet_type_t PKT_TYPE_TCP_BTH = 32;  // TCP Matches Both Directions
const packet_type_t PKT_TYPE_TCP_SEQ = 33;  // TCP Matches Only SEQ Direction
const packet_type_t PKT_TYPE_TCP_ACK = 34;  // TCP Matches Only ACK Direction

const bit<4> seed_stage_0 = 7;
const bit<4> seed_stage_1 = 3;
// const bit<4> seed_stage_2 = 11;

const bit<4> seed_flow_signature   = 5;
const bit<4> seed_packet_signature = 11;

const packet_type_t STATUS_MR_NULL      = 1;
const packet_type_t STATUS_MR_PROCEED   = 2;
const packet_type_t STATUS_MR_COLLAPSED = 3;

// Headers

header ethernet_h {
    mac_addr_t dst_addr;
    mac_addr_t src_addr;
    bit<16> ether_type;
}

header ipv4_h {
    // 20 bytes
    bit<4>  version;        // 1 byte
    bit<4>  ihl;
    bit<8>  diffserv;       // 1 byte
    bit<16> total_len;      // 2 bytes
    bit<16> identification; // 2 bytes
    bit<3>  flags;          // 2 bytes
    bit<13> frag_offset;
    bit<8>  ttl;            // 1 byte
    bit<8>  protocol;       // 1 byte
    bit<16> hdr_checksum;   // 2 bytes
    ipv4_addr_t src_addr;   // 4 bytes
    ipv4_addr_t dst_addr;   // 4 bytes
}

header tcp_h {
    // 20 bytes
    bit<16> src_port;       // 2 bytes
    bit<16> dst_port;       // 2 bytes
    bit<32> seq_no;         // 4 bytes
    bit<32> ack_no;         // 4 bytes
    bit<4>  data_offset;    // 2 bytes
    bit<6>  res;
    bit<1>  urg;
    bit<1>  ack;
    bit<1>  psh;
    bit<1>  rst;
    bit<1>  syn;
    bit<1>  fin;
    bit<16> window;         // 2 bytes
    bit<16> checksum;       // 2 bytes
    bit<16> urgent_ptr;     // 2 bytes
}

// Key + Value types
struct flow_record_keyval_t {
    flow_sign_t flow_sign;
    mr_edge_t   right_edge;
    mr_edge_t   left_edge;
}
struct packet_record_keyval_t {
    eack_t        eack;
    timestamp_t   timestamp;
}

// Key types
struct flow_record_key_t {
    flow_sign_t flow_sign;
}
struct packet_record_key_t {
    eack_t eack;
}

// Value type
struct flow_record_val_t {
    mr_edge_t   right_edge;
    mr_edge_t   left_edge;
}

header p4rtt_recirc_h {
    
    // Equal (or lesser) to the IPv4 + TCP header size since we're modifying them
    // 32 bytes without table_index_t
    packet_type_t          recirc_type;          // 1 byte
    packet_type_t          first_packet_type;    // 1 byte
    flow_record_key_t      first_flow_rec;       // 4 bytes
    packet_record_key_t    first_packet_rec;     // 4 bytes
    flow_record_keyval_t   curr_flow_rec;        // 4 bytes * 3 = 12 bytes
    packet_record_keyval_t curr_packet_rec;      // 4 bytes * 2 = 8 bytes
    recirc_count_t         recirc_count_flow;    // 1 byte
    recirc_count_t         recirc_count_packet;  // 1 byte
    // table_index_t          first_packet_rec_index; // 2 bytes
}

header rtt_report_h {   // Modified UDP packet

    // Equal to the TCP header size since we're modifying it
    // 20 bytes
    bit<16>     src_port;       // 2 bytes
    bit<16>     dst_port;       // 2 bytes
    bit<16>     total_length;   // 2 bytes
    bit<16>     checksum;       // 2 bytes
    eack_t      ack_no;         // 4 bytes
    timestamp_t pt_tstamp;      // 4 bytes
    timestamp_t rtt;            // 4 bytes
}

struct header_t {
    ethernet_h ethernet;
    p4rtt_recirc_h p4rtt_recirc;
    ipv4_h ipv4;
    tcp_h tcp;
    rtt_report_h rtt_report;
}

// Metadata

@flexible
header bridged_md_h {

    bit<32> ingress_tstamp;
    
    packet_type_t packet_type;
    packet_type_t packet_status;
    packet_type_t ft_update_status;
    
    flow_record_keyval_t curr_flow_rec;

    bit<32> sub_result_flow_signatures;
}

struct ig_metadata_t {

    bit<32> ingress_tstamp;

    packet_type_t seq_match_packet_type;
    packet_type_t ack_match_packet_type;

    // bit<32> tot_hdr_len;
    // bit<32> ip_pkt_len;
    bit<32> payload_size;

    packet_type_t packet_type;
    packet_type_t ft_update_status;
    packet_type_t packet_status;

    flow_record_keyval_t curr_flow_rec;
    flow_record_val_t    read_flow_rec;

    mr_edge_t           comp_left_edge;

    bool do_flow_signatures_match;

    ft_addr_wsz ft_stage_0_index;

    bit<32> sub_result_mr_comparison_crcl;
    bit<32> sub_result_mr_comparison_crrr;
    bit<32> sub_result_mr_comparison_clrr;
    bit<32> sub_result_mr_comparison_crrl;
    bit<32> sub_result_flow_signatures;

    bridged_md_h bridged_md;
}

// Ingress Parsers

parser TofinoIngressParser(
        packet_in pkt,
        out ingress_intrinsic_metadata_t ig_intr_md) {
    
    state start {
        pkt.extract(ig_intr_md);
        transition select(ig_intr_md.resubmit_flag) {
            1: parse_resubmit;
            0: parse_port_metadata;
        }
    }

    state parse_resubmit {
        // pkt.advance(128); // tofino2 resubmit metadata size
        // transition accept;
        transition reject;
    }
    
    state parse_port_metadata {
        pkt.advance(PORT_METADATA_SIZE);
        transition accept;
    }
}

parser SwitchIngressParser(
        packet_in pkt,
        out header_t hdr,
        out ig_metadata_t ig_md,
        out ingress_intrinsic_metadata_t ig_intr_md) {

    TofinoIngressParser() tofino_parser;
    
    state start {

        hdr.rtt_report.setInvalid();

        ig_md.ingress_tstamp = ig_intr_md.ingress_mac_tstamp[31:0]; // Current
        // ig_md.ingress_tstamp = ig_intr_md.ingress_mac_tstamp[47:16]; // Overflow (not used)

        ig_md.seq_match_packet_type = NULL;
        ig_md.ack_match_packet_type = NULL;

        ig_md.payload_size = NULL;

        ig_md.packet_type      = NULL;
        ig_md.ft_update_status = STATUS_MR_NULL;
        ig_md.packet_status    = NULL;

        ig_md.curr_flow_rec.flow_sign  = NULL;
        ig_md.curr_flow_rec.right_edge = NULL;
        ig_md.curr_flow_rec.left_edge  = NULL;

        ig_md.read_flow_rec.right_edge = NULL;
        ig_md.read_flow_rec.left_edge  = NULL;

        ig_md.comp_left_edge   = NULL;

        ig_md.do_flow_signatures_match = false;

        ig_md.ft_stage_0_index = NULL;

        ig_md.sub_result_mr_comparison_crcl = 1;
        ig_md.sub_result_mr_comparison_crrr = 1;
        ig_md.sub_result_mr_comparison_clrr = 1;
        ig_md.sub_result_mr_comparison_crrl = 1;
        ig_md.sub_result_flow_signatures    = 1;

        tofino_parser.apply(pkt, ig_intr_md);
        transition parse_ethernet;
    }

    state parse_ethernet {
        pkt.extract(hdr.ethernet);
        
        transition select(hdr.ethernet.ether_type) {
            ETHERTYPE_IPV4: parse_ipv4;
            ETHERTYPE_PRTT: parse_p4rtt_recirc;
            default:        reject;
        }
    }

    state parse_p4rtt_recirc {
        pkt.extract(hdr.p4rtt_recirc);
        transition accept;
    }

    state parse_ipv4 {
        pkt.extract(hdr.ipv4);

        transition select(hdr.ipv4.protocol) {
            IP_PROTOCOL_TCP: parse_tcp;
            IP_PROTOCOL_UDP: parse_rtt;
            default:         reject;
        }
    }

    state parse_tcp {
        pkt.extract(hdr.tcp);
        transition accept;
    }

    state parse_rtt {
        pkt.extract(hdr.rtt_report);
        transition accept;
    }

}

// Ingress Processing

control SwitchIngress(
        inout header_t hdr,
        inout ig_metadata_t ig_md,
        in ingress_intrinsic_metadata_t ig_intr_md,
        in ingress_intrinsic_metadata_from_parser_t ig_prsr_md,
        inout ingress_intrinsic_metadata_for_deparser_t ig_dprsr_md,
        inout ingress_intrinsic_metadata_for_tm_t ig_tm_md) {

    action no_action() { }
    // action drop_packet() { ig_dprsr_md.drop_ctl = 0x1; exit; }
    action set_packet_type(packet_type_t pkt_type) { ig_md.packet_type = pkt_type; }
    action set_seq_match_packet_type(packet_type_t pkt_type) { ig_md.seq_match_packet_type = pkt_type; }
    action set_ack_match_packet_type(packet_type_t pkt_type) { ig_md.ack_match_packet_type = pkt_type; }

    table tab_determine_traffic_direction_priority_seq {
        const size = 256;
        key = {
            hdr.ipv4.src_addr: ternary;
            hdr.ipv4.dst_addr: ternary;
            hdr.tcp.src_port:  ternary;
            hdr.tcp.dst_port:  ternary;
        }
        actions = { set_seq_match_packet_type; no_action; }
        const entries = {
            #include "entries_determine_traffic_direction_seq.p4inc"
        }
        const default_action = no_action();
    }

    // table tab_determine_traffic_direction_priority_ack {
    //     const size = 256;
    //     key = {
    //         hdr.ipv4.src_addr: ternary;
    //         hdr.ipv4.dst_addr: ternary;
    //         hdr.tcp.src_port:  ternary;
    //         hdr.tcp.dst_port:  ternary;
    //     }
    //     actions = { set_ack_match_packet_type; no_action; }
    //     const entries = {
    //         #include "entries_determine_traffic_direction_ack.p4inc"
    //     }
    //     const default_action = no_action();
    // }

    // TCP payload length computation
    // action act_compute_total_header_len(bit<32> tot_hdr_len) { ig_md.tot_hdr_len = tot_hdr_len; }
    // action act_load_ipv4_total_len() { ig_md.ip_pkt_len = 16w0 ++ hdr.ipv4.total_len; }
    // action act_compute_packet_len()  { ig_md.payload_size = ig_md.ip_pkt_len - ig_md.tot_hdr_len; }
    action act_lookup_tcp_payload_size(bit<32> payload_size) { ig_md.payload_size = payload_size; }

    // Table to directly feed total TCP payload size instead of computing it
    table tab_determine_tcp_payload_size {
        const size = TCP_PAYLOAD_SIZE_TAB_FULL;
        // const size = TCP_PAYLOAD_SIZE_TAB_SHORT;
        key = {
            hdr.ipv4.ihl: exact;
            hdr.ipv4.total_len: exact;
            hdr.tcp.data_offset: exact;
        }
        actions = { act_lookup_tcp_payload_size; no_action; }
        const default_action = no_action();
        const entries = {
            #include "entries_determine_tcp_payload_size.p4inc"
        }
    }

    table tab_determine_valid_packet_type {
        const size = 16;
        key = {
            ig_md.packet_type: ternary;
            ig_md.seq_match_packet_type: ternary;
            ig_md.ack_match_packet_type: ternary;
            hdr.tcp.fin: ternary;
            hdr.tcp.syn: ternary;
            hdr.tcp.rst: ternary;
            hdr.tcp.ack: ternary;
            ig_md.payload_size: ternary;
        }
        actions = { set_packet_type; no_action; }
        const entries = {
            ( _, _, _, 1, _, _, _, _ )                                 : no_action(); // FIN set
            ( _, _, _, _, 1, _, _, _ )                                 : no_action(); // SYN set
            ( _, _, _, _, _, 1, _, _ )                                 : no_action(); // RST set
            ( PKT_TYPE_TCP_PIN, SQPM_SEQ, AKPM_ACK, 0, 0, 0, 1, 32w0 ) : set_packet_type( PKT_TYPE_TCP_ACK ); // Both directions but Pure ACK
            ( PKT_TYPE_TCP_PIN, SQPM_ACK, AKPM_SEQ, 0, 0, 0, 1, 32w0 ) : set_packet_type( PKT_TYPE_TCP_ACK ); // Both directions but Pure ACK
            ( PKT_TYPE_TCP_PIN, SQPM_SEQ, AKPM_ACK, 0, 0, 0, 1, _ )    : set_packet_type( PKT_TYPE_TCP_BTH ); // Valid for both directions
            ( PKT_TYPE_TCP_PIN, SQPM_ACK, AKPM_SEQ, 0, 0, 0, 1, _ )    : set_packet_type( PKT_TYPE_TCP_BTH ); // Valid for both directions
            ( PKT_TYPE_TCP_PIN, SQPM_SEQ, AKPM_ACK, 0, 0, 0, 0, 32w0 ) : no_action();                         // Neither direction valid
            ( PKT_TYPE_TCP_PIN, SQPM_ACK, AKPM_SEQ, 0, 0, 0, 0, 32w0 ) : no_action();                         // Neither direction valid
            ( PKT_TYPE_TCP_PIN, SQPM_SEQ, AKPM_ACK, 0, 0, 0, 0, _ )    : set_packet_type( PKT_TYPE_TCP_SEQ ); // Valid SEQ packet
            ( PKT_TYPE_TCP_PIN, SQPM_ACK, AKPM_SEQ, 0, 0, 0, 0, _ )    : set_packet_type( PKT_TYPE_TCP_SEQ ); // Valid SEQ packet
            ( PKT_TYPE_TCP_PIN, SQPM_SEQ, NULL, 0, 0, 0, _, 32w0 )     : no_action();                         // Neither direction valid
            ( PKT_TYPE_TCP_PIN, SQPM_SEQ, NULL, 0, 0, 0, _, _ )        : set_packet_type( PKT_TYPE_TCP_SEQ ); // Valid SEQ packet
            ( PKT_TYPE_TCP_PIN, SQPM_ACK, NULL, 0, 0, 0, 0, _ )        : no_action();                         // Neither direction valid
            ( PKT_TYPE_TCP_PIN, SQPM_ACK, NULL, 0, 0, 0, 1, _ )        : set_packet_type( PKT_TYPE_TCP_ACK ); // Valid ACK packet
            ( PKT_TYPE_FTS_PIN, NULL, NULL, 0, 0, 0, 1, _ )            : set_packet_type( PKT_TYPE_TCP_SEQ ); // Valid SEQ packet
        }
        const default_action = no_action();
    }

    // Recirculated Packet Extraction
    action act_extract_recirc_flow_header_into_curr_records() {
        ig_md.curr_flow_rec.flow_sign  = hdr.p4rtt_recirc.curr_flow_rec.flow_sign;
        ig_md.curr_flow_rec.right_edge = hdr.p4rtt_recirc.curr_flow_rec.right_edge;
        ig_md.curr_flow_rec.left_edge  = hdr.p4rtt_recirc.curr_flow_rec.left_edge;
        // Default computed left edge is the extracted left edge
        ig_md.comp_left_edge           = ig_md.curr_flow_rec.left_edge;
        // Only for the FTI_PIN case; duplicate required since FT record is overwritten before PT processing
        // ig_md.curr_packet_sign = hdr.p4rtt_recirc.curr_flow_rec.flow_sign;
    }
    action act_extract_recirc_packet_header_into_curr_records() {
        ig_md.curr_flow_rec.flow_sign   = hdr.p4rtt_recirc.curr_flow_rec.flow_sign;
        // act_extract_recirc_packet_headers_only_into_curr_records();
    }
    
    action subtract_for_comparison_curr_edges() {
        ig_md.sub_result_mr_comparison_crcl = ig_md.curr_flow_rec.right_edge - ig_md.curr_flow_rec.left_edge;
    }
    action subtract_for_comparison_right_edges() {
        ig_md.sub_result_mr_comparison_crrr = ig_md.curr_flow_rec.right_edge - ig_md.read_flow_rec.right_edge;
    }
    action subtract_for_comparison_curr_left_edge_with_mem_right_edge() {
        ig_md.sub_result_mr_comparison_clrr = ig_md.curr_flow_rec.left_edge - ig_md.read_flow_rec.right_edge;
    }
    action subtract_for_comparison_curr_right_edge_with_mem_left_edge() {
        ig_md.sub_result_mr_comparison_crrl = ig_md.curr_flow_rec.right_edge - ig_md.read_flow_rec.left_edge;
    }
    action subtract_for_comparison_flow_table_cycle() {
        ig_md.sub_result_flow_signatures = ig_md.curr_flow_rec.flow_sign - hdr.p4rtt_recirc.first_flow_rec.flow_sign;
    }

    /********** FLOW TABLE RESOURCES **********/

    Hash<bit<FLOW_TABLE_SIGN_WSZ>>(HashAlgorithm_t.CRC32,
            CRCPolynomial<bit<FLOW_TABLE_SIGN_WSZ>>(CRC_POLY_3,false,false,false,0,0)) hash_seq_flow_sign;
    Hash<bit<FLOW_TABLE_SIGN_WSZ>>(HashAlgorithm_t.CRC32,
            CRCPolynomial<bit<FLOW_TABLE_SIGN_WSZ>>(CRC_POLY_3,false,false,false,0,0)) hash_ack_flow_sign;
    action act_compute_seq_flow_signature() {
        ig_md.curr_flow_rec.flow_sign = hash_seq_flow_sign.get({
            seed_flow_signature,
            hdr.ipv4.src_addr,
            hdr.ipv4.dst_addr,
            hdr.tcp.src_port,
            hdr.tcp.dst_port
        });
    }
    action act_compute_ack_flow_signature() {
        ig_md.curr_flow_rec.flow_sign = hash_ack_flow_sign.get({
            seed_flow_signature,
            hdr.ipv4.dst_addr,
            hdr.ipv4.src_addr,
            hdr.tcp.dst_port,
            hdr.tcp.src_port
        });
    }

    action act_compute_seq_flow_mr_edges() {
        ig_md.curr_flow_rec.right_edge = hdr.tcp.seq_no + ig_md.payload_size;
        ig_md.curr_flow_rec.left_edge  = hdr.tcp.seq_no;
    }
    action act_compute_ack_flow_mr_edges() {
        ig_md.curr_flow_rec.right_edge = hdr.tcp.ack_no;
        ig_md.curr_flow_rec.left_edge  = hdr.tcp.ack_no; // Irrelevant
    }

    #include "util_flow_table_stage_0_ingress.p4"

    // Bridged metadata for egress processing
    action act_populate_bridged_metadata() {

        ig_md.bridged_md.ingress_tstamp = ig_md.ingress_tstamp;

        ig_md.bridged_md.packet_type      = ig_md.packet_type;
        ig_md.bridged_md.packet_status    = ig_md.packet_status;
        ig_md.bridged_md.ft_update_status = ig_md.ft_update_status;

        ig_md.bridged_md.curr_flow_rec.flow_sign  = ig_md.curr_flow_rec.flow_sign;
        ig_md.bridged_md.curr_flow_rec.right_edge = ig_md.curr_flow_rec.right_edge;
        ig_md.bridged_md.curr_flow_rec.left_edge  = ig_md.curr_flow_rec.left_edge;
        
        ig_md.bridged_md.sub_result_flow_signatures = ig_md.sub_result_flow_signatures;

        ig_md.bridged_md.setValid();
    }

    apply {

        // ig_md.ingress_tstamp = hdr.ethernet.dst_addr[31:0]; // For edited trace file to be replayed in the Tofino model
        
        if ( hdr.ethernet.isValid() && hdr.p4rtt_recirc.isValid() && !hdr.ipv4.isValid() && !hdr.tcp.isValid() ) {

            set_packet_type( hdr.p4rtt_recirc.recirc_type );

            if ( ig_md.packet_type == PKT_TYPE_FTI_PIN || ig_md.packet_type == PKT_TYPE_FTE_PIN || ig_md.packet_type == PKT_TYPE_FTE_PRE ) {

                // First Flow Record Recirculation
                act_extract_recirc_flow_header_into_curr_records();
                ig_md.packet_status = 50;
            
            } else if ( ig_md.packet_type == PKT_TYPE_PTE_PIN ) {

                // Packet Record Recirculation: Check Flow Record for Staleness, then Insert
                act_extract_recirc_packet_header_into_curr_records();
                ig_md.packet_status = 60;
            }

        } else if (hdr.ethernet.isValid() && !hdr.p4rtt_recirc.isValid() && hdr.ipv4.isValid() && hdr.tcp.isValid()) {

            if (ig_intr_md.ingress_port == RECIRCULATION_PORT) {

                // Recirculated SEQ packet handling
                set_packet_type( PKT_TYPE_FTS_PIN );

            } else {

                // Fresh TCP packet handling
                set_packet_type( PKT_TYPE_TCP_PIN );
                tab_determine_traffic_direction_priority_seq.apply();
                // tab_determine_traffic_direction_priority_ack.apply();
            }

            // tab_determine_ipv4_total_header_length.apply();
            // act_load_ipv4_total_len();
            // act_compute_packet_len();
            tab_determine_tcp_payload_size.apply();
            tab_determine_valid_packet_type.apply();

            /********** Flow Table Processing **********/

            /********** Flow Table: Search and Update **********/

            if ( ig_md.packet_type == PKT_TYPE_TCP_SEQ ) {

                act_compute_seq_flow_signature();
                act_compute_seq_flow_mr_edges();
                subtract_for_comparison_curr_edges();
                ig_md.packet_status = 70;

            } else if ( ig_md.packet_type == PKT_TYPE_TCP_ACK || ig_md.packet_type == PKT_TYPE_TCP_BTH ) {

                act_compute_ack_flow_signature();
                act_compute_ack_flow_mr_edges();
                ig_md.packet_status = 80;
            }
        }

        act_compute_index_flow_table_stage_0();
        tab_execute_ft_flow_sign_action.apply();

        // Next step for packet status (compound) 50
        if ( ig_md.packet_status == 50 && ( ig_md.packet_type == PKT_TYPE_FTE_PIN || ig_md.packet_type == PKT_TYPE_FTE_PRE ) ) {
            subtract_for_comparison_flow_table_cycle();
            // act_set_flow_table_stage_0_mrr();
        }
        
        // Next step for PKT_TYPE_PTE_PIN
        else if ( ig_md.packet_status == 60 && ig_md.do_flow_signatures_match ) {
            // act_get_flow_table_stage_0_mrr();
            ig_md.packet_status = 61;
        }

        // Next step for PKT_TYPE_TCP_SEQ
        else if ( ig_md.packet_status == 70 && ig_md.do_flow_signatures_match ) {
            // subtract_for_comparison_curr_edges();
            if ( ig_md.sub_result_mr_comparison_crcl[31:31] == 1 ) {
                // Lesser than (sign bit 1): Sequence number wraparound detected
                if (ig_md.curr_flow_rec.right_edge == NULL) {
                    ig_md.curr_flow_rec.right_edge = 1;
                }
                // act_set_flow_table_stage_0_mrr();
                ig_md.packet_status = 71;
            } else {
                // No sequence number wraparound
                // act_update_flow_table_stage_0_seq_mrr_setmax();
                ig_md.packet_status = 72;
            }
        }

        // Next step for PKT_TYPE_TCP_ACK
        else if ( ig_md.packet_status == 80 && ig_md.do_flow_signatures_match ) {
            // ACK packet doesn't change MR right edge
            // act_update_flow_table_stage_0_seq_mrr_setmax();
            ig_md.packet_status = 81;
        }

        tab_execute_ft_right_edge_action.apply();

        // // Next step for packet status (compound) 50
        // if ( ig_md.packet_status == 50 ) {
        //     // act_set_flow_table_stage_0_mrl();
        // }

        // // Next step for PKT_TYPE_PTE_PIN
        // if ( ig_md.packet_status == 61 ) {
        //     // act_get_flow_table_stage_0_mrl();
        //     ig_md.packet_status = 63;
        // }

        // Next step for PKT_TYPE_TCP_SEQ (branch 1: sequence no. wraparound)
        if ( ig_md.packet_status == 71 ) {
            ig_md.comp_left_edge = 1;
            // act_set_flow_table_stage_0_mrl();
            ig_md.packet_status = 73;
        }

        // Next step for PKT_TYPE_TCP_SEQ (branch 2: no sequence no. wraparound)
        else if ( ig_md.packet_status == 72 ) {

            subtract_for_comparison_right_edges();
            subtract_for_comparison_curr_left_edge_with_mem_right_edge(); // Conditional use

            if ( ig_md.sub_result_mr_comparison_crrr[31:31] == 1 ) {
                // Current eACK not ahead of previous eACK: Retransmission, collapse MR
                // act_update_ft_stage_0_mrl_setnull();
                ig_md.packet_status = 74;
                ig_md.ft_update_status = STATUS_MR_COLLAPSED;
            }
            
            else if ( ig_md.sub_result_mr_comparison_clrr == 0 ) {
                // Seq no. == reMR: Extension, leave leMR unchanged if not null, or set to seq no. (effectively do nothing)
                ig_md.comp_left_edge = ig_md.curr_flow_rec.left_edge;
                // act_update_flow_table_stage_0_seq_mrl_setinifnull();
                ig_md.packet_status = 75;
                ig_md.ft_update_status = STATUS_MR_PROCEED;
            }

            else if ( ig_md.sub_result_mr_comparison_clrr[31:31] == 1 ) {
                // Seq no. < reMR: Retransmission, set leMR to current eACK
                // act_update_ft_stage_0_mrl_setnull();
                ig_md.packet_status = 76;
                ig_md.ft_update_status = STATUS_MR_COLLAPSED;
            }

            else {
                // Seq no. > reMR: Hole detected, set leMR to Seq no.
                ig_md.comp_left_edge = ig_md.curr_flow_rec.left_edge;
                // act_set_flow_table_stage_0_mrl();
                ig_md.packet_status = 77;
                ig_md.ft_update_status = STATUS_MR_PROCEED;
            }
        }

        // Next step for PKT_TYPE_TCP_ACK
        else if ( ig_md.packet_status == 81 ) {

            subtract_for_comparison_right_edges();
            if ( ig_md.sub_result_mr_comparison_crrr == 0 ) { // || ig_md.sub_result_mr_comparison_crrr[31:31] == 0 ) {
                // Current ACK no. greater than or equal to read right edge: Collapse/close MR
                // act_update_ft_stage_0_mrl_setnull();
                ig_md.packet_status = 83;

            } else if ( ig_md.sub_result_mr_comparison_crrr[31:31] == 1 ) {
                // ACK no. lesser than right edge: Could be one of:
                // (1) ACK no. < left edge : Ignore
                // (2) left edge == ACK no.: Collapse MR)
                // (3) ACK no. > left edge: Proceed
                // act_update_flow_table_stage_0_ack_mrl_setnewifmaxornullifequal();
                ig_md.packet_status = 84;
            }
        }

        tab_execute_ft_left_edge_action.apply();

        subtract_for_comparison_curr_right_edge_with_mem_left_edge();
        
        // Next step for PKT_TYPE_TCP_ACK (branch 1)
        if ( ig_md.packet_status == 83 ) {
            if ( ig_md.curr_flow_rec.left_edge > NULL ) {
                ig_md.ft_update_status = STATUS_MR_PROCEED;
            } else {
                ig_md.ft_update_status = STATUS_MR_COLLAPSED;
            }
        }
        else if ( ig_md.packet_status == 84 && ig_md.read_flow_rec.left_edge > NULL ) {
            
            // if ( ig_md.sub_result_mr_comparison_crrl[31:31] == 1 && ig_md.curr_flow_rec.left_edge > NULL ) {
            //     ig_md.ft_update_status = STATUS_MR_PROCEED;
            // } else {
            //     ig_md.ft_update_status = STATUS_MR_COLLAPSED;
            // }
            if ( ig_md.sub_result_mr_comparison_crrl == 0 )  {
                ig_md.ft_update_status = STATUS_MR_COLLAPSED;
            } else if ( ig_md.sub_result_mr_comparison_crrl[31:31] == 0 ) {
                ig_md.ft_update_status = STATUS_MR_PROCEED;
            } 
        }

        // Determine egress port
        if ( ig_md.packet_type == PKT_TYPE_TCP_ACK && ( ig_md.packet_status == 83 || ig_md.packet_status == 84 ) ) {
            ig_tm_md.ucast_egress_port = REPORT_RTT_PORT;
        } else {
            ig_tm_md.ucast_egress_port = RECIRCULATION_PORT;
        }

        act_populate_bridged_metadata();
    }
}

// Ingress deparsing:

control SwitchIngressDeparser(
        packet_out pkt,
        inout header_t hdr,
        in ig_metadata_t ig_md,
        in ingress_intrinsic_metadata_for_deparser_t ig_dprsr_md) {

    apply {
        pkt.emit(ig_md.bridged_md);
        pkt.emit(hdr.ethernet);
        pkt.emit(hdr.ipv4);
        pkt.emit(hdr.p4rtt_recirc);
        pkt.emit(hdr.tcp);
        pkt.emit(hdr.rtt_report);
    }
}

// Egress metadata

struct eg_metadata_t {

    packet_type_t packet_type;
    packet_type_t packet_status;
    packet_type_t ft_update_status;

    bit<16> counter_seq_pkts;
    bit<16> counter_recirc_pkts;
    bit<8>  counter_ack_pkts;

    bit<32> ingress_tstamp;

    flow_record_keyval_t   curr_flow_rec;
    packet_record_keyval_t curr_packet_rec;

    bool do_packet_signatures_match;
    bool do_packet_eacks_match;

    bool recirculate_flow_record;
    bool recirculate_packet_record;

    bool p4rtt_recirc_valid;
    bool drop_packet;

    pt_addr_wsz pt_stage_0_index;

    bit<32> sub_result_flow_signatures;
    bit<32> sub_result_packet_signatures;
    bit<32> sub_result_packet_eacks;
    bit<32> sub_result_eack_comparison_right;
    bit<32> sub_result_eack_comparison_left;
    bit<32> sampled_rtt;

    bridged_md_h bridged_md;
}

// Egress parser

parser TofinoEgressParser(
        packet_in pkt,
        out egress_intrinsic_metadata_t eg_intr_md) {
    
    state start {
        pkt.extract(eg_intr_md);
        transition accept;
    }
}

// Blocks for egress

parser SwitchEgressParser(
        packet_in pkt,
        out header_t hdr,
        out eg_metadata_t eg_md,
        out egress_intrinsic_metadata_t eg_intr_md) {

    TofinoEgressParser() tofino_parser;
    
    state start {

        hdr.rtt_report.setInvalid();

        eg_md.packet_type      = NULL;
        eg_md.packet_status    = NULL;
        eg_md.ft_update_status = NULL;

        eg_md.counter_seq_pkts    = 0;
        eg_md.counter_recirc_pkts = 0;
        eg_md.counter_ack_pkts    = 0;

        eg_md.ingress_tstamp = NULL;

        eg_md.curr_flow_rec.flow_sign   = NULL;
        eg_md.curr_flow_rec.right_edge  = NULL;
        eg_md.curr_flow_rec.left_edge   = NULL;

        eg_md.curr_packet_rec.eack      = NULL;
        eg_md.curr_packet_rec.timestamp = NULL;

        eg_md.do_packet_signatures_match = false;
        eg_md.do_packet_eacks_match      = false;

        eg_md.recirculate_flow_record   = false;
        eg_md.recirculate_packet_record = false;

        eg_md.p4rtt_recirc_valid = false;
        eg_md.drop_packet        = true;

        eg_md.pt_stage_0_index = NULL;
        
        eg_md.sub_result_flow_signatures       = 1;
        eg_md.sub_result_packet_signatures     = 1;
        eg_md.sub_result_packet_eacks          = 1;
        eg_md.sub_result_eack_comparison_right = 1;
        eg_md.sub_result_eack_comparison_left  = 1;
        eg_md.sampled_rtt                      = 1;

        tofino_parser.apply(pkt, eg_intr_md);
        transition parse_bridged_md;
    }

    state parse_bridged_md {
        pkt.extract(eg_md.bridged_md);
        eg_md.bridged_md.setInvalid();
        transition parse_ethernet;
    }

    state parse_ethernet {
        pkt.extract(hdr.ethernet);
        
        transition select(hdr.ethernet.ether_type) {
            ETHERTYPE_IPV4: parse_ipv4;
            ETHERTYPE_PRTT: parse_p4rtt_recirc;
            default: reject;
        }
    }

    state parse_p4rtt_recirc {
        pkt.extract(hdr.p4rtt_recirc);
        transition accept;
    }

    state parse_ipv4 {
        pkt.extract(hdr.ipv4);

        transition select(hdr.ipv4.protocol) {
            IP_PROTOCOL_TCP: parse_tcp;
            IP_PROTOCOL_UDP: parse_rtt;
            default: reject;
        }
    }

    state parse_rtt {
        pkt.extract(hdr.rtt_report);
        transition accept;
    }

    state parse_tcp {
        pkt.extract(hdr.tcp);
        transition accept;
    }
}

control SwitchEgressDeparser(
        packet_out pkt,
        inout header_t hdr,
        in eg_metadata_t eg_md,
        in egress_intrinsic_metadata_for_deparser_t eg_intr_dprs_md) {

    apply {
        pkt.emit(hdr.ethernet);
        pkt.emit(hdr.ipv4);
        pkt.emit(hdr.p4rtt_recirc);
        pkt.emit(hdr.tcp);
        pkt.emit(hdr.rtt_report);
    }
}

control SwitchEgress(
        inout header_t hdr,
        inout eg_metadata_t eg_md,
        in egress_intrinsic_metadata_t eg_intr_md,
        in egress_intrinsic_metadata_from_parser_t eg_intr_md_from_prsr,
        inout egress_intrinsic_metadata_for_deparser_t eg_intr_dprs_md,
        inout egress_intrinsic_metadata_for_output_port_t eg_intr_oport_md) {
    
    action no_action() { }

    action act_set_for_recirculation() {
        hdr.ethernet.ether_type = ETHERTYPE_PRTT;
        hdr.ipv4.setInvalid();
        hdr.tcp.setInvalid();
        hdr.ethernet.setValid();
        hdr.p4rtt_recirc.setValid();
        eg_md.drop_packet = false;
    }

    // Determine flow recirculation status
    action set_flow_recirculation_status(bool flow_recirc) { eg_md.recirculate_flow_record = flow_recirc; }
    action set_flow_recirculation_as_last() {
        eg_md.recirculate_flow_record = true;
        hdr.p4rtt_recirc.recirc_count_flow = FLOW_TABLE_MAX_RECIRC - 1;
    }

    table tab_determine_flow_recirculation_status {
        const size = 5;
        key = {
            eg_md.packet_status: exact;
            hdr.p4rtt_recirc.recirc_count_flow: ternary;
            eg_md.curr_flow_rec.flow_sign: ternary;
            eg_md.curr_flow_rec.left_edge: ternary;
            eg_md.sub_result_flow_signatures: ternary;
        }
        actions = { set_flow_recirculation_status; set_flow_recirculation_as_last; no_action; }
        const default_action = no_action();
        const entries = {
            ( 50, FLOW_TABLE_MAX_RECIRC, _, _, _ ) : set_flow_recirculation_status( false );
            ( 50, _, NULL, _, _ ) : set_flow_recirculation_status( false );
            ( 50, _, _, NULL, _ ) : set_flow_recirculation_status( false ); // Collapsed MR
            ( 50, _, _, _, 0 )    : set_flow_recirculation_as_last();
            ( 50, _, _, _, _ )    : set_flow_recirculation_status( true );
        }
    }

    // Recirculated Packet Assignment
    action act_assign_curr_fields_to_recirc_curr_flow_sign_header() {
        hdr.p4rtt_recirc.curr_flow_rec.flow_sign = eg_md.curr_flow_rec.flow_sign;
    }
    action act_assign_curr_fields_to_recirc_curr_flow_header() {
        act_assign_curr_fields_to_recirc_curr_flow_sign_header();
        hdr.p4rtt_recirc.curr_flow_rec.right_edge = eg_md.curr_flow_rec.right_edge;
        hdr.p4rtt_recirc.curr_flow_rec.left_edge  = eg_md.curr_flow_rec.left_edge;
    }
    action act_assign_fresh_curr_fields_to_recirc_curr_packet_header() {
        hdr.p4rtt_recirc.curr_packet_rec.eack      = eg_md.curr_flow_rec.right_edge;
        hdr.p4rtt_recirc.curr_packet_rec.timestamp = eg_md.ingress_tstamp;
    }
    action act_assign_curr_fields_to_recirc_curr_packet_header() {
        hdr.p4rtt_recirc.curr_packet_rec.eack      = eg_md.curr_packet_rec.eack;
        hdr.p4rtt_recirc.curr_packet_rec.timestamp = eg_md.curr_packet_rec.timestamp;
    }
    action act_assign_fresh_curr_fields_to_recirc_curr_headers() {
        act_assign_curr_fields_to_recirc_curr_flow_header();
        act_assign_fresh_curr_fields_to_recirc_curr_packet_header();
    }
    action act_assign_curr_fields_to_recirc_curr_packet_only_header() {
        act_assign_curr_fields_to_recirc_curr_flow_sign_header();
        act_assign_curr_fields_to_recirc_curr_packet_header();
    }

    action act_set_initial_recirc_counts() {
        hdr.p4rtt_recirc.recirc_count_flow   = 1;
        hdr.p4rtt_recirc.recirc_count_packet = 0;
    }
    action act_increment_flow_recirc_count() {
        hdr.p4rtt_recirc.recirc_count_flow = hdr.p4rtt_recirc.recirc_count_flow + 1;
    }
    action act_increment_packet_recirc_count() {
        hdr.p4rtt_recirc.recirc_count_packet = hdr.p4rtt_recirc.recirc_count_packet + 1;
    }

    action act_extract_recirc_packet_headers_only_into_curr_records() {
        eg_md.curr_packet_rec.eack      = hdr.p4rtt_recirc.curr_packet_rec.eack;
        eg_md.curr_packet_rec.timestamp = hdr.p4rtt_recirc.curr_packet_rec.timestamp;
    }
    action act_extract_recirc_packet_header_into_curr_records_for_fti_pin() {
        // eg_md.curr_flow_rec.flow_sign   = eg_md.curr_packet_sign;
        eg_md.curr_flow_rec.flow_sign   = hdr.p4rtt_recirc.curr_flow_rec.flow_sign;
        act_extract_recirc_packet_headers_only_into_curr_records();
    }
    action act_extract_recirc_packet_header_into_curr_records_for_fte_pre() {
        eg_md.curr_flow_rec.flow_sign   = hdr.p4rtt_recirc.first_flow_rec.flow_sign;
        act_extract_recirc_packet_headers_only_into_curr_records();
    }

    // Packet table actions
    action subtract_for_comparison_packet_table_cycle() {
        eg_md.sub_result_packet_signatures = eg_md.curr_flow_rec.flow_sign - hdr.p4rtt_recirc.first_flow_rec.flow_sign;
        eg_md.sub_result_packet_eacks      = eg_md.curr_packet_rec.eack - hdr.p4rtt_recirc.first_packet_rec.eack;
    }
    action subtract_for_comparison_staleness_right() {
        eg_md.sub_result_eack_comparison_right = eg_md.curr_flow_rec.right_edge - eg_md.curr_packet_rec.eack;
    }
    action subtract_for_comparison_staleness_left() {
        eg_md.sub_result_eack_comparison_left = eg_md.curr_packet_rec.eack - eg_md.curr_flow_rec.left_edge;
    }

    // Set first record value(s)
    action act_assign_first_records_to_flow_recirc_header() {
        hdr.p4rtt_recirc.first_flow_rec.flow_sign = eg_md.curr_flow_rec.flow_sign;
    }
    action act_assign_first_records_to_packet_recirc_header() {
        hdr.p4rtt_recirc.first_packet_rec.eack = eg_md.curr_flow_rec.right_edge;
    }
    action act_assign_first_records_to_recirc_headers() {
        act_assign_first_records_to_flow_recirc_header();
        act_assign_first_records_to_packet_recirc_header();
    }

    // Determine packet recirculation status
    action set_packet_recirculation_status(bool pkt_recirc) { eg_md.recirculate_packet_record = pkt_recirc; }
    action set_packet_recirculation_as_last() {
        eg_md.recirculate_packet_record = true;
        hdr.p4rtt_recirc.recirc_count_packet = PACKET_TABLE_MAX_RECIRC - 1;
    }

    // Packet recirculation
    table tab_determine_packet_recirculation_status {
        const size = 8;
        key = {
            eg_md.packet_status: exact;
            hdr.p4rtt_recirc.recirc_count_packet: ternary;
            eg_md.curr_packet_rec.timestamp: ternary;
            eg_md.sub_result_packet_signatures: ternary;
            eg_md.sub_result_packet_eacks: ternary;
        }
        actions = { set_packet_recirculation_status; set_packet_recirculation_as_last; no_action; }
        const default_action = no_action();
        const entries = {
            ( 50, PACKET_TABLE_MAX_RECIRC, _, _, _ ) : set_packet_recirculation_status( false );
            ( 50, _, NULL, _, _ ) : set_packet_recirculation_status( false );
            ( 50, _, _, 0, 0 )    : set_packet_recirculation_as_last();
            ( 50, _, _, _, _ )    : set_packet_recirculation_status( true );
            ( 62, PACKET_TABLE_MAX_RECIRC, _, _, _ ) : set_packet_recirculation_status( false );
            ( 62, _, NULL, _, _ ) : set_packet_recirculation_status( false );
            ( 62, _, _, 0, 0 )    : set_packet_recirculation_as_last();
            ( 62, _, _, _, _ )    : set_packet_recirculation_status( true );
        }
    }

    action ack_set_curr_packet_record() {
        eg_md.curr_packet_rec.eack      = eg_md.curr_flow_rec.right_edge;
        eg_md.curr_packet_rec.timestamp = eg_md.ingress_tstamp;
    }

    // Set recirculated packet type
    action act_set_outgoing_packet_type(packet_type_t outgoing_pkt_type) {
        hdr.p4rtt_recirc.recirc_type = outgoing_pkt_type;
    }

    table tab_set_outgoing_packet_type {
        const size = 6;
        key = {
            eg_md.packet_status: exact;
            eg_md.packet_type: exact;
            eg_md.recirculate_flow_record: exact;
            eg_md.recirculate_packet_record: exact;
        }
        actions = { act_set_outgoing_packet_type; no_action; }
        const default_action = no_action;
        const entries = {
            ( 50, PKT_TYPE_FTI_PIN, true, false ) : act_set_outgoing_packet_type( PKT_TYPE_FTE_PRE );
            ( 50, PKT_TYPE_FTI_PIN, false, true ) : act_set_outgoing_packet_type( PKT_TYPE_PTE_PIN );
            ( 50, PKT_TYPE_FTE_PIN, true, false ) : act_set_outgoing_packet_type( PKT_TYPE_FTE_PIN );
            ( 50, PKT_TYPE_FTE_PRE, true, false ) : act_set_outgoing_packet_type( PKT_TYPE_FTE_PRE );
            ( 50, PKT_TYPE_FTE_PRE, false, true ) : act_set_outgoing_packet_type( PKT_TYPE_PTE_PIN );
            ( 62, PKT_TYPE_PTE_PIN, false, true ) : act_set_outgoing_packet_type( PKT_TYPE_PTE_PIN );
        }
    }

    // Bridged metadata for egress processing
    action act_extract_bridged_metadata() {

        eg_md.ingress_tstamp = eg_md.bridged_md.ingress_tstamp;

        eg_md.packet_type      = eg_md.bridged_md.packet_type;
        eg_md.packet_status    = eg_md.bridged_md.packet_status;
        eg_md.ft_update_status = eg_md.bridged_md.ft_update_status;

        eg_md.curr_flow_rec.flow_sign    = eg_md.bridged_md.curr_flow_rec.flow_sign;
        eg_md.curr_flow_rec.right_edge   = eg_md.bridged_md.curr_flow_rec.right_edge;
        eg_md.curr_flow_rec.left_edge    = eg_md.bridged_md.curr_flow_rec.left_edge;

        eg_md.sub_result_flow_signatures = eg_md.bridged_md.sub_result_flow_signatures;

        eg_md.bridged_md.setInvalid();
    }

    action act_set_rtt_sample_packet_headers() {

        // IPv4 header
        ipv4_addr_t temp_addr     = hdr.ipv4.src_addr;
        hdr.ipv4.version          = 4w0x4;
        hdr.ipv4.ihl              = 4w0x5;
        hdr.ipv4.diffserv         = eg_md.counter_ack_pkts + 1;
        hdr.ipv4.identification   = eg_md.counter_seq_pkts;
        hdr.ipv4.protocol         = IP_PROTOCOL_UDP;
        hdr.ipv4.src_addr         = hdr.ipv4.dst_addr;
        hdr.ipv4.dst_addr         = temp_addr;
        
        // RTT report (UDP) header
        hdr.tcp.setInvalid();
        hdr.rtt_report.setValid();
        hdr.rtt_report.src_port   = hdr.tcp.dst_port;
        hdr.rtt_report.dst_port   = hdr.tcp.src_port;
        hdr.rtt_report.total_length = 20; // UDP header (8 bytes) + UDP data (4 bytes * 3 = 12 bytes)
        hdr.rtt_report.checksum  = eg_md.counter_recirc_pkts;
        hdr.rtt_report.ack_no    = hdr.tcp.ack_no;
        hdr.rtt_report.pt_tstamp = eg_md.curr_packet_rec.timestamp;
        hdr.rtt_report.rtt       = eg_md.sampled_rtt;
    }

    #include "util_packet_table_stage_0_egress.p4"
    #include "util_recirc_counter_egress.p4"

    apply {

        act_extract_bridged_metadata();
        eg_md.p4rtt_recirc_valid = hdr.p4rtt_recirc.isValid();

        tab_determine_flow_recirculation_status.apply();

        if ( eg_md.packet_status == 50 && eg_md.recirculate_flow_record ) {
            act_set_for_recirculation();
            act_assign_curr_fields_to_recirc_curr_flow_header();
            act_increment_flow_recirc_count();
            eg_md.packet_status = 51;
        }

        else if ( eg_md.packet_status == 50 && eg_md.packet_type == PKT_TYPE_FTI_PIN ) {
            act_extract_recirc_packet_header_into_curr_records_for_fti_pin();
            eg_md.packet_status = 52;
        }
        
        else if ( eg_md.packet_status == 50 && eg_md.packet_type == PKT_TYPE_FTE_PRE ) {
            act_extract_recirc_packet_header_into_curr_records_for_fte_pre();
            eg_md.packet_status = 52;
        }

        else if ( eg_md.packet_status == 61 ) {

            act_extract_recirc_packet_headers_only_into_curr_records();
            subtract_for_comparison_staleness_right();
            subtract_for_comparison_staleness_left();

            if ( (eg_md.sub_result_eack_comparison_right == 0 || eg_md.sub_result_eack_comparison_right[31:31] == 0)
                    && eg_md.sub_result_eack_comparison_left[31:31] == 0 ) {
                eg_md.packet_status = 62;
            }

        }

        else if ( eg_md.ft_update_status == STATUS_MR_NULL && eg_md.packet_type == PKT_TYPE_TCP_SEQ ) {

            act_set_for_recirculation(); // Recirculate FTI
            act_set_outgoing_packet_type( PKT_TYPE_FTI_PIN );
            
            // Set first records
            act_assign_first_records_to_recirc_headers();
            // Set current records
            act_assign_fresh_curr_fields_to_recirc_curr_headers();
            // Set initial recirculation counts
            act_set_initial_recirc_counts();
            eg_md.packet_status = 78;
        
        }
        
        else if ( eg_md.ft_update_status == STATUS_MR_PROCEED && eg_md.packet_type == PKT_TYPE_TCP_SEQ ) {
            ack_set_curr_packet_record();
            eg_md.packet_status = 79;
        }
        
        // PKT_TYPE_TCP_ACK or PKT_TYPE_TCP_BTH
        else if ( (eg_md.packet_status == 83 || eg_md.packet_status == 84) && eg_md.ft_update_status == STATUS_MR_PROCEED ) {
            ack_set_curr_packet_record();
            eg_md.packet_status = 85;
        }
        
        // Compute PT index
        act_compute_index_packet_table_stage_0();
        
        // PT packet signature action
        tab_execute_pt_packet_sign_action.apply();

        // PT eACK action
        tab_execute_pt_packet_eack_action.apply();

        if ( eg_md.packet_status == 85 && eg_md.do_packet_signatures_match && eg_md.do_packet_eacks_match ) {
            eg_md.packet_status = 86;
        }

        // PT timestamp action
        tab_execute_pt_packet_timestamp_action.apply();

        if ( eg_md.packet_status == 62 ) {
            // Determine whether PT record needs to recirculate
            subtract_for_comparison_packet_table_cycle();
        }

        // Determine whether PT record needs to recirculate
        tab_determine_packet_recirculation_status.apply();

        // Counter actions
        tab_process_counter_seq_packets.apply();
        tab_process_counter_action_recirc_packets.apply();
        tab_process_counter_ack_packets.apply();

        if ( ( eg_md.packet_status == 52 || eg_md.packet_status == 62 )
             && eg_md.recirculate_packet_record ) {

            act_set_for_recirculation();
            act_assign_curr_fields_to_recirc_curr_packet_only_header();
            act_increment_packet_recirc_count();
        }

        else if ( eg_md.packet_status == 86 ) {
            eg_md.sampled_rtt = eg_md.ingress_tstamp - eg_md.curr_packet_rec.timestamp;
            act_set_rtt_sample_packet_headers();
            eg_md.drop_packet = false;
        }

        else if ( eg_md.packet_type == PKT_TYPE_TCP_BTH ) {
            eg_md.drop_packet = false;
        }

        tab_set_outgoing_packet_type.apply();

        if (eg_md.drop_packet) {
            eg_intr_dprs_md.drop_ctl = 0x1;
        } else {
            eg_intr_dprs_md.drop_ctl = 0x0;
        }

    }
}

// Switch Pipeline

Pipeline(SwitchIngressParser(),
         SwitchIngress(),
         SwitchIngressDeparser(),
         SwitchEgressParser(),
         SwitchEgress(),
         SwitchEgressDeparser()) pipe;

Switch(pipe) main;