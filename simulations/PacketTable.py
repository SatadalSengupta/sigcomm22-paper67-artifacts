# from BitHash import BitHash, ResetBitHash
from CuckooHashTable import CuckooHashTable
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

class PacketTable(CuckooHashTable):

    ##################################################

    def __init__(self, packettab_params, test=True):

        ## Call parent's __init__() function
        CuckooHashTable.__init__(self, "packet", packettab_params, test)
        self._custom_print("Round {}/{}: Initialized packet table".format(self._round_number, self._max_round_number))

    ##################################################

    def _custom_print(self, text, flush=True):
        print(text, flush=flush)

    ##################################################

    def _extractEvictionAccountingTime(self, record):
        return record[1]

    ##################################################

    def _checkForAndHandleEviction(self, record, current_tstamp, flow_table, apxflow_table=None):

        ## Result codes: 0 --> no eviction, 1 --> timeout, 2 --> AFT check fail, 3 --> FT not found, 4 --> FT check fail

        record_packet_key, record_tstamp, _ = record

        if self._test:
            self._custom_print("SEQ PT:: Packet record: {} || Checking record for eviction".format(record_packet_key))
        
        ## Evict on timeout
        if self._hasTimeoutExpired(current_tstamp, record_tstamp):
            if self._test:
                self._custom_print("SEQ PT:: Packet record: {} || Evicted since timeout has expired".format(record_packet_key))
            return 1
        
        record_flow_key = record_packet_key[:-1]

        ## Evict if flow exists in approx. flow table, and packet is not within confidence interval
        if apxflow_table is not None:
            approx_flow_record = apxflow_table.lookup(record_flow_key)
            if approx_flow_record is not None:
                _, (highest_byte_acked_or_rexmited, highest_expected_ack), _, _, _, _ = approx_flow_record
                _, _, _, _, exp_ack = record_packet_key
                if highest_byte_acked_or_rexmited == highest_expected_ack:
                    self._accountForEviction(current_tstamp, record_tstamp)
                    if self._test:
                        self._custom_print("SEQ PT:: AFT action: Packet record: {} || Evicted since interval is closed: {} == {}".format(
                                            record_packet_key, highest_byte_acked_or_rexmited, highest_expected_ack))
                elif exp_ack <= highest_byte_acked_or_rexmited:
                    self._accountForEviction(current_tstamp, record_tstamp)
                    if self._test:
                        self._custom_print("SEQ PT:: AFT action: Packet record: {} || Evicted since expected ACK ({}) <= highest byte ACK/Rx. ({})".format(
                                            record_packet_key, exp_ack, highest_byte_acked_or_rexmited))
                    return 2

        ## Evict if flow doesn't exist in flow table (flow evicted or packet not within confidence interval)
        flow_record = flow_table.lookup(record_flow_key)
        if flow_record is None:
            self._accountForEviction(current_tstamp, record_tstamp)
            if self._test:
                self._custom_print("SEQ PT:: Packet record: {} || Evicted since no corresponding flow record present".format(record_packet_key))
            return 3
        
        _, (highest_byte_acked_or_rexmited, _), _, _, _, _ = flow_record
        _, _, _, _, exp_ack = record_packet_key
        if exp_ack <= highest_byte_acked_or_rexmited:
            self._accountForEviction(current_tstamp, record_tstamp)
            if self._test:
                self._custom_print("SEQ PT:: Packet record: {} || Evicted since expected ACK ({}) <= highest byte ACK/Rx. ({})".format(
                                    record_packet_key, exp_ack, highest_byte_acked_or_rexmited))
            return 4
        
        if self._test:
            self._custom_print("SEQ PT:: Packet record: {} || No reason to evict".format(record_packet_key))

        return 0 #False

    ##################################################

    def _constructUpdatedRecord(self, record, new_record):

        packet_key, _    = record
        _, update_tstamp = new_record
        updated_record = (packet_key, update_tstamp)

        return updated_record
    
    ##################################################

    def _insert(self, record, timestamp, flow_table, apxft_table=None):

        attempts       = 0
        stage          = 0
        recirculations = 0
        original_index = self._computeNthStageIndex(record[0], 0) % self._stageSize

        while attempts < (self._recirculations + 1) * self._numStages:

            if self._test:
                self._custom_print("PT:: Packet record: {} || Start of the loop: Attempts: {}, Stage: {}, Recirculations: {}".format(
                                    record, attempts, stage, recirculations))

            if attempts > 0:
                
                if stage == 0:
                    ## Recirculating right now if AFT not present or doesn't evict
                    if self._test:
                        self._custom_print("SEQ PT:: Packet record: {} || Potential recirculation {}".format(record, recirculations + 1))
                    recirculations += 1
                    self.accountant.accountForRecirculation()
            
                if self._evictionStage == "immediate":
                    ## Check for eviction at each stage of the pipeline
                    if self._test:
                        self._custom_print("SEQ PT:: Packet record: {} || Eviction stage is IMMEDIATE, and stage is {} (should be ALWAYS)".format(record, stage))
                    eviction_code = self._checkForAndHandleEviction(record, timestamp, flow_table, apxft_table)
                    if eviction_code:
                        self.accountant.accountForInsertSuccess()
                        ## Reduce recirculation count if evicted at AFT itself
                        if eviction_code == 2:
                            self.accountant.accountForDeRecirculation()
                        return eviction_code
            
                else:

                    if self._evictionStage == "start" and stage == 0:
                        ## Check for eviction at the beginning of the pipeline
                        if self._test:
                            self._custom_print("SEQ PT:: Packet record: {} || Eviction stage is START, and stage is {} (should be 0)".format(record, stage))
                        eviction_code = self._checkForAndHandleEviction(record, timestamp, flow_table, apxft_table)
                        if eviction_code:
                            self.accountant.accountForInsertSuccess()
                            ## Reduce recirculation count if evicted at AFT itself
                            if eviction_code == 2:
                                self.accountant.accountForDeRecirculation()
                            return eviction_code

                    elif self._evictionStage == "end" and stage == self._numStages - 1:
                        ## Check for eviction at the end of the pipeline
                        if self._test:
                            self._custom_print("SEQ PT:: Packet record: {} || Eviction stage is END, and stage is {} (should be NUM_STAGES-1)".format(record, stage))
                        eviction_code = self._checkForAndHandleEviction(record, timestamp, flow_table, apxft_table)
                        if eviction_code:
                            self.accountant.accountForInsertSuccess()
                            ## Reduce recirculation count if evicted at AFT itself
                            if eviction_code == 2:
                                self.accountant.accountForDeRecirculation()
                            return eviction_code

            index = self._computeNthStageIndex(record[0], stage) % self._stageSize
            if self._test: self._custom_print("SEQ PT:: Packet record: {} || Computed index is {}, Record is right before insertion".format(record, index))
            record = self._insertRecord(stage, index, record)
            if self._test: self._custom_print("SEQ PT:: Packet record: {} || Computed index is {}, Record is just evicted".format(record, index))

            if record is None:
                if self._test:
                    self._custom_print("SEQ PT:: Packet record: {} || Evicted record is NONE, return TRUE".format(record))
                self.accountant.accountForInsertSuccess()
                return 5 # Normal insertion
            
            stage = (stage + 1) % self._numStages
            attempts += 1
        
        if self._test:
            self._custom_print("SEQ PT:: Packet record: {} || Out of the loop without returning, insertion FAILED".format(record))
        self.accountant.accountForInsertFailure()

        ## Insert back last evicted record and evict the fresh record so we don't bias against large RTTs
        self.accountant.accountForRecirculation()
        evicted_record = self._insertRecord(0, original_index, record)
        if self._test:
            self._custom_print("SEQ PT:: Packet record: {} || Reinserted old record at original index {}; evicted original record: {}".format(record, original_index, evicted_record))

        duration = self._getDurationMicrosec(timestamp, self._extractEvictionAccountingTime(record))
        self.accountant._distribution_reinsertionDuration.append(duration)

        return 0 #False

    ##################################################

    def insert(self, record, timestamp, flow_table, apxflow_table=None):

        if self._test:
            self._custom_print("\nPT:: Insert into Packet Table")

        if self.accountant._firstEntryTime is None:
            self.accountant._firstEntryTime = timestamp
        
        self.accountant.accountForInsertAttempt()

        ## Create snapshot (if interval is complete)
        self.accountant.createSnapshot(timestamp)
        
        return self._insert(record, timestamp, flow_table, apxflow_table)

    ##################################################

##################################################
