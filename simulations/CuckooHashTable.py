# from BitHash import BitHash, ResetBitHash
from Accountant import Accountant
from datetime import datetime, timedelta
from ipaddress import IPv4Address
from random import randint
from copy import deepcopy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import itertools
from zlib import crc32
import os, sys
import math

##################################################

MAX_SEQNUM = 2**32
MILLION    = 1000000

##################################################

class CuckooHashTable(object):

    ##################################################

    def __init__(self, tab_type, tab_params, test=True):

        ## Set simulation-level parameters
        self._test             = test
        self._test_lookup      = False
        self._tab_type         = tab_type
        self._round_number     = tab_params["round_num"]
        self._max_round_number = tab_params["max_round_num"]
        self._total_packets    = tab_params["total_packets"]
    
        # Set no. of stages
        if tab_params["num_stages"] < 1:
            self._custom_print("Round {}/{}: Number of stages passed <1, reset to 1".format(self._round_number, self._max_round_number))
        self._numStages = max(1, tab_params["num_stages"])
        tab_params["num_stages"] = self._numStages
        
        # Set maximum size of data structure
        if tab_params["max_size"] < tab_params["num_stages"]:
            self._custom_print("Round {}/{}: Max. size passed is less than no. of stages, reset to no. of stages".format(self._round_number, self._max_round_number))
        self._maxSize = max(tab_params["num_stages"], tab_params["max_size"])
        tab_params["max_size"] = self._maxSize
        
        # Set size of each stage
        self._stageSize = self._maxSize // self._numStages
        if not tab_params["max_size"] % tab_params["num_stages"] == 0:
            self._custom_print("Round {}/{}: Max. size not a multiple of the no. of stages, proceed with the closest multiple".format(self._round_number, self._max_round_number))
            self._maxSize = self._numStages * self._stageSize
        tab_params["stage_size"] = self._stageSize

        # Set no. of recirculations allowed
        if tab_params["recirculations"] < 0:
            self._custom_print("Round {}/{}: Number of recirculations passed <0, reset to 0".format(self._round_number, self._max_round_number))
        self._recirculations = max(0, tab_params["recirculations"])
        tab_params["recirculations"] = self._recirculations
        
        # Set preference mode (old/new)
        if tab_params["prefer_new"] not in [True, False]:
            self._custom_print("Round {}/{}: Invalid option for prefer new, reset to True".format(self._round_number, self._max_round_number))
            self._preferNew = True
        else:
            self._preferNew = tab_params["prefer_new"]
        
        # Set eviction stage (start/immediate/end)
        if tab_params["eviction_stage"] not in ["start", "immediate", "end"]:
            self._custom_print("Round {}/{}: Invalid option for eviction stage, reset to start".format(self._round_number, self._max_round_number))
            self._evictionStage = "start"
        else:
            self._evictionStage = tab_params["eviction_stage"]

        # Set entry timeout
        if isinstance(tab_params["entry_timeout"], int):
            self._entryTimeout = tab_params["entry_timeout"]
        else:
            self._entryTimeout = None
        
        # Set sampling threshold
        if isinstance(tab_params["sampling_threshold"], int):
            self._samplingThreshold = tab_params["sampling_threshold"]
        else:
            self._samplingThreshold = None
        
        # Set sampling rate
        if isinstance(tab_params["sampling_rate"], float):
            if tab_params["sampling_rate"] <= 0.0 or tab_params["sampling_rate"] > 1.0:
                self._custom_print("Round {}/{}: Invalid sampling rate specified; proceed with 1.0 (no sampling)".format(self._round_number, self._max_round_number))
                self._samplingRate = 1.0
            else:
                self._samplingRate = min(1.0, tab_params["sampling_rate"])
        else:
            self._samplingRate = None
        
        # Initialize data structure
        if False:
            self._custom_print("Round {}/{}: RECHECK:: Max size: {}, No. of stages: {}, Stage size: {}, Recirculations: {}".format(
            self._round_number, self._max_round_number, self._maxSize, self._numStages, self._stageSize, self._recirculations))
        self._numRecords = 0
        self._hashArrays = []
        for _ in range(self._numStages):
            self._hashArrays.append([None] * self._stageSize)

        ## Logging
        self.accountant = Accountant(self._tab_type, tab_params, test=self._test)

    ##################################################

    def __str__(self):

        if self._maxSize > 50:
            return "{} Table: Too large to print, {} entries".format(self._tab_type.capitalize(), self._numRecords)

        strings = []
        strings.append("{} Table:".format(self._tab_type.capitalize()))
        for i, array in enumerate(self._hashArrays):
            record_strs = []
            for j, record in enumerate(array):
                record_str = "Item{}:".format(j)
                if record is not None and isinstance(record, tuple):
                    sub_record_strs = []
                    for sub_record in record:
                        if isinstance(sub_record, datetime):
                            sub_record_str = sub_record.strftime("%M.%S.%f")
                        elif isinstance(sub_record, tuple):
                            sub_record_str = "|".join([str(k) for k in sub_record])
                        else:
                            sub_record_str = str(sub_record)
                        sub_record_strs.append(sub_record_str)
                    record_str += ":".join(sub_record_strs)
                else:
                    record_str += str(record)
                record_strs.append(record_str)
            array_str = ", ".join(record_strs)
            strings.append("Table {}: {}".format(i, "[" + array_str + "]"))
        
        return "\n".join(strings)

    ##################################################

    def _computeNthStageIndex(self, key, n):

        hash_key = "".join([str(i) for i in key]).encode()
        running_hash = crc32(hash_key)

        for _ in range(n):
            running_hash = crc32(hash_key, running_hash)
        
        return running_hash
    
    ##################################################

    def _getDurationMillisec(self, current_tstamp, record_tstamp):
        return round((current_tstamp - record_tstamp)/timedelta(milliseconds=1), 3)

    ##################################################

    def _getDurationMicrosec(self, current_tstamp, record_tstamp):
        return int((current_tstamp - record_tstamp)/timedelta(microseconds=1))

    ##################################################

    def _accountForEviction(self, current_tstamp, record_update_tstamp, record_entry_tstamp=None, source=None):

        if self._tab_type == "packet" and source == "delete":
            self.accountant.accountForSampling()
        else:
            self.accountant.accountForEviction()
        
        if record_entry_tstamp is None:
            duration = self._getDurationMicrosec(current_tstamp, record_update_tstamp)
        else:
            duration = self._getDurationMicrosec(current_tstamp, record_entry_tstamp)
        
        if self._tab_type == "packet" and source == "delete":
            self.accountant._distribution_sampledEvictionDuration.append(duration)
        else:
            self.accountant._distribution_validEvictionDuration.append(duration)

    ##################################################

    def _hasCustomTimeoutExpired(self, timeout, current_tstamp, record_update_tstamp, record_entry_tstamp):

        duration = self._getDurationMicrosec(current_tstamp, record_update_tstamp)

        ## Evict on timeout
        if timeout is not None and duration/1000 >= timeout:
            self._accountForEviction(current_tstamp, record_update_tstamp, record_entry_tstamp, source="timeout")
            if self._test:
                self._custom_print("Should be evicted due to timeout; Update time: {}, Current time: {}, Delta: {} ms, Timeout: {} ms".format(
                                        record_update_tstamp, current_tstamp, duration/1000, timeout))
            return True
        
        return False

    ##################################################

    def _hasTimeoutExpired(self, current_tstamp, record_update_tstamp, record_entry_tstamp=None):
        return self._hasCustomTimeoutExpired(self._entryTimeout, current_tstamp, record_update_tstamp, record_entry_tstamp)

    ##################################################

    def _hasSYNTimeoutExpired(self, flags, current_tstamp, record_update_tstamp, record_entry_tstamp=None):
        return "S" in flags and self._synAction == "timeout" and self._hasCustomTimeoutExpired(self._synTimeout_entryTimeout, current_tstamp, record_update_tstamp, record_entry_tstamp)

    ##################################################

    def _retrieveRecordByKey(self, lookup_key, stage):
        index = self._computeNthStageIndex(lookup_key, stage) % self._stageSize
        record = self._hashArrays[stage][index]
        return record

    ##################################################

    def _retrieveRecordByIndex(self, index, stage):
        return self._hashArrays[stage][index]

    ##################################################

    def _insertRecord(self, stage, index, record):

        ## Preferring OLD
        if not self._preferNew:
            if stage < self._numStages - 1:
                if self._hashArrays[stage][index] is not None:
                    return record

        ## record is a tuple of values to be inserted
        evicted_record = self._hashArrays[stage][index]
        self._hashArrays[stage][index] = record
        if self._test:
            self._custom_print("{} table: Insert record into stage {}, index {}".format(self._tab_type.capitalize(), stage, index))
        if evicted_record is None:
            self._numRecords += 1
            self.accountant.setNumRecords(self._numRecords)

        return evicted_record

    ##################################################

    def lookup(self, lookup_key):
        ## Returns: None if record not found, record if found

        if self._test_lookup: self._custom_print("Lookup:: Lookup key is: {}".format(lookup_key))

        for stage in range(self._numStages):
            index = self._computeNthStageIndex(lookup_key, stage) % self._stageSize
            record = self._hashArrays[stage][index]
            if self._test_lookup: self._custom_print("Lookup:: Record retrieved from stage {}, index {} is: {}".format(stage, index, record))
            if record is not None:
                if self._test_lookup: self._custom_print("Lookup:: Record is not NONE")
                record_key = record[0]
                if self._test_lookup: self._custom_print("Lookup:: Record key is {} and lookup key is {}".format(record_key, lookup_key))
                if record_key == lookup_key:
                    if self._test_lookup: self._custom_print("Lookup:: Match; returning record".format(record))
                    return record
        if self._test_lookup: self._custom_print("Lookup:: Unmatched; returning NONE")

        return None

    ##################################################

    def exhaustive_lookup(self, lookup_key):
        ## Returns: None if record not found, record if found

        if self._test_lookup: self._custom_print("Exhaustive Lookup:: Lookup key is: {}".format(lookup_key))

        for index in range(self._stageSize):
            record = self._hashArrays[0][index]
            if record is not None:
                record_key = record[0]
                if record_key == lookup_key:
                    if self._test_lookup: self._custom_print("Exhaustive Lookup:: Match found in stage {}, index {}; returning record: {}".format(
                                                                0, index, record))
                    return record
        
        record = self.lookup(lookup_key)
        if record is not None:
            if self._test_lookup: self._custom_print("Exhaustive Lookup:: Match found after stage 0; returning record: {}".format(record))
            return record

        # for stage in range(self._numStages):
        #     for index in range(self._stageSize):
        #         record = self._hashArrays[stage][index]
        #         if record is not None:
        #             record_key = record[0]
        #             if record_key == lookup_key:
        #                 if self._test_lookup: self._custom_print("Exhaustive Lookup:: Match found in stage {}, index {}; returning record: {}".format(
        #                                                             stage, index, record))
        #                 return record
        
        if self._test_lookup: self._custom_print("Exhaustive Lookup:: Unmatched; returning NONE")

        return None

    ##################################################

    def delete(self, lookup_key, current_tstamp):

        ## Create snapshot (if interval is complete)
        self.accountant.createSnapshot(current_tstamp)

        for stage in range(self._numStages):
            index = self._computeNthStageIndex(lookup_key, stage) % self._stageSize
            record = self._hashArrays[stage][index]
            if record is not None:
                record_key = record[0]
                entry_tstamp = self._extractEvictionAccountingTime(record)
                if record_key == lookup_key:
                    self._hashArrays[stage][index] = None
                    self._accountForEviction(current_tstamp, entry_tstamp, source="delete")
                    self._numRecords -= 1
                    self.accountant.setNumRecords(self._numRecords)
                    return True

        return False

    ##################################################

    def update(self, lookup_key, new_record, current_tstamp):

        ## Create snapshot (if interval is complete)
        self.accountant.createSnapshot(current_tstamp)

        for stage in range(self._numStages):
            index = self._computeNthStageIndex(lookup_key, stage) % self._stageSize
            record = self._hashArrays[stage][index]
            if record is not None:
                record_key = record[0]
                if record_key == lookup_key:
                    self._hashArrays[stage][index] = self._constructUpdatedRecord(record, new_record)
                    return True
                    
        return False
    
    ##################################################

##################################################
