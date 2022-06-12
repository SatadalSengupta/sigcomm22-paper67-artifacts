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

class ApproxFlowTable(CuckooHashTable):

    ##################################################

    def __init__(self, approx_flowtab_params, test=True):

        ## Call parent's __init__() function
        CuckooHashTable.__init__(self, "approx_flow", approx_flowtab_params, test)
        self._custom_print("Round {}/{}: Initialized approximate flow table".format(self._round_number, self._max_round_number))

    ##################################################

    def _custom_print(self, text, flush=True):
        print(text, flush=flush)

    ##################################################

    def _extractEvictionAccountingTime(self, record):
        return record[3]

    ##################################################

    def _checkForAndHandleEviction(self, record, current_tstamp, state):
        
        if self._test:
            self._custom_print("Determining if record should be evicted")
        
        _, record_conf_interval, record_entry_tstamp, record_update_tstamp, _, record_update_flags = record
        
        if self._hasSYNTimeoutExpired(record_update_flags, current_tstamp, record_update_tstamp, record_entry_tstamp):
            return True
        
        if self._hasTimeoutExpired(current_tstamp, record_update_tstamp, record_entry_tstamp):
            return True
        
        if record_conf_interval[0] == record_conf_interval[1]:
            self._accountForEviction(current_tstamp, record_update_tstamp, record_entry_tstamp)
            if self._test:
                self._custom_print("Approx. flow entry confidence interval has collapsed - removing; left bound: {}, right bound: {}".format(record_conf_interval[0], record_conf_interval[1]))
            return True
        
        if self._test:
            self._custom_print("Do not evict record")

        return False

    ##################################################

    def _constructUpdatedRecord(self, record, new_record):

        flow_key, _, entry_tstamp, _, entry_flags, _        = record
        _, conf_interval, _, update_tstamp, _, update_flags = new_record
        updated_record = (flow_key, conf_interval, entry_tstamp, update_tstamp, entry_flags, update_flags)

        return updated_record
    
    ##################################################

    def _insert_or_update(self, record, timestamp):
        ''' Flow table insertion '''

        original_record = record + tuple()
        
        for stage in range(0, self._numStages):

            contested_index  = self._computeNthStageIndex(original_record[0], stage) % self._stageSize
            contested_record = self._retrieveRecordByIndex(contested_index, stage)

            ## Case 1: If contested record is None, insert and return
            if contested_record is None:
                self._insertRecord(stage, contested_index, record)
                self.accountant.accountForInsertAttempt()
                self.accountant.accountForInsertSuccess()
                if self._test: self._custom_print("AFT:: Case 1: Found empty slot in stage {}, index {} for record {}".format(stage, contested_index, record))
                return True
            
            ## Case 2: If contested record has the same flow key as original record, then update and return
            if contested_record[0] == original_record[0]:
                if self._test: self._custom_print("AFT:: Case 2: Record with same key as original record found in stage {}, index {}".format(
                                                    stage, contested_index))
                if record[0] == original_record[0]:
                    ## Case 2.1: Record being updated has the same flow key, so simply update
                    updated_record = self._constructUpdatedRecord(contested_record, original_record)
                    self._insertRecord(stage, contested_index, updated_record)
                    if self._test: self._custom_print("AFT:: Case 2.1: Flow record for same key exists in stage {}, index {}; updated to {}".format(
                                                        stage, contested_index, updated_record))
                else:
                    ## Case 2.2: Record being updated has a different flow key, so replace
                    self._insertRecord(stage, contested_index, record)
                    if self._test: self._custom_print("AFT:: Case 2.2: Flow record for different key exists in stage {}, index {}; replaced by {}".format(
                                                        stage, contested_index, record))
                self.accountant.accountForUpdateAttempt()
                self.accountant.accountForUpdateSuccess()
                return True
            
            ## Case 3: Cuckoo-style eviction, either until empty slot/matching key found or end of stages reached
            record = self._insertRecord(stage, contested_index, record)
            if self._test: self._custom_print("AFT:: Case 3: Cuckoo eviction at stage {}, index {}; evicted record: {}".format(stage, contested_index, record))
        
        if self._test:
            self._custom_print("AFT:: Out of the loop without returning, insertion/update FAILED")
        self.accountant.accountForInsertAttempt()
        self.accountant.accountForInsertFailure()

        duration = self._getDurationMicrosec(timestamp, self._extractEvictionAccountingTime(record))
        self.accountant._distribution_reinsertionDuration.append(duration)

        return False

    ##################################################

    def insert_or_update(self, record, timestamp):

        if self._test:
            self._custom_print("\nAFT:: Insert into or update Approx. Flow Table")

        if self.accountant._firstEntryTime is None:
            self.accountant._firstEntryTime = timestamp

        ## Create snapshot (if interval is complete)
        self.accountant.createSnapshot(timestamp)
        
        return self._insert_or_update(record, timestamp)

    ##################################################

##################################################
