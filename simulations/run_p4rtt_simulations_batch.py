from SimulationBatch import SimulationBatch
from datetime import datetime, timedelta
import os

##################################################

IS_TEST = False
SERVER  = "jrex-dell"

##################################################

def run_simulations_batch():

    ## Base path
    if SERVER == "cabernet804":
        ## cabernet804 path
        base_path  = "/mnt/p4rtt_sata"
        local_path = "/u/satadals/scratch"
    elif SERVER == "ionic":
        ## ionic path
        base_path  = "/n/fs/anonflow/p4rtt_sata"
        local_path = "/scratch/satadals"
        # local_path = "/n/fs/anonflow/p4rtt_sata/scratch"
    elif SERVER == "jrex-dell":
        ## jrex-dell path
        base_path  = "/u/satadals/mnt/trace_04_07_2020"
        local_path = "/u/satadals/scratch"
        code_path  = "/u/satadals/workspace/p4-measurements/p4rtt-simulations"
    
    tcptrace_data_paths = {
                            "p4rtt_simulations_dir": os.path.join(local_path, "simulations"),
                            # "all_pkts_pickle": os.path.join(base_path, "tcptrace_parsed_data/all_packets_meandata.pickle"),
                            # "part_pkts_pickle": os.path.join(base_path, "tcptrace_parsed_data/packets_meandata_{}.pickle"),
                            "part_pkts_pickle": os.path.join(local_path, "local_packets/packets_meandata_{}.pickle"),
                            "part_pkts_count": 14,
                            # "part_pkts_count": 1,
                            "total_packets_count": 135777565,
                            # "all_pkts_pickle": os.path.join(base_path, "tcptrace_parsed_data/packets_meandata_00.pickle"),
                            # "test_pkts_pickle": os.path.join(base_path, "tcptrace_parsed_data/test_packets_sampled.pickle"),
                            # "test_pkts_pickle": os.path.join(base_path, "tcptrace_parsed_data/test_packets_one_conn.pickle"),
                            "test_pkts_pickle": os.path.join(base_path, "tcptrace_parsed_data/packets_meandata_00.pickle"),
                            "local_directory": os.path.join(local_path, "local_packets"),
                            "code_path": code_path
                        }

    flowtab_params = {
                        "num_stages": [1, ], #[r for r in range(4, 5, 2)],
                        "max_size":  [65536, ], # 65536], #[256, 1024, 4096, 16384], # 
                        "recirculations": [3, ], #[r for r in range(3, 4, 1)],
                        "prefer_new": [True, ],
                        "eviction_stage": ["start", ], # ["start", "immediate", "end"],
                        "entry_timeout": [None, ],
                        "sampling_threshold": [None, ],
                        "sampling_rate": [1.0, ],
                        "syn_action": ["ignore", ], #["timeout", "ignore", "staging"],
                        "syn_timeout_entry_timeout": [None, ], #[500, ],
                        "syn_staging_num_stages": [r for r in range(4, 5, 2)],
                        "syn_staging_max_size": [20000, ],
                        "syn_staging_recirculations": [r for r in range(1, 2, 1)],
                        "syn_staging_prefer_new": [True, ],
                        "syn_staging_eviction_stage": ["start", ],
                        "syn_staging_entry_timeout": [500, ],
                        "log_interval": [5000, ]
                    }

    packettab_params = {
                            "num_stages": [1, ], # 2, 3], #[r for r in range(4, 5, 2)],
                            "max_size": [1024, 2048, 4096, 8192, 16384, 32768, 65536], #131072, 262144],
                            "recirculations": [8,], #[r for r in range(1, 2, 1)],
                            "prefer_new": [True, ],
                            "eviction_stage": ["start", ], # ["start", "immediate", "end"],
                            "entry_timeout": [None, ],
                            "sampling_threshold": [None, ],
                            "sampling_rate": [1.0, ],
                            "log_interval": [5000, ]
                        }

    apxflowtab_params = {
                            "enable_apxft": [False], #[False, True],
                            "num_stages": [r for r in range(4, 5, 2)],
                            "max_size": [256, 1024],
                            "recirculations": [r for r in range(1, 2, 1)],
                            "prefer_new": [True, ],
                            "eviction_stage": ["start", ], # ["start", "immediate", "end"],
                            "entry_timeout": [None, ],
                            "sampling_threshold": [None, ],
                            "sampling_rate": [1.0, ],
                            "log_interval": [10000, ]
                        }
    
    if IS_TEST:

        ## test params
        flowtab_params = {
                            "num_stages": [4, ],
                            "max_size": [10, ],
                            "recirculations": [3, ],
                            "prefer_new": [True, ],
                            "eviction_stage": ["start", ], #["start", "immediate", "end"],
                            "entry_timeout": [None, ], #[500, ],
                            "sampling_threshold": [None, ],
                            "sampling_rate": [1.0, ],
                            "syn_action": ["ignore", ], #["timeout", "ignore", "staging"],
                            "syn_timeout_entry_timeout": [None, ], #[500, ],
                            "syn_staging_num_stages": [3, ],
                            "syn_staging_max_size": [15, ],
                            "syn_staging_recirculations": [1, ],
                            "syn_staging_prefer_new": [True, ],
                            "syn_staging_eviction_stage": ["start", ],
                            "syn_staging_entry_timeout": [None, ], #[500, ],
                            "log_interval": [1, ]
                        }

        packettab_params = {
                                "num_stages": [6, ],
                                "max_size": [18, ],
                                "recirculations": [3, ],
                                "prefer_new": [True, ],
                                "eviction_stage": ["start", ], #["start", "immediate", "end"],
                                "entry_timeout": [None, ],
                                "sampling_threshold": [None, ],
                                "sampling_rate": [1.0, ],
                                "log_interval": [1, ]
                            }
        
        apxflowtab_params = {
                                "enable_apxft": [True],
                                "num_stages": [2, ],
                                "max_size": [4, ],
                                "recirculations": [0, ],
                                "prefer_new": [True, ],
                                "eviction_stage": ["start", ], #["start", "immediate", "end"],
                                "entry_timeout": [None, ], #[500, ],
                                "sampling_threshold": [None, ],
                                "sampling_rate": [1.0, ],
                                "log_interval": [1, ]
                            }
        
    simulation_batch = SimulationBatch(tcptrace_data_paths = tcptrace_data_paths, flowtab_params = flowtab_params,
                                        packettab_params = packettab_params, apxflowtab_params = apxflowtab_params, test = IS_TEST)
    simulation_batch.p4rtt_simulate_batch()

##################################################

def main():

    t_format = "%Y-%m-%d %H:%M:%S"
    t_start  = datetime.now()
    print("Starting simulations at time: {}".format(t_start.strftime(t_format)))
    run_simulations_batch()
    t_end = datetime.now()
    t_elapsed = round((t_end - t_start)/timedelta(minutes=1), 2)
    print("Simulations complete at time: {}".format(t_end.strftime(t_format)))
    print("Time elapsed: {} mins.".format(t_elapsed))

##################################################

if __name__ == "__main__":
    main()

##################################################
