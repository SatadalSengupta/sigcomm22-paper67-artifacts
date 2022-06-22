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

    def _augment_execution_script(self, simulation_parameters):

        params_str = json.dumps(simulation_parameters)
        command = "nohup python3 -u Simulation.py '{}' 1>>{} 2>&1 &\n".format(
                    params_str, self._log_file)
        
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

    def _trigger_execution_script(self):

        copy(self._local_exec_script, self._remote_exec_script)
        proc = subprocess.run(self._local_exec_script)

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
