# from BitHash import BitHash, ResetBitHash
from CuckooHashTable import CuckooHashTable
from SynTable import SynTable
from datetime import datetime, timedelta
from random import randint
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import itertools
from zlib import crc32
import os, sys

##################################################

MAX_SEQNUM = 2**32

##################################################

class FlowTable(CuckooHashTable):

    ##################################################

    def __init__(self, flowtab_params, test=True):

        ## Call parent's __init__() function
        CuckooHashTable.__init__(self, "flow", flowtab_params, test)
        self._custom_print("Round {}/{}: Initialized flow table".format(self._round_number, self._max_round_number))
        
        # Set SYN action
        if flowtab_params["syn_action"] not in ["timeout", "ignore", "staging"]:
            self._custom_print("Round {}/{}: Invalid option for SYN action, resetting to ignore".format(self._round_number, self._max_round_number))
            self._synAction = "ignore"
        else:
            self._synAction = flowtab_params["syn_action"]
        
        # Set SYN timeout if SYN action is "timeout"
        if self._synAction == "timeout":
            self._synTimeout_entryTimeout = flowtab_params["syn_timeout_entry_timeout"]
        
        # Set SYN staging params if SYN action is "staging"
        if self._synAction == "staging":
            self._synStaging_numStages      = max(1, flowtab_params["syn_staging_num_stages"])
            self._synStaging_maxSize        = max(flowtab_params["syn_staging_num_stages"], flowtab_params["syn_staging_max_size"])
            self._synStaging_recirculations = max(0, flowtab_params["syn_staging_recirculations"])
            self._synStaging_preferNew      = flowtab_params["syn_staging_prefer_new"]
            self._synStaging_evictionStage  = flowtab_params["syn_staging_eviction_stage"]
            self._synStaging_entryTimeout   = flowtab_params["syn_staging_entry_timeout"]
            ## Create SYN table params
            syntab_params = {   "round_num": self._round_number,
                                "num_stages": self._synStaging_numStages,
                                "max_size": self._synStaging_maxSize,
                                "recirculations": self._synStaging_recirculations,
                                "prefer_new": self._synStaging_preferNew,
                                "eviction_stage": self._synStaging_evictionStage,
                                "entry_timeout": self._synStaging_entryTimeout,
                                "sampling_threshold": None,
                                "sampling_rate": None,
                                "log_interval": self._logInterval   }
            # Create SYN staging table if SYN action is "staging"
            self._custom_print("Round {}/{}: Initializing the SYN staging table".format(self._round_number, self._max_round_number))
            self._synTable = SynTable(syntab_params, test)

    ##################################################

    def _custom_print(self, text, flush=True):
        print(text, flush=flush)

    ##################################################

    def _extractEvictionAccountingTime(self, record):
        return record[2]

    ##################################################

    def _checkForAndHandleEviction(self, record, current_tstamp):
        
        if self._test:
            self._custom_print("FT:: Determining if record should be evicted")
        
        _, record_conf_interval, record_entry_tstamp, record_update_tstamp, _, record_update_flags = record
        
        if self._hasSYNTimeoutExpired(record_update_flags, current_tstamp, record_update_tstamp, record_entry_tstamp):
            return True
        
        if self._hasTimeoutExpired(current_tstamp, record_update_tstamp, record_entry_tstamp):
            return True
        
        if record_conf_interval[0] == record_conf_interval[1]:
            self._accountForEviction(current_tstamp, record_update_tstamp, record_entry_tstamp)
            if self._test:
                self._custom_print("FT:: Flow entry confidence interval has collapsed - removing; left bound: {}, right bound: {}".format(record_conf_interval[0], record_conf_interval[1]))
            return True
        
        if self._test:
            self._custom_print("FT:: Do not evict record")

        return False

    ##################################################

    def _constructUpdatedRecord(self, record, new_record):

        flow_key, _, entry_tstamp, _, entry_flags, _        = record
        _, conf_interval, _, update_tstamp, _, update_flags = new_record
        updated_record = (flow_key, conf_interval, entry_tstamp, update_tstamp, entry_flags, update_flags)

        return updated_record
    
    ##################################################

    def _insert(self, record, timestamp):
        ''' Flow table insertion '''

        ## Insert into SYN table if it exists (In current implementation, it doesn't)
        if self._synAction == "staging" and "S" in record[4]:
            return self._synTable.insert(record, timestamp)

        # ## Insert into the last stage if it's empty
        # index  = self._computeNthStageIndex(record[0], self._numStages-1) % self._stageSize
        # record_at_last_stage = self._retrieveRecordByKey(record[0], self._numStages-1)
        # if record_at_last_stage is None:
        #     # index  = self._computeNthStageIndex(record[0], self._numStages-1) % self._stageSize
        #     _ = self._insertRecord(self._numStages-1, index, record)
        #     self.accountant.accountForInsertSuccess()
        #     if self._test: self._custom_print("FT:: Insert at index {} of last (={}) stage.".format(index, self._numStages-1))
        #     return True, [record, ] ## No extra records were touched
        
        ## Insert in the prescribed manner (i.e., according to preferences)
        # if self._test: self._custom_print("FT:: Index {} of last (={}) stage not empty; recirculating...".format(index, self._numStages-1))
        
        if self._test: self._custom_print("SEQ FT:: Couldn't find record in either FT or PT; inserting in FT after recirculation")
        self.accountant.accountForRecirculation()

        attempts        = 0
        stage           = 0
        recirculations  = 1
        touched_records = []

        while attempts < (self._recirculations + 1) * self._numStages:

            if self._test:
                self._custom_print("FT:: Start of the loop: Attempts: {}, Stage: {}, Recirculations: {}, Timestamp: {}, Record: {}".format(
                        attempts, stage, recirculations, timestamp, record))
            
            if attempts > 0:
                
                if stage == 0:
                    ## Recirculating right now
                    if self._test:
                        self._custom_print("FT:: Recirculation {}".format(recirculations + 1))
                    recirculations += 1
                    self.accountant.accountForRecirculation()
            
                if self._evictionStage == "immediate":
                    ## Check for eviction at each stage of the pipeline
                    if self._test:
                        self._custom_print("FT:: Eviction stage is IMMEDIATE, and stage is {} (should be ALWAYS)".format(stage))
                    if self._checkForAndHandleEviction(record, timestamp):
                        self.accountant.accountForInsertSuccess()
                        return True, touched_records
            
                else:

                    if self._evictionStage == "start" and stage == 0:
                        ## Check for eviction at the beginning of the pipeline
                        if self._test:
                            self._custom_print("FT:: Eviction stage is START, and stage is {} (should be 0)".format(stage))
                        if self._checkForAndHandleEviction(record, timestamp):
                            self.accountant.accountForInsertSuccess()
                            return True, touched_records

                    elif self._evictionStage == "end" and stage == self._numStages - 1:
                        ## Check for eviction at the end of the pipeline
                        if self._test:
                            self._custom_print("FT:: Eviction stage is END, and stage is {} (should be NUM_STAGES-1)".format(stage))
                        if self._checkForAndHandleEviction(record, timestamp):
                            self.accountant.accountForInsertSuccess()
                            return True, touched_records
            
            index = self._computeNthStageIndex(record[0], stage) % self._stageSize
            record = self._insertRecord(stage, index, record)
            if self._test: self._custom_print("FT:: Computed index is {}, Evicted record is {}".format(index, record))

            if record is None:
                if self._test: self._custom_print("FT:: Evicted record is NONE, return TRUE")
                self.accountant.accountForInsertSuccess()
                return True, touched_records

            if stage == 0:
                touched_records.append(record + tuple())
            stage = (stage + 1) % self._numStages
            attempts += 1
        
        if self._test:
            self._custom_print("SEQ FT:: Out of the loop without returning, insertion FAILED; last evicted: {}".format(record))
        self.accountant.accountForInsertFailure()

        duration = self._getDurationMicrosec(timestamp, self._extractEvictionAccountingTime(record))
        self.accountant._distribution_reinsertionDuration.append(duration)

        return False, touched_records

    ##################################################

    def insert(self, record, timestamp):

        if self._test:
            self._custom_print("\nFT:: Insert into Flow Table")

        if self.accountant._firstEntryTime is None:
            self.accountant._firstEntryTime = timestamp
        
        self.accountant.accountForInsertAttempt()

        ## Create snapshot (if interval is complete)
        self.accountant.createSnapshot(timestamp)
        
        return self._insert(record, timestamp)

    ##################################################

##################################################
