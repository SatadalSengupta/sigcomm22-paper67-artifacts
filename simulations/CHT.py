# from BitHash import BitHash, ResetBitHash
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

TIMESTAMP_START = datetime(2020, 4, 7, 19, 4, 32, 999476)
TIMESTAMP_END   = datetime(2020, 4, 7, 19, 20, 1, 124583)

def time_abs2rel(ts_abs):
    return int((ts_abs - TIMESTAMP_START)/timedelta(microseconds=1))

def time_rel2abs(ts_rel):
    return TIMESTAMP_START + timedelta(microseconds=ts_rel)

##################################################

class CuckooHashTable(object):

    ##################################################

    def __init__(self, num_stages, max_size, recirculations, prefer_new, log_interval, shouldExpire):

        if num_stages < 1:
            print("Number of stages passed <1, resetting to 1")
        
        if max_size < num_stages:
            print("Max. size passed is less than no. of stages, resetting to no. of stages")
        
        if not max_size % num_stages == 0:
            print("Max. size not a multiple of the no. of stages, proceeding with a lesser size")

        self._numStages      = max(1, num_stages)
        self._maxSize        = max(num_stages, max_size)
        self._arraySize      = self._maxSize // self._numStages
        self._recirculations = recirculations
        self._preferNew      = prefer_new
        self._shouldExpire   = shouldExpire

        self._numRecords = 0
        self._hashArrays = []
        for _ in range(self._numStages):
            self._hashArrays.append([None] * self._arraySize)

        # Total counters
        self._countAttemptedInsertions = 0
        self._countFailedInsertions = 0
        self._countRecirculations = 0
        self._countExpiredRecords = 0

        # Refreshed counters
        self._countRefreshedAttemptedInsertions = 0
        self._countRefreshedFailedInsertions = 0
        self._countRefreshedRecirculations = 0
        self._countRefreshedExpiredRecords = 0

        # Logging
        self._logInterval       = log_interval # in ms
        self._firstEntryTime    = None
        self._latestEntryRound  = 0
        self._occupancyRate     = []
        self._failureRate       = []
        self._recirculationRate = []
        self._insertionRate     = []
        self._expirationRate    = []
    
    ##################################################

    def getOccupancy(self):
        return round(self._numRecords * 100 / (self._arraySize * self._numStages), 2)

    ##################################################

    def getFailureRate(self):
        return round(self._countFailedInsertions * 100 / self._countAttemptedInsertions, 2)

    ##################################################

    def getRecirculationRate(self):
        return round(self._countRecirculations * 100 / self._countAttemptedInsertions, 2)

    ##################################################

    def getInsertionLoad(self):
        return round(self._countAttemptedInsertions * 100 / (self._arraySize * self._numStages), 2)

    ##################################################

    def getExpirationRate(self):
        return round(self._countExpiredRecords * 100 / self._countAttemptedInsertions, 2)

    ##################################################

    def getRefreshedFailureRate(self):
        return round(self._countRefreshedFailedInsertions * 100 / self._countRefreshedAttemptedInsertions, 2)

    ##################################################

    def getRefreshedRecirculationRate(self):
        return round(self._countRefreshedRecirculations * 100 / self._countRefreshedAttemptedInsertions, 2)

    ##################################################

    def getRefreshedInsertionLoad(self):
        return round(self._countRefreshedAttemptedInsertions * 100 / (self._arraySize * self._numStages), 2)

    ##################################################

    def getRefreshedExpirationRate(self):
        return round(self._countRefreshedExpiredRecords * 100 / self._countRefreshedAttemptedInsertions, 2)

    ##################################################

    def __str__(self):

        strings = []
        strings.append("Cuckoo Hash Table:")
        for i, array in enumerate(self._hashArrays):
            strings.append("\tTable {}: {}".format(str(i+1), str(array)))
        
        return "\n".join(strings)

    ##################################################

    def _computeNthStageIndex(self, key, n):

        hash_key = "".join([str(i) for i in key]).encode()
        running_hash = crc32(hash_key)
        # running_hash = hash(hash_key)

        for _ in range(n):
            running_hash = crc32(hash_key, running_hash)
            # running_hash = hash(running_hash)
            
        # print("Hash: {}, Array index: {}".format(running_hash, running_hash % self._arraySize))
        
        return running_hash

    ##################################################

    def _isEmpty(self, stage, index):

        if self._hashArrays[stage][index] is None:
            return True

        return False

    ##################################################

    def _insertRecord(self, stage, index, key, data):

        evicted_record, self._hashArrays[stage][index] = self._hashArrays[stage][index], (key, data)
        if evicted_record is None:
            self._numRecords += 1

        return evicted_record

    ##################################################

    # def _insertPreferNew(self, key, data, expiry_check_arg):

    #     stage = 0
    #     attempts = 0
    #     self._countAttemptedInsertions += 1

    #     if self._shouldExpire((key, data), expiry_check_arg):
    #         self._countExpiredRecords += 1
    #         return True

    #     while attempts < (self._recirculations + 1) * self._numStages:
    #         index = self._computeNthStageIndex(key, stage) % self._arraySize
    #         evicted_record = self._insertRecord(stage, index, key, data)

    #         if evicted_record is None:
    #             return True
            
    #         if self._shouldExpire(evicted_record, expiry_check_arg):
    #             self._countExpiredRecords += 1
    #             return True
            
    #         key, data = evicted_record
    #         stage = (stage + 1) % self._numStages
    #         attempts += 1

    #         if stage == 0 and attempts > 0 and attempts < (self._recirculations + 1) * self._numStages:
    #             self._countRecirculations += 1
        
    #     self._countFailedInsertions += 1

    #     return False

    ##################################################

    def _insertPreferNew(self, key, data, expiry_check_arg):

        stage = 0
        attempts = 0
        recirculations = 0
        self._countAttemptedInsertions += 1

        while attempts < (self._recirculations + 1) * self._numStages:

            # print("START:: Just in")

            if stage == 0 and attempts >= 0 and attempts < (self._recirculations + 1) * self._numStages:

                # print("Stage={}, Attempts={}, Recirculations={}".format(stage, attempts, recirculations))

                if self._shouldExpire((key, data), expiry_check_arg):
                    self._countExpiredRecords += 1
                    # print("Should expire")
                    return True

                if attempts > 0:
                    # print("Recirculating")
                    recirculations += 1
                    self._countRecirculations += 1

            index = self._computeNthStageIndex(key, stage) % self._arraySize
            evicted_record = self._insertRecord(stage, index, key, data)

            if evicted_record is None:
                return True

            key, data = evicted_record
            # print("Evicted:", evicted_record)
            
            stage = (stage + 1) % self._numStages
            attempts += 1

            # print("END:: Stage={}, Attempts={}, Recirculations={}".format(stage, attempts, recirculations))
        
        self._countFailedInsertions += 1

        return False

    ##################################################

    def _insertPreferOld(self, key, data, expiry_check_arg):

        stage = 0
        attempts = 0
        recirculations = 0
        self._countAttemptedInsertions += 1

        while attempts < (self._recirculations + 1) * self._numStages:

            # print("START:: Just in")

            if stage == 0 and attempts >= 0 and attempts < (self._recirculations + 1) * self._numStages:

                # print("Stage={}, Attempts={}, Recirculations={}".format(stage, attempts, recirculations))

                if self._shouldExpire((key, data), expiry_check_arg):
                    self._countExpiredRecords += 1
                    # print("Should expire")
                    return True

                if attempts > 0:
                    # print("Recirculating")
                    recirculations += 1
                    self._countRecirculations += 1

            index = self._computeNthStageIndex(key, stage) % self._arraySize
            if self._hashArrays[stage][index] is None:
                _ = self._insertRecord(stage, index, key, data)
                return True
            
            if stage == self._numStages - 1:
                evicted_record = self._insertRecord(stage, index, key, data)
                key, data = evicted_record
                # print("Evicted:", evicted_record)
            
            stage = (stage + 1) % self._numStages
            attempts += 1

            # print("END:: Stage={}, Attempts={}, Recirculations={}".format(stage, attempts, recirculations))
        
        self._countFailedInsertions += 1

        return False

    ##################################################

    def insert(self, key, data, expiry_check_arg, tstamp):

        if self._firstEntryTime is None:
            self._firstEntryTime = tstamp
        
        self._log(tstamp)

        if self._preferNew:
            return self._insertPreferNew(key, data, expiry_check_arg)
        else:
            # print("Prefer OLD")
            return self._insertPreferOld(key, data, expiry_check_arg)

    ##################################################

    def lookup(self, lookup_key):

        for stage in range(self._numStages):
            index = self._computeNthStageIndex(lookup_key, stage) % self._arraySize
            record = self._hashArrays[stage][index]
            if record is not None:
                key, _ = record
                if key == lookup_key:
                    return record

        return None

    ##################################################

    def update(self, lookup_key, data):

        for stage in range(self._numStages):
            index = self._computeNthStageIndex(lookup_key, stage) % self._arraySize
            record = self._hashArrays[stage][index]
            if record is not None:
                key, _ = record
                if key == lookup_key:
                    self._hashArrays[stage][index] = (key, data)
                    return True

        return False

    ##################################################

    def _log(self, t):

        ms_elapsed = (t - self._firstEntryTime)/timedelta(milliseconds=1)
        ms_cutoff  = (self._latestEntryRound + 1) * self._logInterval
        if ms_elapsed >= ms_cutoff:
            self._insertionRate.append(self.getInsertionLoad())
            self._occupancyRate.append(self.getOccupancy())
            self._failureRate.append(self.getFailureRate())
            self._recirculationRate.append(self.getRecirculationRate())
            self._expirationRate.append(self.getExpirationRate())
            self._latestEntryRound += 1

    ##################################################

    def plot_logs(self, tcptrace_data_paths, label):

        print("\t\t Plot Cuckoo Hash Table stats...", flush=True)
        plt.figure(figsize=(6,4))
        sns_colors = itertools.cycle(sns.color_palette("bright"))
        time_x = [r*self._logInterval/1000 for r in range(self._latestEntryRound)]
        plt.plot(time_x, self._insertionRate, color=next(sns_colors), linestyle="-", label="Insertion Load")
        plt.plot(time_x, self._occupancyRate, color=next(sns_colors), linestyle="--", label="Occupancy")
        plt.plot(time_x, self._failureRate, color=next(sns_colors), linestyle="--", label="Failure Rate")
        plt.plot(time_x, self._recirculationRate, color=next(sns_colors), linestyle="-.", label="Recirculation Rate")
        plt.plot(time_x, self._expirationRate, color=next(sns_colors), linestyle=":", label="Expiration Rate")
        plt.legend()
        plt.xlabel("Time (seconds)")
        plt.ylabel("Rate in %")
        plt.title("Cuckoo Hash Table Stats: {}".format(label))
        plt.tight_layout()
        if not os.path.exists(tcptrace_data_paths["cuckoo_hash_table_stats"]):
            os.makedirs(tcptrace_data_paths["cuckoo_hash_table_stats"])
        plt.savefig(os.path.join(tcptrace_data_paths["cuckoo_hash_table_stats"], "cht_stats__{}.png".format(label.replace(" ", "_").lower())), dpi=300)
        plt.clf()
        plt.close("all")

        return

    ##################################################

##################################################

def test():

    def shouldExpire(record, check):
        if randint(1, 5) == 5:
            return True
        return False
    
    size = 15
    stages = 3
    recirc = 1
    missing = 0
    found = 0 
    
    # Create a hash table with an initially small number of buckets
    c = CuckooHashTable(stages, size, recirc, True, shouldExpire)
    
    # Insert elements
    inserted = 0
    for i in range(size + 5):
        print("Inserting", i+1)
        if c.insert((i+1, "a"), i+1, 0):
            print("Successful")
            inserted += 1
        else:
            print("Failed")
        print(c)
        print()
    # print(c)
    print(c._numRecords, "records inserted\n\n")
        
    # Lookup elements
    for i in range(size + 5):
        record = c.lookup((i+1, "a"))
        if record is None:
            print("Failed to find data for key", (i+1, "a"))
            missing += 1
        else:
            _, data = record
            print("Data is", data, "for key", (i+1, "a"))
            found += 1
    print("There were", missing, "records missing from Cuckoo\n\n")

    # Update elements
    missing = 0
    found = 0
    for i in range(size + 5):
        success = c.update((i+1, "a"), i+101)
        if not success:
            print("Failed to find data for key", (i+1, "a"))
            missing += 1
        else:
            print("Data updated to", i+101, "for key", (i+1, "a"))
            found += 1
    print("There were", missing, "records missing from Cuckoo")
    print(c)

##################################################

def __main():
    test()

##################################################

if __name__ == '__main__':
    __main()

##################################################
