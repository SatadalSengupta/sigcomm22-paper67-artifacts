from SimulationBatch import SimulationBatch
from datetime import datetime, timedelta
import os

##################################################

IS_TEST = False

##################################################

def run_simulations_batch():

    local_path = "/home/ubuntu/sigcomm22-paper67-artifacts/simulations/intermediate"
    
    tcptrace_data_paths = {
                            "p4rtt_simulations_dir": os.path.join(local_path, "dart_simulations"),
                            "part_pkts_pickle": os.path.join(local_path, "smallFlows.pickle"),
                            "part_pkts_count": 1,
                            "total_packets_count": 14261,
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
                        "log_interval": [2000, ]
                    }

    packettab_params = {
                            "num_stages": [r for r in range(1, 9, 1)],
                            "max_size": [16384, ], #131072, 262144],
                            "recirculations": [8,], #[r for r in range(1, 2, 1)],
                            "prefer_new": [True, ],
                            "eviction_stage": ["start", ], # ["start", "immediate", "end"],
                            "entry_timeout": [None, ],
                            "sampling_threshold": [None, ],
                            "sampling_rate": [1.0, ],
                            "log_interval": [2000, ]
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
