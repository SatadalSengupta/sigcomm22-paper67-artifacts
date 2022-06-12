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

# ##################################################

# MAX_SEQNUM = 2**32

# ##################################################

# TIMESTAMP_START = datetime(2020, 4, 7, 19, 4, 32, 999476)
# TIMESTAMP_END   = datetime(2020, 4, 7, 19, 20, 1, 124583)

# def time_abs2rel(ts_abs):
#     return int((ts_abs - TIMESTAMP_START)/timedelta(microseconds=1))

# def time_rel2abs(ts_rel):
#     return TIMESTAMP_START + timedelta(microseconds=ts_rel)

# ##################################################

class SynTable(CuckooHashTable):

    ##################################################

    def __init__(self, syntab_params, test=True):

        ## Call parent's __init__() function
        CuckooHashTable.__init__(self, "syn", syntab_params, test)
        print("Round {}/{}: Initialized SYN table".format(self._round_number, self._max_round_number))

    ##################################################

#     def _shouldRecordBeEvicted(self, record_flow_key, record_tstamp, tstamp):
        
#         ## Evict on timeout
#         if self._packetTimeout is not None and tstamp - record_tstamp >= self._packetTimeout:
#             return True
        
#         ## Evict if flow doesn't exist in flow table, or packet not within confidence interval
#         record_flow_key = record_flow_key[:-1]
#         flow_record = flow_table.lookup(record_flow_key)
#         if flow_record is None:
#             duration = int((tstamp - record_tstamp)/timedelta(microseconds=1))
#             self._recordDuration.append(duration)
#             return True
#         _, _, (highest_byte_acked_or_rexmited, _), _ = flow_record
#         _, _, _, _, exp_ack = record_flow_key
#         if exp_ack <= highest_byte_acked_or_rexmited:
#             duration = int((tstamp - record_tstamp)/timedelta(microseconds=1))
#             self._recordDuration.append(duration)
#             return True
        
#         return False

#     ##################################################

#     def _insertRecord(self, stage, index, flow_key, tstamp):

#         evicted_record = self._hashArrays[stage][index]
#         self._hashArrays[stage][index] = (flow_key, tstamp)
#         if evicted_record is None:
#             self._numRecords += 1

#         return evicted_record

#     ##################################################

#     def _insertPreferNew(self, flow_key, tstamp, flow_table):

#         stage = 0
#         attempts = 0
#         recirculations = 0
#         record_flow_key = flow_key
#         record_tstamp = tstamp

#         while attempts < (self._recirculations + 1) * self._numStages:

#             # print("START:: Just in")

#             if stage == 0 and attempts >= 0:

#                 # print("Stage={}, Attempts={}, Recirculations={}".format(stage, attempts, recirculations))

#                 if self._shouldRecordBeEvicted(record_flow_key, record_tstamp, tstamp):
#                     self._totalEvictedRecords += 1
#                     self._intervalEvictedRecords += 1
#                     self._recordDuration.append(tstamp - record_tstamp)
#                     # print("Should expire")
#                     return True

#                 if attempts > 0:
#                     # print("Recirculating")
#                     recirculations += 1
#                     self._totalRecirculations += 1

#             index = self._computeNthStageIndex(flow_key, stage) % self._stageSize
#             evicted_record = self._insertRecord(stage, index, flow_key, tstamp)

#             if evicted_record is None:
#                 return True

#             record_flow_key, record_tstamp = evicted_record
#             # print("Evicted:", evicted_record)
            
#             stage = (stage + 1) % self._numStages
#             attempts += 1

#             # print("END:: Stage={}, Attempts={}, Recirculations={}".format(stage, attempts, recirculations))
        
#         self._totalFailedInsertions += 1

#         return False

#     ##################################################

#     def _insertPreferOld(self, flow_key, tstamp, flow_table):

#         stage = 0
#         attempts = 0
#         recirculations = 0
#         record_flow_key = flow_key
#         record_tstamp = tstamp

#         while attempts < (self._recirculations + 1) * self._numStages:

#             # print("START:: Just in")

#             if stage == 0 and attempts >= 0:

#                 # print("Stage={}, Attempts={}, Recirculations={}".format(stage, attempts, recirculations))

#                 if self._shouldRecordBeEvicted(record_flow_key, record_tstamp, tstamp, flow_table):
#                     self._totalEvictedRecords += 1
#                     self._intervalEvictedRecords += 1
#                     self._recordDuration.append(tstamp - record_tstamp)
#                     # print("Should expire")
#                     return True

#                 if attempts > 0:
#                     # print("Recirculating")
#                     recirculations += 1
#                     self._totalRecirculations += 1

#             index = self._computeNthStageIndex(flow_key, stage) % self._stageSize
#             if self._hashArrays[stage][index] is None:
#                 _ = self._insertRecord(stage, index, flow_key, tstamp)
#                 return True
            
#             if stage == self._numStages - 1:
#                 evicted_record = self._insertRecord(stage, index, flow_key, tstamp)
#                 record_flow_key, record_tstamp = evicted_record
#                 # print("Evicted:", evicted_record)
            
#             stage = (stage + 1) % self._numStages
#             attempts += 1

#             # print("END:: Stage={}, Attempts={}, Recirculations={}".format(stage, attempts, recirculations))
        
#         self._totalFailedInsertions += 1

#         return False

#     ##################################################

#     def insert(self, flow_key, tstamp):

#         if self._firstEntryTime is None:
#             self._firstEntryTime = tstamp
        
#         ## Create snapshot (if interval is complete)
#         self._createSnapshot(tstamp)
        
#         self._totalAttemptedInsertions += 1
#         self._intervalAttemptedInsertions += 1

#         if self._preferNew:
#             return self._insertPreferNew(flow_key, tstamp)
#         else:
#             # print("Prefer OLD")
#             return self._insertPreferOld(flow_key, tstamp)

#     ##################################################

#     def lookup(self, lookup_key):

#         for stage in range(self._numStages):
#             index = self._computeNthStageIndex(lookup_key, stage) % self._arraySize
#             record = self._hashArrays[stage][index]
#             if record is not None:
#                 key, _ = record
#                 if key == lookup_key:
#                     return record

#         return None

#     ##################################################

#     def update(self, lookup_key, data):

#         for stage in range(self._numStages):
#             index = self._computeNthStageIndex(lookup_key, stage) % self._arraySize
#             record = self._hashArrays[stage][index]
#             if record is not None:
#                 key, _ = record
#                 if key == lookup_key:
#                     self._hashArrays[stage][index] = (key, data)
#                     return True

#         return False

#     ##################################################

#     def delete(self, lookup_key):

#         for stage in range(self._numStages):
#             index = self._computeNthStageIndex(lookup_key, stage) % self._stageSize
#             record = self._hashArrays[stage][index]
#             if record is not None:
#                 flow_key, _ = record
#                 if flow_key == lookup_key:
#                     self._hashArrays[stage][index] = None
#                     return True

#         return False

#     ##################################################

# ##################################################
