from Simulation import Simulation
from multiprocessing import Pool, Process, cpu_count
from datetime import datetime, timedelta
from itertools import product, chain
from shutil import copy, move
from sys import exit
import subprocess
import pickle
import json
import stat
import os

##################################################

class SimulationBatch(object):

    ##################################################

    def __init__(self, tcptrace_data_paths, flowtab_params, packettab_params, apxflowtab_params, test=True):
        
        self._start_time              = (datetime.now() - datetime.utcfromtimestamp(0)).total_seconds()
        self._test                    = test
        self._flowtab_params          = None
        self._packettab_params        = None
        self._apxflowtab_params       = None
        self._simulation_results_dir  = None
        self._simulation_batch_number = None
        self._simulation_batch_dir    = None
        self._tcptrace_data_paths     = tcptrace_data_paths

        ## Read flow table parameters
        reqd_flowtab_params = ["num_stages", "max_size", "recirculations", "prefer_new", "eviction_stage", "entry_timeout", \
                               "sampling_threshold", "sampling_rate", "syn_action", "syn_timeout_entry_timeout", \
                               "syn_staging_num_stages", "syn_staging_max_size", "syn_staging_recirculations", \
                               "syn_staging_prefer_new", "syn_staging_eviction_stage", "syn_staging_entry_timeout", "log_interval"]
        for param in reqd_flowtab_params:
            if param not in flowtab_params:
                self._custom_print("Missing packet table parameter: {}. Exiting simulation.".format(param))
                exit(1)
        self._flowtab_params = flowtab_params

        ## Read packet table parameters
        reqd_pkttab_params = ["num_stages", "max_size", "recirculations", "prefer_new", "eviction_stage", \
                              "entry_timeout", "sampling_threshold", "sampling_rate", "log_interval"]
        for param in reqd_pkttab_params:
            if param not in packettab_params:
                self._custom_print("Missing packet table parameter: {}. Exiting simulation.".format(param))
                exit(1)
        self._packettab_params = packettab_params

        ## Read approx. flow table parameters
        reqd_apxflowtab_params = ["enable_apxft", "num_stages", "max_size", "recirculations", "prefer_new", "eviction_stage", \
                                  "entry_timeout", "sampling_threshold", "sampling_rate", "log_interval"]
        for param in reqd_apxflowtab_params:
            if param not in apxflowtab_params:
                self._custom_print("Missing approx. packet table parameter: {}. Exiting simulation.".format(param))
                exit(1)
        self._apxflowtab_params = apxflowtab_params

        ## Set simulation directory
        self._simulation_results_dir = tcptrace_data_paths["p4rtt_simulations_dir"]
        if not os.path.exists(self._simulation_results_dir):
            self._custom_print("Create directory: {}".format(self._simulation_results_dir))
            os.makedirs(self._simulation_results_dir)
        
        ## Determine batch number
        batch_numbers = []
        if not os.path.exists(self._simulation_results_dir):
            self._custom_print("Simulation results directory does not exist. Exit simulation.")
            exit(1)
        for batch_dirname in os.listdir(self._simulation_results_dir):
            if os.path.isdir(os.path.join(self._simulation_results_dir, batch_dirname)):
                batch_numbers.append(int(batch_dirname.split("_")[2]))
        if len(batch_numbers) > 0:
            self._simulation_batch_number = max(batch_numbers) + 1
        else:
            self._simulation_batch_number = 0

        ## Create simulation batch directory
        self._simulation_batch_dir = os.path.join(tcptrace_data_paths["p4rtt_simulations_dir"], "simulation_batch_{}".format(str(self._simulation_batch_number).zfill(3)))
        if os.path.exists(self._simulation_batch_dir):
            self._custom_print("Batch path already exists. Exit simulation.")
            exit(1)
        self._custom_print("Create directory: {}".format(self._simulation_batch_dir))
        os.makedirs(self._simulation_batch_dir)

        # ## Load all packets in trace inside a massive list
        # self._custom_print("Build packets data")
        # self._packets = self._build_packets_data()

        ## Determine execution script path
        if not os.path.exists("scripts"):
            os.makedirs("scripts")
        self._local_exec_script  = os.path.join("scripts", "sim_batch_exec_script.sh")
        self._remote_exec_script = os.path.join(self._simulation_batch_dir, "sim_batch_exec_script.sh")
        with open(self._local_exec_script, 'w') as fp:
            fp.write("#!/bin/sh\n")

        ## Determine log file path
        datetime_str = datetime.now().strftime("%Y%m%d_%H%M")
        self._log_file = os.path.join(self._simulation_batch_dir, "sim_log_{}.txt".format(datetime_str))

        ## Copy packets file to local
        self._prepare_local_data()

        ## Create parameters file
        params_lines = []
        params_lines.append("##################################################")
        params_lines.append("Simulation Batch No.: {}".format(self._simulation_batch_number))
        # params_lines.append("Packet Count: {}\n".format(len(self._packets)))
        params_lines.append("")
        params_lines.append("##### Flow Table Parameters #####")
        params_lines.append("num_stages: {}".format(self._flowtab_params["num_stages"]))
        params_lines.append("max_size: {}".format(self._flowtab_params["max_size"]))
        params_lines.append("recirculations: {}".format(self._flowtab_params["recirculations"]))
        params_lines.append("prefer_new: {}".format(self._flowtab_params["prefer_new"]))
        params_lines.append("eviction_stage: {}".format(self._flowtab_params["eviction_stage"]))
        params_lines.append("entry_timeout: {}".format(self._flowtab_params["entry_timeout"]))
        params_lines.append("sampling_threshold: {}".format(self._flowtab_params["sampling_threshold"]))
        params_lines.append("sampling_rate: {}".format(self._flowtab_params["sampling_rate"]))
        params_lines.append("syn_action: {}".format(self._flowtab_params["syn_action"]))
        params_lines.append("syn_timeout_entry_timeout: {}".format(self._flowtab_params["syn_timeout_entry_timeout"]))
        params_lines.append("syn_staging_num_stages: {}".format(self._flowtab_params["syn_staging_num_stages"]))
        params_lines.append("syn_staging_max_size: {}".format(self._flowtab_params["syn_staging_max_size"]))
        params_lines.append("syn_staging_recirculations: {}".format(self._flowtab_params["syn_staging_recirculations"]))
        params_lines.append("syn_staging_prefer_new: {}".format(self._flowtab_params["syn_staging_prefer_new"]))
        params_lines.append("syn_staging_eviction_stage: {}".format(self._flowtab_params["syn_staging_eviction_stage"]))
        params_lines.append("syn_staging_entry_timeout: {}".format(self._flowtab_params["syn_staging_entry_timeout"]))
        params_lines.append("log_interval: {}".format(self._flowtab_params["log_interval"]))
        params_lines.append("")
        params_lines.append("##### Packet Table Parameters #####")
        params_lines.append("num_stages: {}".format(self._packettab_params["num_stages"]))
        params_lines.append("max_size: {}".format(self._packettab_params["max_size"]))
        params_lines.append("recirculations: {}".format(self._packettab_params["recirculations"]))
        params_lines.append("prefer_new: {}".format(self._packettab_params["prefer_new"]))
        params_lines.append("eviction_stage: {}".format(self._packettab_params["eviction_stage"]))
        params_lines.append("entry_timeout: {}".format(self._packettab_params["entry_timeout"]))
        params_lines.append("sampling_threshold: {}".format(self._packettab_params["sampling_threshold"]))
        params_lines.append("sampling_rate: {}".format(self._packettab_params["sampling_rate"]))
        params_lines.append("log_interval: {}".format(self._packettab_params["log_interval"]))
        params_lines.append("")
        params_lines.append("##### Approx. Flow Table Parameters #####")
        params_lines.append("enable_apxft: {}".format(self._apxflowtab_params["enable_apxft"]))
        params_lines.append("num_stages: {}".format(self._apxflowtab_params["num_stages"]))
        params_lines.append("max_size: {}".format(self._apxflowtab_params["max_size"]))
        params_lines.append("recirculations: {}".format(self._apxflowtab_params["recirculations"]))
        params_lines.append("prefer_new: {}".format(self._apxflowtab_params["prefer_new"]))
        params_lines.append("eviction_stage: {}".format(self._apxflowtab_params["eviction_stage"]))
        params_lines.append("entry_timeout: {}".format(self._apxflowtab_params["entry_timeout"]))
        params_lines.append("sampling_threshold: {}".format(self._apxflowtab_params["sampling_threshold"]))
        params_lines.append("sampling_rate: {}".format(self._apxflowtab_params["sampling_rate"]))
        params_lines.append("log_interval: {}".format(self._apxflowtab_params["log_interval"]))
        params_lines.append("")
        params_lines.append("##################################################\n")
        
        params_text = "\n".join(params_lines)
        batch_params_path = os.path.join(self._simulation_batch_dir, "simulation_batch_parameters.txt")
        self._custom_print("Write batch parameters to: {}".format(batch_params_path))
        with open(batch_params_path, "w") as fp:
            fp.write(params_text)

        ## Simulation combinations
        self._num_combinations = 0
        base_count = len(self._flowtab_params["num_stages"]) * len(self._flowtab_params["max_size"]) * len(self._flowtab_params["recirculations"]) \
                        * len(self._flowtab_params["prefer_new"]) * len(self._flowtab_params["eviction_stage"]) * len(self._flowtab_params["entry_timeout"]) \
                        * len(self._flowtab_params["sampling_threshold"]) * len(self._flowtab_params["sampling_rate"]) * len(self._flowtab_params["syn_action"]) \
                        * len(self._flowtab_params["syn_timeout_entry_timeout"]) * len(self._flowtab_params["syn_staging_num_stages"]) \
                        * len(self._flowtab_params["syn_staging_max_size"]) * len(self._flowtab_params["syn_staging_recirculations"]) \
                        * len(self._flowtab_params["syn_staging_prefer_new"]) * len(self._flowtab_params["syn_staging_eviction_stage"]) \
                        * len(self._flowtab_params["syn_staging_entry_timeout"]) * len(self._flowtab_params["log_interval"]) \
                        * len(self._packettab_params["num_stages"]) * len(self._packettab_params["max_size"]) * len(self._packettab_params["recirculations"]) \
                        * len(self._packettab_params["prefer_new"]) * len(self._packettab_params["eviction_stage"]) * len(self._packettab_params["entry_timeout"]) \
                        * len(self._packettab_params["sampling_threshold"]) * len(self._packettab_params["sampling_rate"]) * len(self._packettab_params["log_interval"])

        for enable_apxft in self._apxflowtab_params["enable_apxft"]:

            if not enable_apxft:
                self._num_combinations += base_count
                # self._custom_print("AFT enabled is: {}, no. of combinations: {}".format(enable_apxft, self._num_combinations))
            else:                     
                self._num_combinations += base_count * len(self._apxflowtab_params["num_stages"]) * len(self._apxflowtab_params["max_size"]) \
                                        * len(self._apxflowtab_params["recirculations"]) * len(self._apxflowtab_params["prefer_new"]) * len(self._apxflowtab_params["eviction_stage"]) \
                                        * len(self._apxflowtab_params["entry_timeout"]) * len(self._apxflowtab_params["sampling_threshold"]) * len(self._apxflowtab_params["sampling_rate"]) \
                                        * len(self._apxflowtab_params["log_interval"])
                # self._custom_print("AFT enabled is: {}, no. of combinations: {}".format(enable_apxft, self._num_combinations))

        self._custom_print("No. of simulations in this batch: {}".format(self._num_combinations))
    
    ##################################################

    def _custom_print(self, text, flush=True):
        print(text, flush=flush)

    ##################################################

    def _clean_packets_data(self):

        all_packets_meandata = []
        remote_src = self._tcptrace_data_paths["seq_pkts_pickle"]
        remote_dst = os.path.dirname(remote_src)
        local_src_dir = "/scratch/satadals/packets_meandata_dir"
        if not os.path.exists(local_src_dir):
            os.makedirs(local_src_dir)
        
        for seq_count in range(14):
            remote_src_path = remote_src.format(str(seq_count).zfill(2))
            local_src_path  = os.path.join(local_src_dir, "packets_meandata_{}.pickle".format(str(seq_count).zfill(2)))
            copy(remote_src_path, local_src_path)

            self._custom_print("Process packets list from: {}".format(remote_src_path))
            with open(local_src_path, "rb") as packets_fp:
                seq_packets = pickle.load(packets_fp)

            # packets_meandata = []
            # for packet in seq_packets:
            #     # packet_mindata = {}
            #     # packet_mindata["pktno"]     = packet["pktno"]
            #     # packet_mindata["timestamp"] = packet["timestamp"]
            #     # packet_mindata["ipsrc"]     = packet["ipsrc"]
            #     # packet_mindata["ipdst"]     = packet["ipdst"]
            #     # packet_mindata["tcpsrc"]    = packet["tcpsrc"]
            #     # packet_mindata["tcpdst"]    = packet["tcpdst"]
            #     # packet_mindata["tcpflags"]  = packet["tcpflags"]
            #     # packet_mindata["seqno"]     = packet["seqno"]
            #     # packet_mindata["ackno"]     = packet["ackno"]
            #     # packet_mindata["pktsize"]   = packet["pktsize"]
            #     packet_meandata = (packet["pktno"], packet["timestamp"], packet["ipsrc"], packet["ipdst"],
            #                       packet["tcpsrc"], packet["tcpdst"], packet["tcpflags"],
            #                       packet["seqno"], packet["ackno"], packet["pktsize"])
            #     packets_meandata.append(packet_meandata)
            
            all_packets_meandata.extend(seq_packets)
            
            # local_dst_path  = os.path.join(local_dst_dir, "packets_meandata_{}.pickle".format(str(seq_count).zfill(2)))
            # remote_dst_path = os.path.join(remote_dst, "packets_meandata_{}.pickle".format(str(seq_count).zfill(2)))
                
            # self._custom_print("Dump packets to: {}".format(local_dst_path))
            # with open(local_dst_path, "wb") as packets_fp:
            #     pickle.dump(packets_meandata, packets_fp)
            
            # move(local_dst_path, remote_dst_path)
            os.remove(local_src_path)
        
        local_dst_path  = os.path.join(local_src_dir, "all_packets_meandata.pickle")
        remote_dst_path = os.path.join(remote_dst, "all_packets_meandata.pickle")
        self._custom_print("Dump packets to: {}".format(local_dst_path))
        with open(local_dst_path, "wb") as packets_fp:
            pickle.dump(all_packets_meandata, packets_fp)
        copy(local_dst_path, remote_dst_path)
        self._custom_print("Cleaned data!")

        return

    ##################################################

    def _build_packets_data(self):

        t_format = "%Y-%m-%d %H:%M:%S"
        t_start  = datetime.now()
        self._custom_print("Build packets data starts at time: {}".format(t_start.strftime(t_format)))

        remote_packets_path = self._tcptrace_data_paths["all_pkts_pickle"]
        if self._test:
            remote_packets_path = self._tcptrace_data_paths["test_pkts_pickle"]
        
        # self._custom_print("BEFORE check path existence: {}".format(os.path.exists(self._tcptrace_data_paths["local_directory"])))
        if not os.path.exists(self._tcptrace_data_paths["local_directory"]):
            # self._custom_print("WITHIN check path existence: {}".format(os.path.exists(self._tcptrace_data_paths["local_directory"])))
            os.makedirs(self._tcptrace_data_paths["local_directory"])
        # self._custom_print("AFTER check path existence: {}".format(os.path.exists(self._tcptrace_data_paths["local_directory"])))
        local_packets_path = os.path.join(self._tcptrace_data_paths["local_directory"], "local_packets.pickle")
        copy(remote_packets_path, local_packets_path)

        with open(local_packets_path, "rb") as packets_fp:
            packets = pickle.load(packets_fp)
        
        ## Temp
        # packets = packets[:250000]
        # packets = packets[:100000]
        
        # if self._test and len(packets) > 1000:
        #     packets = packets[:len(packets)//100]
        
        t_end     = datetime.now()
        t_elapsed = round((t_end - t_start)/timedelta(minutes=1), 2)
        self._custom_print("Build packets complete at time: {}; time elapsed: {} mins.".format(t_end.strftime(t_format), t_elapsed))

        return packets

        # ## Load from existing packets dict
        # if os.path.exists(self._tcptrace_data_paths["all_pkts_pickle"]):
        #     self._custom_print("Loading existing packets list")
        #     with open(self._tcptrace_data_paths["all_pkts_pickle"], "rb") as packets_fp:
        #         packets = pickle.load(packets_fp)
        #     return packets

        # ## Built complete packets dict
        # if not os.path.exists(os.path.dirname(self._tcptrace_data_paths["all_pkts_pickle"])):
        #     os.makedirs(os.path.dirname(self._tcptrace_data_paths["all_pkts_pickle"]))
        # packets = []
        # for seq_count in range(14):
        #     packets_path = self._tcptrace_data_paths["seq_pkts_pickle"].format(str(seq_count).zfill(2))
        #     self._custom_print("Extending packets list with packets from: {}".format(packets_path))
        #     with open(packets_path, "rb") as packets_fp:
        #         seq_packets = pickle.load(packets_fp)
        #         packets.extend(seq_packets)
        # self._custom_print("Dumping packets list to: {}".format(self._tcptrace_data_paths["all_pkts_pickle"]))
        # with open(self._tcptrace_data_paths["all_pkts_pickle"], "wb") as packets_fp:
        #     pickle.dump(packets, packets_fp)
        # return packets

    ##################################################

    def _remove_packets_data(self):

        self._custom_print("Clean up local packets data")
        # local_packets_path = os.path.join(self._tcptrace_data_paths["local_directory"], "local_packets.pickle")
        # if os.path.exists(local_packets_path):
        #     os.remove(local_packets_path)

        if os.path.exists(self._tcptrace_data_paths["local_directory"]):
            local_packets_path = os.path.join(self._tcptrace_data_paths["local_directory"], "local_packets_round_{}.pickle")
            for count in range(self._tcptrace_data_paths["part_pkts_count"]):
                curr_local_packets_path  = local_packets_path.format(str(count).zfill(2))
                if os.path.exists(curr_local_packets_path):
                    os.remove(curr_local_packets_path)

    ##################################################

    def _prepare_local_data(self):

        self._custom_print("Copy packets data file")

        # remote_packets_path = self._tcptrace_data_paths["all_pkts_pickle"]
        # if self._test:
        #     remote_packets_path = self._tcptrace_data_paths["test_pkts_pickle"]
        
        # if not os.path.exists(self._tcptrace_data_paths["local_directory"]):
        #     os.makedirs(self._tcptrace_data_paths["local_directory"])

        # local_packets_path = os.path.join(self._tcptrace_data_paths["local_directory"], "local_packets_round_0.pickle")
        # if not os.path.exists(local_packets_path):
        #     copy(remote_packets_path, local_packets_path)

        remote_packets_path = self._tcptrace_data_paths["part_pkts_pickle"]
        if not os.path.exists(self._tcptrace_data_paths["local_directory"]):
            os.makedirs(self._tcptrace_data_paths["local_directory"])
        local_packets_path = os.path.join(self._tcptrace_data_paths["local_directory"], "local_packets_round_{}.pickle")

        for count in range(self._tcptrace_data_paths["part_pkts_count"]):
            curr_remote_packets_path = remote_packets_path.format(str(count).zfill(2))
            curr_local_packets_path  = local_packets_path.format(str(count).zfill(2))
            if not os.path.exists(curr_local_packets_path):
                copy(curr_remote_packets_path, curr_local_packets_path)

    ##################################################

    def _augment_execution_script(self, simulation_parameters):

        params_str = json.dumps(simulation_parameters)
        command = "nohup python3 -u {}/Simulation.py '{}' 1>>{} 2>&1 &\n".format(
                    self._tcptrace_data_paths["code_path"], params_str, self._log_file)
        
        with open(self._local_exec_script, 'a') as fp:
            fp.write(command)
    
    ##################################################

    def _conclude_execution_script(self):

        with open(self._local_exec_script, 'a') as fp:
            fp.write("echo \"Waiting for subprocesses to finish...\"\n")
            fp.write("wait\n")
        
        path_st = os.stat(self._local_exec_script)
        os.chmod(self._local_exec_script, path_st.st_mode | stat.S_IEXEC)

    ##################################################

    def _trigger_p4rtt_simulation(self, simulation_params):

        # round_num = simulation_params["sim_params"]["round_number"]
        # # self._custom_print("Round {}/{}: Build packets data".format(round_num, self._num_combinations-1))
        # # self._packets = self._build_packets_data()
        # # simulation_params["sim_params"]["total_packets"] = len(self._packets)
        
        # self._custom_print("Round {}/{}: Create simulation object with current set of params".format(round_num, self._num_combinations-1))
        # simulation = Simulation(simulation_params, self._test)
        # self._custom_print("Round {}/{}: Start P4RTT simulations with created packets list".format(round_num, self._num_combinations-1))
        # # simulation.run_p4rtt_simulation(self._packets)
        # simulation.run_p4rtt_simulation()

        ## Execute shell script
        return

    ##################################################

    def _trigger_execution_script(self):

        copy(self._local_exec_script, self._remote_exec_script)
        proc = subprocess.run(self._local_exec_script)
        # self._remove_packets_data()

    ##################################################

    def p4rtt_simulate_batch(self):

        iterables = {"True": [], "False": []}

        for enable_apxft in self._apxflowtab_params["enable_apxft"]:

            if enable_apxft:

                iterables["True"] = product( self._flowtab_params["num_stages"], self._flowtab_params["max_size"], self._flowtab_params["recirculations"],
                                        self._flowtab_params["prefer_new"], self._flowtab_params["eviction_stage"], self._flowtab_params["entry_timeout"],
                                        self._flowtab_params["sampling_threshold"], self._flowtab_params["sampling_rate"], self._flowtab_params["syn_action"],
                                        self._flowtab_params["syn_timeout_entry_timeout"], self._flowtab_params["syn_staging_num_stages"], self._flowtab_params["syn_staging_max_size"],
                                        self._flowtab_params["syn_staging_recirculations"], self._flowtab_params["syn_staging_prefer_new"], self._flowtab_params["syn_staging_eviction_stage"],
                                        self._flowtab_params["syn_staging_entry_timeout"], self._flowtab_params["log_interval"],
                                        self._packettab_params["num_stages"], self._packettab_params["max_size"], self._packettab_params["recirculations"],
                                        self._packettab_params["prefer_new"], self._packettab_params["eviction_stage"], self._packettab_params["entry_timeout"],
                                        self._packettab_params["sampling_threshold"], self._packettab_params["sampling_rate"], self._packettab_params["log_interval"],
                                        [True], self._apxflowtab_params["num_stages"], self._apxflowtab_params["max_size"], self._apxflowtab_params["recirculations"],
                                        self._apxflowtab_params["prefer_new"], self._apxflowtab_params["eviction_stage"], self._apxflowtab_params["entry_timeout"],
                                        self._apxflowtab_params["sampling_threshold"], self._apxflowtab_params["sampling_rate"], self._apxflowtab_params["log_interval"] )
        
            else:

                iterables["False"] = product( self._flowtab_params["num_stages"], self._flowtab_params["max_size"], self._flowtab_params["recirculations"],
                                        self._flowtab_params["prefer_new"], self._flowtab_params["eviction_stage"], self._flowtab_params["entry_timeout"],
                                        self._flowtab_params["sampling_threshold"], self._flowtab_params["sampling_rate"], self._flowtab_params["syn_action"],
                                        self._flowtab_params["syn_timeout_entry_timeout"], self._flowtab_params["syn_staging_num_stages"], self._flowtab_params["syn_staging_max_size"],
                                        self._flowtab_params["syn_staging_recirculations"], self._flowtab_params["syn_staging_prefer_new"], self._flowtab_params["syn_staging_eviction_stage"],
                                        self._flowtab_params["syn_staging_entry_timeout"], self._flowtab_params["log_interval"],
                                        self._packettab_params["num_stages"], self._packettab_params["max_size"], self._packettab_params["recirculations"],
                                        self._packettab_params["prefer_new"], self._packettab_params["eviction_stage"], self._packettab_params["entry_timeout"],
                                        self._packettab_params["sampling_threshold"], self._packettab_params["sampling_rate"], self._packettab_params["log_interval"], [False] )
        
        
        count_round = 0
        all_simulation_params = []
        for combination in chain(iterables["False"], iterables["True"]):
            params = iter(combination)
            simulation_params = { "sim_params": {}, "flowtab_params": {}, "packettab_params": {}, "apxflowtab_params": {} }
            ## Common params
            simulation_params["sim_params"]["is_test"]             = self._test
            simulation_params["sim_params"]["tcptrace_data_paths"] = self._tcptrace_data_paths
            simulation_params["sim_params"]["sim_batch_dir"]       = self._simulation_batch_dir
            simulation_params["sim_params"]["round_number"]        = count_round
            simulation_params["sim_params"]["combinations_count"]  = self._num_combinations
            simulation_params["sim_params"]["start_time"]          = self._start_time
            count_round += 1
            ## Flow table params
            simulation_params["flowtab_params"]["num_stages"]                 = next(params)
            simulation_params["flowtab_params"]["max_size"]                   = next(params)
            simulation_params["flowtab_params"]["recirculations"]             = next(params)
            simulation_params["flowtab_params"]["prefer_new"]                 = next(params)
            simulation_params["flowtab_params"]["eviction_stage"]             = next(params)
            simulation_params["flowtab_params"]["entry_timeout"]              = next(params)
            simulation_params["flowtab_params"]["sampling_threshold"]         = next(params)
            simulation_params["flowtab_params"]["sampling_rate"]              = next(params)
            simulation_params["flowtab_params"]["syn_action"]                 = next(params)
            simulation_params["flowtab_params"]["syn_timeout_entry_timeout"]  = next(params)
            simulation_params["flowtab_params"]["syn_staging_num_stages"]     = next(params)
            simulation_params["flowtab_params"]["syn_staging_max_size"]       = next(params)
            simulation_params["flowtab_params"]["syn_staging_recirculations"] = next(params)
            simulation_params["flowtab_params"]["syn_staging_prefer_new"]     = next(params)
            simulation_params["flowtab_params"]["syn_staging_eviction_stage"] = next(params)
            simulation_params["flowtab_params"]["syn_staging_entry_timeout"]  = next(params)
            simulation_params["flowtab_params"]["log_interval"]               = next(params)
            ## Packet table params
            simulation_params["packettab_params"]["num_stages"]               = next(params)
            simulation_params["packettab_params"]["max_size"]                 = next(params)
            simulation_params["packettab_params"]["recirculations"]           = next(params)
            simulation_params["packettab_params"]["prefer_new"]               = next(params)
            simulation_params["packettab_params"]["eviction_stage"]           = next(params)
            simulation_params["packettab_params"]["entry_timeout"]            = next(params)
            simulation_params["packettab_params"]["sampling_threshold"]       = next(params)
            simulation_params["packettab_params"]["sampling_rate"]            = next(params)
            simulation_params["packettab_params"]["log_interval"]             = next(params)
            ## Approx. flow table params
            simulation_params["sim_params"]["enable_apxft"]                   = next(params)
            if simulation_params["sim_params"]["enable_apxft"]:
                simulation_params["apxflowtab_params"]["num_stages"]          = next(params)
                simulation_params["apxflowtab_params"]["max_size"]            = next(params)
                simulation_params["apxflowtab_params"]["recirculations"]      = next(params)
                simulation_params["apxflowtab_params"]["prefer_new"]          = next(params)
                simulation_params["apxflowtab_params"]["eviction_stage"]      = next(params)
                simulation_params["apxflowtab_params"]["entry_timeout"]       = next(params)
                simulation_params["apxflowtab_params"]["sampling_threshold"]  = next(params)
                simulation_params["apxflowtab_params"]["sampling_rate"]       = next(params)
                simulation_params["apxflowtab_params"]["log_interval"]        = next(params)
            ## Append to all params list
            all_simulation_params.append(simulation_params)
            # ## No multiprocessing here
            # self._trigger_p4rtt_simulation(simulation_params)
            ## Alternative: Execution script
            self._augment_execution_script(simulation_params)
        
        self._conclude_execution_script()
        
        ## Trigger simulations in a multiprocessed fashion
        self._custom_print("No. of CPUs: {}".format(cpu_count()))
        self._custom_print("No. of usable CPUs: {}".format(len(os.sched_getaffinity(0))))

        self._trigger_execution_script()

##################################################
