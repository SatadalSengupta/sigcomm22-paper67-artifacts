from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import itertools
import math
import os

##################################################

class Accountant():

    def __init__(self, tab_type, tab_params, test=True):

        self._test = test

        # Populate tab params
        self._test             = test
        self._tab_type         = tab_type
        self._round_number     = tab_params["round_num"]
        self._max_round_number = tab_params["max_round_num"]
        self._total_packets    = tab_params["total_packets"]
        self._numRecords       = 0
        self._stageSize        = tab_params["stage_size"]
        self._numStages        = tab_params["num_stages"]
        self._recirculations   = tab_params["recirculations"]

        # Log total counters
        self._totalOccupancy           = 0
        self._totalPacketsProcessed    = 0
        self._totalSEQPacketsProcessed = 0
        self._totalACKPacketsProcessed = 0
        self._totalPacketsDropped      = 0
        self._totalSEQPacketsDropped   = 0
        self._totalACKPacketsDropped   = 0
        self._totalInsertAttempts      = 0
        self._totalInsertSuccesses     = 0
        self._totalInsertFailures      = 0
        self._totalRecirculations      = 0
        self._totalEvictions           = 0
        self._totalSampled             = 0
        self._totalUpdateAttempts      = 0
        self._totalSEQUpdateAttempts   = 0
        self._totalACKUpdateAttempts   = 0
        self._totalUpdateSuccesses     = 0
        self._totalSEQUpdateSuccesses  = 0
        self._totalACKUpdateSuccesses  = 0
        self._totalUpdateFailures      = 0
        self._totalSEQUpdateFailures   = 0
        self._totalACKUpdateFailures   = 0

        # Log time interval counters
        self._intervalOccupancy        = 0
        self._intervalPacketsProcessed = 0
        self._intervalPacketsDropped   = 0
        self._intervalInsertAttempts   = 0
        self._intervalInsertSuccesses  = 0
        self._intervalInsertFailures   = 0
        self._intervalRecirculations   = 0
        self._intervalEvictions        = 0
        self._intervalSampled          = 0
        self._intervalUpdateAttempts   = 0
        self._intervalUpdateSuccesses  = 0
        self._intervalUpdateFailures   = 0

        # Logging
        ## Path
        self._resultsPath = os.path.join(tab_params["results_path"], tab_type + "_table")
        if not os.path.exists(self._resultsPath):
            os.makedirs(self._resultsPath)
        ## Timing
        self._logInterval       = tab_params["log_interval"] # in ms
        self._firstEntryTime    = None
        self._latestEntryRound  = 0
        self._snapshotTime      = []
        ## Total Rates
        self._snapshots_totalOccupancyRate        = []
        self._snapshots_totalPacketsProcessedRate = []
        self._snapshots_totalPacketsDroppedRate   = []
        self._snapshots_totalInsertAttemptRate    = []
        self._snapshots_totalInsertSuccessRate    = []
        self._snapshots_totalInsertFailureRate    = []
        self._snapshots_totalRecirculationRate    = []
        self._snapshots_totalEvictionRate         = []
        self._snapshots_totalUpdateAttemptRate    = []
        self._snapshots_totalUpdateSuccessRate    = []
        self._snapshots_totalUpdateFailureRate    = []
        ## Interval Rates
        self._snapshots_intervalOccupancyRate        = []
        self._snapshots_intervalPacketsProcessedRate = []
        self._snapshots_intervalPacketsDroppedRate   = []
        self._snapshots_intervalInsertAttemptRate    = []
        self._snapshots_intervalInsertSuccessRate    = []
        self._snapshots_intervalInsertFailureRate    = []
        self._snapshots_intervalRecirculationRate    = []
        self._snapshots_intervalEvictionRate         = []
        self._snapshots_intervalUpdateAttemptRate    = []
        self._snapshots_intervalUpdateSuccessRate    = []
        self._snapshots_intervalUpdateFailureRate    = []
        ## Total Counts
        self._snapshots_totalOccupancyCount           = []
        self._snapshots_totalPacketsProcessedCount    = []
        self._snapshots_totalSEQPacketsProcessedCount = []
        self._snapshots_totalACKPacketsProcessedCount = []
        self._snapshots_totalPacketsDroppedCount      = []
        self._snapshots_totalSEQPacketsDroppedCount   = []
        self._snapshots_totalACKPacketsDroppedCount   = []
        self._snapshots_totalInsertAttemptCount       = []
        self._snapshots_totalInsertSuccessCount       = []
        self._snapshots_totalInsertFailureCount       = []
        self._snapshots_totalRecirculationCount       = []
        self._snapshots_totalEvictionCount            = []
        self._snapshots_totalUpdateAttemptCount       = []
        self._snapshots_totalUpdateSuccessCount       = []
        self._snapshots_totalUpdateFailureCount       = []
        ## Interval Counts
        self._snapshots_intervalOccupancyCount        = []
        self._snapshots_intervalPacketsProcessedCount = []
        self._snapshots_intervalPacketsDroppedCount   = []
        self._snapshots_intervalInsertAttemptCount    = []
        self._snapshots_intervalInsertSuccessCount    = []
        self._snapshots_intervalInsertFailureCount    = []
        self._snapshots_intervalRecirculationCount    = []
        self._snapshots_intervalEvictionCount         = []
        self._snapshots_intervalUpdateAttemptCount    = []
        self._snapshots_intervalUpdateSuccessCount    = []
        self._snapshots_intervalUpdateFailureCount    = []
        ## Distribution Data Points
        self._distribution_validEvictionDuration      = []
        self._distribution_reinsertionDuration        = []
        self._distribution_sampledEvictionDuration    = []

    ##################################################

    def _custom_print(self, text, flush=True):
        print(text, flush=flush)

    ##################################################

    def setNumRecords(self, num_records):
        self._numRecords = num_records

    ##################################################

    def _getTotalOccupancyRate(self):
        return round(self._numRecords * 100 / (self._stageSize * self._numStages), 2)

    ##################################################

    def _getTotalPacketsProcessedRate(self):
        return round(self._totalPacketsProcessed * 100 / self._total_packets, 2)
    
    ##################################################

    def _getTotalPacketsDroppedRate(self):
        return round(self._totalPacketsDropped * 100 / self._totalPacketsProcessed, 2)
    
    ##################################################

    def _getTotalInsertAttemptRate(self):
        return round(self._totalInsertAttempts * 100 / self._totalPacketsProcessed, 2)
    
    ##################################################

    def _getTotalInsertSuccessRate(self):
        return round(self._totalInsertSuccesses * 100 / self._totalInsertAttempts, 2)
    
    ##################################################

    def _getTotalInsertFailureRate(self):
        return round(self._totalInsertFailures * 100 / self._totalInsertAttempts, 2)
    
    ##################################################

    def _getTotalRecirculationRate(self):
        return round( (self._totalRecirculations * 100) / (self._totalInsertAttempts * self._recirculations), 2)

    ##################################################

    def _getTotalEvictionRate(self):
        return round(self._totalEvictions * 100 / self._totalInsertAttempts, 2)

    ##################################################

    def _getTotalUpdateAttemptRate(self):
        return round(self._totalUpdateAttempts * 100 / self._totalPacketsProcessed, 2)

    ##################################################

    def _getTotalUpdateSuccessRate(self):
        return round(self._totalUpdateSuccesses * 100 / self._totalUpdateAttempts, 2)

    ##################################################

    def _getTotalUpdateFailureRate(self):
        return round(self._totalUpdateFailures * 100 / self._totalUpdateAttempts, 2)

    ##################################################

    def _getIntervalOccupancyRate(self):
        if len(self._snapshots_totalOccupancyRate) < 2:
            return self._getTotalOccupancyRate()
        else:
            return self._getTotalOccupancyRate() - self._snapshots_totalOccupancyRate[-2]

    ##################################################

    def _getIntervalPacketsProcessedRate(self):
        return round(self._intervalPacketsProcessed * 100 / self._total_packets, 2)
    
    ##################################################

    def _getIntervalPacketsDroppedRate(self):
        return round(self._intervalPacketsDropped * 100 / self._intervalPacketsProcessed, 2)
    
    ##################################################

    def _getIntervalInsertAttemptRate(self):
        return round(self._intervalInsertAttempts * 100 / self._intervalPacketsProcessed, 2)
    
    ##################################################

    def _getIntervalInsertSuccessRate(self):
        return round(self._intervalInsertSuccesses * 100 / self._intervalInsertAttempts, 2)
    
    ##################################################

    def _getIntervalInsertFailureRate(self):
        return round(self._intervalInsertFailures * 100 / self._intervalInsertAttempts, 2)
    
    ##################################################

    def _getIntervalRecirculationRate(self):
        return round( (self._intervalRecirculations * 100) / (self._intervalInsertAttempts * self._recirculations), 2)

    ##################################################

    def _getIntervalEvictionRate(self):
        return round(self._intervalEvictions * 100 / self._intervalInsertAttempts, 2)

    ##################################################

    def _getIntervalUpdateAttemptRate(self):
        return round(self._intervalUpdateAttempts * 100 / self._intervalPacketsProcessed, 2)

    ##################################################

    def _getIntervalUpdateSuccessRate(self):
        return round(self._intervalUpdateSuccesses * 100 / self._intervalUpdateAttempts, 2)

    ##################################################

    def _getIntervalUpdateFailureRate(self):
        return round(self._intervalUpdateFailures * 100 / self._intervalUpdateAttempts, 2)

    ##################################################

    def accountForProcessing(self, pkt_type="SEQ"):
        self._totalPacketsProcessed += 1
        if pkt_type == "SEQ": self._totalSEQPacketsProcessed += 1
        else: self._totalACKPacketsProcessed += 1
        self._intervalPacketsProcessed += 1

    ##################################################

    def accountForDrop(self, pkt_type="SEQ"):
        self._totalPacketsDropped += 1
        if pkt_type == "SEQ": self._totalSEQPacketsDropped += 1
        else: self._totalACKPacketsDropped += 1
        self._intervalPacketsDropped += 1

    ##################################################

    def accountForRecirculation(self, pkt_type="SEQ"):
        self._totalRecirculations    += 1
        self._intervalRecirculations += 1

    ##################################################

    def accountForDeRecirculation(self, pkt_type="SEQ"):
        self._totalRecirculations    -= 1
        self._intervalRecirculations -= 1

    ##################################################

    def accountForUpdateAttempt(self, pkt_type="SEQ"):
        self._totalUpdateAttempts += 1
        if pkt_type == "SEQ": self._totalSEQUpdateAttempts += 1
        else: self._totalACKUpdateAttempts += 1
        self._intervalUpdateAttempts += 1

    ##################################################

    def accountForUpdateSuccess(self, pkt_type="SEQ"):
        self._totalUpdateSuccesses    += 1
        if pkt_type == "SEQ": self._totalSEQUpdateSuccesses += 1
        else: self._totalACKUpdateSuccesses += 1
        self._intervalUpdateSuccesses += 1

    ##################################################

    def accountForUpdateFailure(self, pkt_type="SEQ"):
        self._totalUpdateFailures     += 1
        if pkt_type == "SEQ": self._totalSEQUpdateFailures  += 1
        else: self._totalACKUpdateFailures  += 1
        self._intervalUpdateFailures  += 1

    ##################################################

    def accountForInsertAttempt(self, pkt_type="SEQ"):
        self._totalInsertAttempts    += 1
        self._intervalInsertAttempts += 1

    ##################################################

    def accountForInsertSuccess(self, pkt_type="SEQ"):
        self._totalInsertSuccesses    += 1
        self._intervalInsertSuccesses += 1

    ##################################################

    def accountForInsertFailure(self, pkt_type="SEQ"):
        self._totalInsertFailures    += 1
        self._intervalInsertFailures += 1

    ##################################################

    def accountForSampling(self, pkt_type="SEQ"):
        self._totalSampled      += 1
        self._intervalSampled   += 1

    ##################################################

    def accountForEviction(self, pkt_type="SEQ"):
        self._totalEvictions    += 1
        self._intervalEvictions += 1

    ##################################################

    def explicitSnapshot(self, latest_tstamp):
        self.createSnapshot(latest_tstamp, True)

    ##################################################

    def createSnapshot(self, t, explicit=False):

        if self._firstEntryTime is None or self._intervalPacketsProcessed == 0:
            return
        
        if self._test:
            self._custom_print("Interval packets: {}, Total packets: {}".format(self._intervalPacketsProcessed, self._totalPacketsProcessed))

        ms_elapsed = (t - self._firstEntryTime)/timedelta(milliseconds=1)
        if len(self._snapshotTime) == 0:
            ms_cutoff  = (self._latestEntryRound + 1) * self._logInterval
        else:
            ms_cutoff  = max(self._snapshotTime[-1] + self._logInterval, (self._latestEntryRound + 1) * self._logInterval)

        # self._custom_print("In createSnapshot:: Entry round: {}; Cutoff: {}, Check for snapshot at time: {} ms".format(self._latestEntryRound, ms_cutoff, ms_elapsed))

        if ms_elapsed >= ms_cutoff or explicit:
            if self._test:
                self._custom_print("Create snapshot check successful:: Entry round: {}; Cutoff: {}, Take snapshot at time: {} ms".format(self._latestEntryRound, ms_cutoff, ms_elapsed))
            ## Record time
            self._snapshotTime.append(ms_elapsed)

            self._totalOccupancy = int(self._numRecords)

            ## Packets Processed
            self._snapshots_totalPacketsProcessedRate.append(self._getTotalPacketsProcessedRate())
            self._snapshots_intervalPacketsProcessedRate.append(self._getIntervalPacketsProcessedRate())
            self._snapshots_totalPacketsProcessedCount.append(self._totalPacketsProcessed)
            self._snapshots_totalSEQPacketsProcessedCount.append(self._totalSEQPacketsProcessed)
            self._snapshots_totalACKPacketsProcessedCount.append(self._totalACKPacketsProcessed)
            self._snapshots_intervalPacketsProcessedCount.append(self._intervalPacketsProcessed)

            ## Packets Dropped
            self._snapshots_totalPacketsDroppedRate.append(self._getTotalPacketsDroppedRate())
            self._snapshots_intervalPacketsDroppedRate.append(self._getIntervalPacketsDroppedRate())
            self._snapshots_totalPacketsDroppedCount.append(self._totalPacketsDropped)
            self._snapshots_totalSEQPacketsDroppedCount.append(self._totalSEQPacketsDropped)
            self._snapshots_totalACKPacketsDroppedCount.append(self._totalACKPacketsDropped)
            self._snapshots_intervalPacketsDroppedCount.append(self._intervalPacketsDropped)

            ## Occupancy
            self._snapshots_totalOccupancyRate.append(self._getTotalOccupancyRate())
            self._snapshots_intervalOccupancyRate.append(self._getIntervalOccupancyRate())
            self._snapshots_totalOccupancyCount.append(self._totalOccupancy)
            self._snapshots_intervalOccupancyCount.append(self._intervalOccupancy)

            ## Insert Attempts, Successes, Failures, Recirculations, Evictions
            ### Totals
            #### Rates
            self._snapshots_totalInsertAttemptRate.append(self._getTotalInsertAttemptRate())
            if self._totalInsertAttempts > 0:
                self._snapshots_totalInsertSuccessRate.append(self._getTotalInsertSuccessRate())
                self._snapshots_totalInsertFailureRate.append(self._getTotalInsertFailureRate())
                self._snapshots_totalRecirculationRate.append(self._getTotalRecirculationRate())
                self._snapshots_totalEvictionRate.append(self._getTotalEvictionRate())
            elif len(self._snapshots_totalInsertSuccessRate) == 0:
                self._snapshots_totalInsertSuccessRate.append(0.0)
                self._snapshots_totalInsertFailureRate.append(0.0)
                self._snapshots_totalRecirculationRate.append(0.0)
                self._snapshots_totalEvictionRate.append(0.0)
            else:
                self._snapshots_totalInsertSuccessRate.append(self._snapshots_totalInsertSuccessRate[-1])
                self._snapshots_totalInsertFailureRate.append(self._snapshots_totalInsertFailureRate[-1])
                self._snapshots_totalRecirculationRate.append(self._snapshots_totalRecirculationRate[-1])
                self._snapshots_totalEvictionRate.append(self._snapshots_totalEvictionRate[-1])
            #### Counts
            self._snapshots_totalInsertAttemptCount.append(self._totalInsertAttempts)
            self._snapshots_totalInsertSuccessCount.append(self._totalInsertSuccesses)
            self._snapshots_totalInsertFailureCount.append(self._totalInsertFailures)
            self._snapshots_totalRecirculationCount.append(self._totalRecirculations)
            self._snapshots_totalEvictionCount.append(self._totalEvictions)

            ### Intervals
            self._snapshots_intervalInsertAttemptRate.append(self._getIntervalInsertAttemptRate())
            if self._intervalInsertAttempts > 0:
                self._snapshots_intervalInsertSuccessRate.append(self._getIntervalInsertSuccessRate())
                self._snapshots_intervalInsertFailureRate.append(self._getIntervalInsertFailureRate())
                self._snapshots_intervalRecirculationRate.append(self._getIntervalRecirculationRate())
                self._snapshots_intervalEvictionRate.append(self._getIntervalEvictionRate())
            elif len(self._snapshots_intervalInsertSuccessRate) == 0:
                self._snapshots_intervalInsertSuccessRate.append(0.0)
                self._snapshots_intervalInsertFailureRate.append(0.0)
                self._snapshots_intervalRecirculationRate.append(0.0)
                self._snapshots_intervalEvictionRate.append(0.0)
            else:
                self._snapshots_intervalInsertSuccessRate.append(self._snapshots_intervalInsertSuccessRate[-1])
                self._snapshots_intervalInsertFailureRate.append(self._snapshots_intervalInsertFailureRate[-1])
                self._snapshots_intervalRecirculationRate.append(self._snapshots_intervalRecirculationRate[-1])
                self._snapshots_intervalEvictionRate.append(self._snapshots_intervalEvictionRate[-1])
            #### Counts
            self._snapshots_intervalInsertAttemptCount.append(self._intervalInsertAttempts)
            self._snapshots_intervalInsertSuccessCount.append(self._intervalInsertSuccesses)
            self._snapshots_intervalInsertFailureCount.append(self._intervalInsertFailures)
            self._snapshots_intervalRecirculationCount.append(self._intervalRecirculations)
            self._snapshots_intervalEvictionCount.append(self._intervalEvictions)

            ## Update Attempts, Successes, Failures
            ### Totals
            #### Rates
            self._snapshots_totalUpdateAttemptRate.append(self._getTotalUpdateAttemptRate())
            if self._totalUpdateAttempts > 0:
                self._snapshots_totalUpdateSuccessRate.append(self._getTotalUpdateSuccessRate())
                self._snapshots_totalUpdateFailureRate.append(self._getTotalUpdateFailureRate())
            elif len(self._snapshots_totalUpdateSuccessRate) == 0:
                self._snapshots_totalUpdateSuccessRate.append(0.0)
                self._snapshots_totalUpdateFailureRate.append(0.0)
            else:
                self._snapshots_totalUpdateSuccessRate.append(self._snapshots_totalUpdateSuccessRate[-1])
                self._snapshots_totalUpdateFailureRate.append(self._snapshots_totalUpdateFailureRate[-1])
            #### Counts
            self._snapshots_totalUpdateAttemptCount.append(self._totalUpdateAttempts)
            self._snapshots_totalUpdateSuccessCount.append(self._totalUpdateSuccesses)
            self._snapshots_totalUpdateFailureCount.append(self._totalUpdateFailures)

            ### Intervals
            #### Rates
            self._snapshots_intervalUpdateAttemptRate.append(self._getIntervalUpdateAttemptRate())
            if self._intervalUpdateAttempts > 0:
                self._snapshots_intervalUpdateSuccessRate.append(self._getIntervalUpdateSuccessRate())
                self._snapshots_intervalUpdateFailureRate.append(self._getIntervalUpdateFailureRate())
            elif len(self._snapshots_intervalUpdateSuccessRate) == 0:
                self._snapshots_intervalUpdateSuccessRate.append(0.0)
                self._snapshots_intervalUpdateFailureRate.append(0.0)
            else:
                self._snapshots_intervalUpdateSuccessRate.append(self._snapshots_intervalUpdateSuccessRate[-1])
                self._snapshots_intervalUpdateFailureRate.append(self._snapshots_intervalUpdateFailureRate[-1])
            #### Counts
            self._snapshots_intervalUpdateAttemptCount.append(self._intervalUpdateAttempts)
            self._snapshots_intervalUpdateSuccessCount.append(self._intervalUpdateSuccesses)
            self._snapshots_intervalUpdateFailureCount.append(self._intervalUpdateFailures)
            
            ## Reset interval counters
            self._intervalOccupancy        = 0
            self._intervalPacketsProcessed = 0
            self._intervalPacketsDropped   = 0
            self._intervalInsertAttempts   = 0
            self._intervalInsertSuccesses  = 0
            self._intervalInsertFailures   = 0
            self._intervalRecirculations   = 0
            self._intervalEvictions        = 0
            self._intervalUpdateAttempts   = 0
            self._intervalUpdateSuccesses  = 0
            self._intervalUpdateFailures   = 0
            
            ## Increment round
            self._latestEntryRound += 1

    ##################################################

    def saveSnapshots(self):

        if not os.path.exists(self._resultsPath):
            os.makedirs(self._resultsPath)
        cumulative_data_path = os.path.join(self._resultsPath, "cumulative_data")
        if not os.path.exists(cumulative_data_path):
            os.makedirs(cumulative_data_path)
        discrete_data_path = os.path.join(self._resultsPath, "discrete_data")
        if not os.path.exists(discrete_data_path):
            os.makedirs(discrete_data_path)
        cumulative_plot_path = os.path.join(self._resultsPath, "cumulative_plot")
        if not os.path.exists(cumulative_plot_path):
            os.makedirs(cumulative_plot_path)
        discrete_plot_path = os.path.join(self._resultsPath, "discrete_plot")
        if not os.path.exists(discrete_plot_path):
            os.makedirs(discrete_plot_path)
        
        ## Cumulative rates
        with open(os.path.join(cumulative_data_path, "cumulative_rate_occupancy.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_totalOccupancyRate)]
            fp.write("\n".join(lines))
        with open(os.path.join(cumulative_data_path, "cumulative_rate_packets_processed.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_totalPacketsProcessedRate)]
            fp.write("\n".join(lines))
        with open(os.path.join(cumulative_data_path, "cumulative_rate_packets_dropped.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_totalPacketsDroppedRate)]
            fp.write("\n".join(lines))
        with open(os.path.join(cumulative_data_path, "cumulative_rate_insert_attempts.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_totalInsertAttemptRate)]
            fp.write("\n".join(lines))
        with open(os.path.join(cumulative_data_path, "cumulative_rate_insert_successes.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_totalInsertSuccessRate)]
            fp.write("\n".join(lines))
        with open(os.path.join(cumulative_data_path, "cumulative_rate_insert_failures.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_totalInsertFailureRate)]
            fp.write("\n".join(lines))
        with open(os.path.join(cumulative_data_path, "cumulative_rate_recirculations.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_totalRecirculationRate)]
            fp.write("\n".join(lines))
        with open(os.path.join(cumulative_data_path, "cumulative_rate_evictions.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_totalEvictionRate)]
            fp.write("\n".join(lines))
        with open(os.path.join(cumulative_data_path, "cumulative_rate_update_attempts.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_totalUpdateAttemptRate)]
            fp.write("\n".join(lines))
        with open(os.path.join(cumulative_data_path, "cumulative_rate_update_successes.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_totalUpdateSuccessRate)]
            fp.write("\n".join(lines))
        with open(os.path.join(cumulative_data_path, "cumulative_rate_update_failures.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_totalUpdateFailureRate)]
            fp.write("\n".join(lines))
        
        ## Discrete rates
        with open(os.path.join(discrete_data_path, "discrete_rate_occupancy.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_intervalOccupancyRate)]
            fp.write("\n".join(lines))
        with open(os.path.join(discrete_data_path, "discrete_rate_packets_processed.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_intervalPacketsProcessedRate)]
            fp.write("\n".join(lines))
        with open(os.path.join(discrete_data_path, "discrete_rate_packets_dropped.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_intervalPacketsDroppedRate)]
            fp.write("\n".join(lines))
        with open(os.path.join(discrete_data_path, "discrete_rate_insert_attempts.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_intervalInsertAttemptRate)]
            fp.write("\n".join(lines))
        with open(os.path.join(discrete_data_path, "discrete_rate_insert_successes.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_intervalInsertSuccessRate)]
            fp.write("\n".join(lines))
        with open(os.path.join(discrete_data_path, "discrete_rate_insert_failures.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_intervalInsertFailureRate)]
            fp.write("\n".join(lines))
        with open(os.path.join(discrete_data_path, "discrete_rate_recirculations.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_intervalRecirculationRate)]
            fp.write("\n".join(lines))
        with open(os.path.join(discrete_data_path, "discrete_rate_evictions.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_intervalEvictionRate)]
            fp.write("\n".join(lines))
        with open(os.path.join(discrete_data_path, "discrete_rate_update_attempts.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_intervalUpdateAttemptRate)]
            fp.write("\n".join(lines))
        with open(os.path.join(discrete_data_path, "discrete_rate_update_successes.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_intervalUpdateSuccessRate)]
            fp.write("\n".join(lines))
        with open(os.path.join(discrete_data_path, "discrete_rate_update_failures.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_intervalUpdateFailureRate)]
            fp.write("\n".join(lines))


        ## Cumulative counts
        with open(os.path.join(cumulative_data_path, "cumulative_count_occupancy.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_totalOccupancyCount)]
            fp.write("\n".join(lines))
        with open(os.path.join(cumulative_data_path, "cumulative_count_packets_processed.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_totalPacketsProcessedCount)]
            fp.write("\n".join(lines))
        with open(os.path.join(cumulative_data_path, "cumulative_count_packets_dropped.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_totalPacketsDroppedCount)]
            fp.write("\n".join(lines))
        with open(os.path.join(cumulative_data_path, "cumulative_count_insert_attempts.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_totalInsertAttemptCount)]
            fp.write("\n".join(lines))
        with open(os.path.join(cumulative_data_path, "cumulative_count_insert_successes.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_totalInsertSuccessCount)]
            fp.write("\n".join(lines))
        with open(os.path.join(cumulative_data_path, "cumulative_count_insert_failures.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_totalInsertFailureCount)]
            fp.write("\n".join(lines))
        with open(os.path.join(cumulative_data_path, "cumulative_count_recirculations.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_totalRecirculationCount)]
            fp.write("\n".join(lines))
        with open(os.path.join(cumulative_data_path, "cumulative_count_evictions.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_totalEvictionCount)]
            fp.write("\n".join(lines))
        with open(os.path.join(cumulative_data_path, "cumulative_count_update_attempts.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_totalUpdateAttemptCount)]
            fp.write("\n".join(lines))
        with open(os.path.join(cumulative_data_path, "cumulative_count_update_successes.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_totalUpdateSuccessCount)]
            fp.write("\n".join(lines))
        with open(os.path.join(cumulative_data_path, "cumulative_count_update_failures.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_totalUpdateFailureCount)]
            fp.write("\n".join(lines))

        ## Discrete counts
        with open(os.path.join(discrete_data_path, "discrete_count_occupancy.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_intervalOccupancyCount)]
            fp.write("\n".join(lines))
        with open(os.path.join(discrete_data_path, "discrete_count_packets_processed.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_intervalPacketsProcessedCount)]
            fp.write("\n".join(lines))
        with open(os.path.join(discrete_data_path, "discrete_count_packets_dropped.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_intervalPacketsDroppedCount)]
            fp.write("\n".join(lines))
        with open(os.path.join(discrete_data_path, "discrete_count_insert_attempts.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_intervalInsertAttemptCount)]
            fp.write("\n".join(lines))
        with open(os.path.join(discrete_data_path, "discrete_count_insert_successes.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_intervalInsertSuccessCount)]
            fp.write("\n".join(lines))
        with open(os.path.join(discrete_data_path, "discrete_count_insert_failures.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_intervalInsertFailureCount)]
            fp.write("\n".join(lines))
        with open(os.path.join(discrete_data_path, "discrete_count_recirculations.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_intervalRecirculationCount)]
            fp.write("\n".join(lines))
        with open(os.path.join(discrete_data_path, "discrete_count_evictions.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_intervalEvictionCount)]
            fp.write("\n".join(lines))
        with open(os.path.join(discrete_data_path, "discrete_count_update_attempts.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_intervalUpdateAttemptCount)]
            fp.write("\n".join(lines))
        with open(os.path.join(discrete_data_path, "discrete_count_update_successes.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_intervalUpdateSuccessCount)]
            fp.write("\n".join(lines))
        with open(os.path.join(discrete_data_path, "discrete_count_update_failures.txt"), "w") as fp:
            lines = ["{},{}".format(t, point) for t, point in zip(self._snapshotTime, self._snapshots_intervalUpdateFailureCount)]
            fp.write("\n".join(lines))
        
        ## Distributions
        with open(os.path.join(cumulative_data_path, "distribution_valid_evictions_duration.txt"), "w") as fp:
            lines = ["{}".format(point) for point in self._distribution_validEvictionDuration]
            fp.write("\n".join(lines))
        with open(os.path.join(cumulative_data_path, "distribution_reinsertions_duration.txt"), "w") as fp:
            lines = ["{}".format(point) for point in self._distribution_reinsertionDuration]
            fp.write("\n".join(lines))

    ##################################################

    def _humanReadableStr(self, n):

        humanReadableSuffix = ["", " K", " M", " B", " T"]
        n = float(n)
        idx = max(0, min(len(humanReadableSuffix)-1, int(math.floor(0 if n == 0 else math.log10(abs(n))/3))))
        rounded_num = round(n / 10**(3*idx), 2)
        if rounded_num % 1 == 0:
            formatted_num = int(rounded_num)
        else:
            formatted_num = rounded_num

        return "{}{}".format(formatted_num, humanReadableSuffix[idx])

    ##################################################

    def _plotMetric(self, y, plot_filename, color, linestyle, title):

        plt.figure(figsize=(6,4))
        time_x = [t/1000 for t in self._snapshotTime]
        plt.plot(time_x, y, color=color, linestyle=linestyle)
        plt.xlabel("Time (sec.)")
        if "rate" in plot_filename:
            plt.ylabel("Rate (%)")
        elif "count" in plot_filename:
            plt.ylabel("Count")
        plt.title(self._tab_type.capitalize() + " Table: " + title)
        plt.tight_layout()
        if "cumulative" in plot_filename:
            plot_path = os.path.join(self._resultsPath, "cumulative_plot", plot_filename + ".png")
        elif "discrete" in plot_filename:
            plot_path = os.path.join(self._resultsPath, "discrete_plot", plot_filename + ".png")
        else:
            plot_path = os.path.join(self._resultsPath, plot_filename + ".png")

        plt.savefig(plot_path, dpi=300)
        plt.clf()
        plt.close("all")

    ##################################################

    def _plotMetricCDF(self, x, plot_filename, color, linestyle, title):
    
        plt.figure(figsize=(6,4))
        x = np.sort(x)
        cdf_y = np.arange(1, len(x)+1)/len(x)
        plt.plot(x, cdf_y, color=color, linestyle=linestyle)
        plt.xlabel("Time (ms)")
        plt.ylabel("CDF")
        plt.xscale("log")
        plt.title(self._tab_type.capitalize() + " Table: " + title.format(len(x)))
        plt.tight_layout()
        if "cumulative" in plot_filename:
            plot_path = os.path.join(self._resultsPath, "cumulative_plot", plot_filename + ".png")
        elif "discrete" in plot_filename:
            plot_path = os.path.join(self._resultsPath, "discrete_plot", plot_filename + ".png")
        else:
            plot_path = os.path.join(self._resultsPath, plot_filename + ".png")

        plt.savefig(plot_path, dpi=300)
        plt.clf()
        plt.close("all")

    ##################################################

    def _plotPacketFate(self):

        ## Cumulative
        sns_colors = itertools.cycle(sns.color_palette("bright"))

        plt.figure(figsize=(6,4))
        time_x = [t/1000 for t in self._snapshotTime]

        ## SEQ Packets Processed/Dropped
        color = next(sns_colors)
        linestyles = itertools.cycle(["-", "--"])
        plt.plot(time_x, self._snapshots_totalSEQPacketsProcessedCount, color=color, alpha=0.5, linestyle=next(linestyles), label="SEQ Packets Processed ({})".format(
                    self._humanReadableStr(self._totalSEQPacketsProcessed)))
        plt.plot(time_x, self._snapshots_totalSEQPacketsDroppedCount, color=color, linestyle=next(linestyles), label="SEQ Packets Dropped ({})".format(
                    self._humanReadableStr(self._totalSEQPacketsDropped)))
        
        ## ACK Packets Processed/Dropped
        color = next(sns_colors)
        linestyles = itertools.cycle(["-", "--"])
        plt.plot(time_x, self._snapshots_totalACKPacketsProcessedCount, color=color, alpha=0.5, linestyle=next(linestyles), label="ACK Packets Processed ({})".format(
                    self._humanReadableStr(self._totalACKPacketsProcessed)))
        plt.plot(time_x, self._snapshots_totalACKPacketsDroppedCount, color=color, linestyle=next(linestyles), label="ACK Packets Dropped ({})".format(
                    self._humanReadableStr(self._totalACKPacketsDropped)))

        ## Insertion Stats
        color = next(sns_colors)
        linestyles = itertools.cycle(["-", "--", ":"])
        plt.plot(time_x, self._snapshots_totalInsertAttemptCount, color=color, alpha=0.5, linestyle=next(linestyles), label="Attempted Insertions ({})".format(
                    self._humanReadableStr(self._totalInsertAttempts)))
        plt.plot(time_x, self._snapshots_totalInsertSuccessCount, color=color, linestyle=next(linestyles), label="Successful Insertions ({})".format(
                    self._humanReadableStr(self._totalInsertSuccesses)))
        # plt.plot(time_x, self._snapshots_totalInsertFailureCount, color=color, linestyle=next(linestyles), label="Failed Insertions ({})".format(
        #             self._humanReadableStr(self._totalInsertFailures)))

        ## Update Stats
        color = next(sns_colors)
        linestyles = itertools.cycle(["-", "--", ":"])
        plt.plot(time_x, self._snapshots_totalUpdateAttemptCount, color=color, alpha=0.5, linestyle=next(linestyles), label="Attempted Updates ({})".format(
                    self._humanReadableStr(self._totalUpdateAttempts)))
        plt.plot(time_x, self._snapshots_totalUpdateSuccessCount, color=color, linestyle=next(linestyles), label="Successful Updates ({})".format(
                    self._humanReadableStr(self._totalUpdateSuccesses)))
        # plt.plot(time_x, self._snapshots_totalUpdateFailureCount, color=color, linestyle=next(linestyles), label="Failed Updates ({})".format(
        #             self._humanReadableStr(self._totalUpdateFailures)))

        # plt.yscale("log")
        plt.xlabel("Time (sec.)")
        plt.ylabel("Count")
        plt.legend(loc="upper left")
        
        plt.title(self._tab_type.capitalize() + " Table: Packet Fate (Cumulative Counts)")
        plt.tight_layout()
        plot_path = os.path.join(self._resultsPath, "cumulative_count_packet_fate.png")
        plt.savefig(plot_path, dpi=300)
        plt.clf()
        plt.close("all")

    ##################################################

    def _plotInsertionStats(self):

        ## Cumulative
        sns_colors = itertools.cycle(sns.color_palette("bright"))
        linestyles = itertools.cycle(["-", "--", "-.", ":"])

        plt.figure(figsize=(6,4))
        time_x = [t/1000 for t in self._snapshotTime]
        plt.plot(time_x, self._snapshots_totalInsertSuccessRate, color=next(sns_colors), alpha=0.5, linestyle=next(linestyles), label="Successful Insertions ({})".format(
                    self._humanReadableStr(self._totalInsertSuccesses)))
        # plt.plot(time_x, self._snapshots_totalInsertFailureRate, color=next(sns_colors), alpha=0.7, linestyle=next(linestyles), label="Failed Insertions ({})".format(
                    # self._humanReadableStr(self._totalInsertFailures)))
        plt.plot(time_x, self._snapshots_totalRecirculationRate, color=next(sns_colors), alpha=0.65, linestyle=next(linestyles), label="Recirculations ({})".format(
                    self._humanReadableStr(self._totalRecirculations)))
        plt.plot(time_x, self._snapshots_totalEvictionRate, color=next(sns_colors), alpha=0.8, linestyle=next(linestyles), label="Valid Evictions ({})".format(
                    self._humanReadableStr(self._totalEvictions)))
        plt.plot(time_x, self._snapshots_totalUpdateSuccessRate, color=next(sns_colors), alpha=0.95, linestyle=next(linestyles), label="Successful Updates ({})".format(
                self._humanReadableStr(self._totalUpdateSuccesses)))
        # plt.plot(time_x, self._snapshots_totalUpdateFailureRate, color=next(sns_colors), alpha=0.7, linestyle=next(linestyles), label="Failed Updates ({})".format(
                    # self._humanReadableStr(self._totalUpdateFailures)))

        plt.xlabel("Time (sec.)")
        plt.ylabel("Rate (%)")
        plt.legend(loc="upper left")
        
        plt.title(self._tab_type.capitalize() + " Table: Insertion and Update Stats (Cumulative Rates)")
        plt.tight_layout()
        plot_path = os.path.join(self._resultsPath, "cumulative_rate_insertion_stats.png")
        plt.savefig(plot_path, dpi=300)
        plt.clf()
        plt.close("all")

    ##################################################

    def _plotDuration(self):

        sns_colors = itertools.cycle(sns.color_palette("bright"))
        linestyles = itertools.cycle(["-", "--", "-.", ":"])

        plt.figure(figsize=(6,4))

        x = np.sort([dur/1000 for dur in self._distribution_validEvictionDuration])
        cdf_y = np.arange(1, len(x)+1)/len(x)
        plt.plot(x, cdf_y, color=next(sns_colors), alpha=0.5, linestyle=next(linestyles), label="Valid Evictions ({})".format(self._humanReadableStr(len(x))))

        x = np.sort([dur/1000 for dur in self._distribution_reinsertionDuration])
        cdf_y = np.arange(1, len(x)+1)/len(x)
        plt.plot(x, cdf_y, color=next(sns_colors), alpha=0.75, linestyle=next(linestyles), label="Reinsertions ({})".format(self._humanReadableStr(len(x))))

        if self._tab_type == "packet":
            x = np.sort([dur/1000 for dur in self._distribution_sampledEvictionDuration])
            cdf_y = np.arange(1, len(x)+1)/len(x)
            plt.plot(x, cdf_y, color=next(sns_colors), alpha=1.0, linestyle=next(linestyles), label="Sampled Evictions ({})".format(self._humanReadableStr(len(x))))

        plt.xlabel("Time (ms)")
        plt.ylabel("CDF")
        plt.xscale("log")
        plt.legend(loc="upper left")
        plt.title(self._tab_type.capitalize() + " Table: Evicted Records Duration CDF")
        plt.tight_layout()
        
        plot_path = os.path.join(self._resultsPath, "cdf_evictions_duration.png")
        plt.savefig(plot_path, dpi=300)
        plt.clf()
        plt.close("all")
    
    ##################################################

    def plotSnapshots(self):

        self._custom_print("Round {}/{}: Plot {} table snapshots...".format(self._round_number, self._max_round_number, self._tab_type))
        
        sns_colors = itertools.cycle(sns.color_palette("bright"))
        linestyles = itertools.cycle(["-"])

        ## Cumulative rates
        self._plotMetric(self._snapshots_totalOccupancyRate, "cumulative_rate_occupancy", next(sns_colors), next(linestyles), "Cumulative Occupancy Rate")
        self._plotMetric(self._snapshots_totalPacketsProcessedRate, "cumulative_rate_packets_processed", next(sns_colors), next(linestyles), "Cumulative Packets Processed Rate")
        self._plotMetric(self._snapshots_totalPacketsDroppedRate, "cumulative_rate_packets_dropped", next(sns_colors), next(linestyles), "Cumulative Packets Dropped Rate")
        self._plotMetric(self._snapshots_totalInsertAttemptRate, "cumulative_rate_insert_attempts", next(sns_colors), next(linestyles), "Cumulative Insertion Attempt Rate")
        self._plotMetric(self._snapshots_totalInsertSuccessRate, "cumulative_rate_insert_successes", next(sns_colors), next(linestyles), "Cumulative Insertion Success Rate")
        self._plotMetric(self._snapshots_totalInsertFailureRate, "cumulative_rate_insert_failures", next(sns_colors), next(linestyles), "Cumulative Insertion Failure Rate")
        self._plotMetric(self._snapshots_totalRecirculationRate, "cumulative_rate_recirculations", next(sns_colors), next(linestyles), "Cumulative Recirculation Rate")
        self._plotMetric(self._snapshots_totalEvictionRate, "cumulative_rate_evictions", next(sns_colors), next(linestyles), "Cumulative Eviction Rate")
        self._plotMetric(self._snapshots_totalUpdateAttemptRate, "cumulative_rate_update_attempts", next(sns_colors), next(linestyles), "Cumulative Update Attempt Rate")
        self._plotMetric(self._snapshots_totalUpdateSuccessRate, "cumulative_rate_update_successes", next(sns_colors), next(linestyles), "Cumulative Update Success Rate")
        self._plotMetric(self._snapshots_totalUpdateFailureRate, "cumulative_rate_update_failures", next(sns_colors), next(linestyles), "Cumulative Update Failure Rate")

        ## Discrete rates
        self._plotMetric(self._snapshots_intervalOccupancyRate, "discrete_rate_occupancy", next(sns_colors), next(linestyles), "Discrete Occupancy Rate")
        self._plotMetric(self._snapshots_intervalPacketsProcessedRate, "discrete_rate_packets_processed", next(sns_colors), next(linestyles), "Discrete Packets Processed Rate")
        self._plotMetric(self._snapshots_intervalPacketsDroppedRate, "discrete_rate_packets_dropped", next(sns_colors), next(linestyles), "Discrete Packets Dropped Rate")
        self._plotMetric(self._snapshots_intervalInsertAttemptRate, "discrete_rate_insert_attempts", next(sns_colors), next(linestyles), "Discrete Insertion Attempt Rate")
        self._plotMetric(self._snapshots_intervalInsertSuccessRate, "discrete_rate_insert_successes", next(sns_colors), next(linestyles), "Discrete Insertion Success Rate")
        self._plotMetric(self._snapshots_intervalInsertFailureRate, "discrete_rate_insert_failures", next(sns_colors), next(linestyles), "Discrete Insertion Failure Rate")
        self._plotMetric(self._snapshots_intervalRecirculationRate, "discrete_rate_recirculations", next(sns_colors), next(linestyles), "Discrete Recirculation Rate")
        self._plotMetric(self._snapshots_intervalEvictionRate, "discrete_rate_evictions", next(sns_colors), next(linestyles), "Discrete Eviction Rate")
        self._plotMetric(self._snapshots_intervalUpdateAttemptRate, "discrete_rate_update_attempts", next(sns_colors), next(linestyles), "Discrete Update Attempt Rate")
        self._plotMetric(self._snapshots_intervalUpdateSuccessRate, "discrete_rate_update_successes", next(sns_colors), next(linestyles), "Discrete Update Success Rate")
        self._plotMetric(self._snapshots_intervalUpdateFailureRate, "discrete_rate_update_failures", next(sns_colors), next(linestyles), "Discrete Update Failure Rate")

        ## Cumulative counts
        self._plotMetric(self._snapshots_totalOccupancyCount, "cumulative_count_occupancy", next(sns_colors), next(linestyles), "Cumulative Occupancy Count")
        self._plotMetric(self._snapshots_totalPacketsProcessedCount, "cumulative_count_packets_processed", next(sns_colors), next(linestyles), "Cumulative Packets Processed Count")
        self._plotMetric(self._snapshots_totalPacketsDroppedCount, "cumulative_count_packets_dropped", next(sns_colors), next(linestyles), "Cumulative Packets Dropped Count")
        self._plotMetric(self._snapshots_totalInsertAttemptCount, "cumulative_count_insert_attempts", next(sns_colors), next(linestyles), "Cumulative Insertion Attempt Count")
        self._plotMetric(self._snapshots_totalInsertSuccessCount, "cumulative_count_insert_successes", next(sns_colors), next(linestyles), "Cumulative Insertion Success Count")
        self._plotMetric(self._snapshots_totalInsertFailureCount, "cumulative_count_insert_failures", next(sns_colors), next(linestyles), "Cumulative Insertion Failure Count")
        self._plotMetric(self._snapshots_totalRecirculationCount, "cumulative_count_recirculations", next(sns_colors), next(linestyles), "Cumulative Recirculation Count")
        self._plotMetric(self._snapshots_totalEvictionCount, "cumulative_count_evictions", next(sns_colors), next(linestyles), "Cumulative Eviction Count")
        self._plotMetric(self._snapshots_totalUpdateAttemptCount, "cumulative_count_update_attempts", next(sns_colors), next(linestyles), "Cumulative Update Attempt Count")
        self._plotMetric(self._snapshots_totalUpdateSuccessCount, "cumulative_count_update_successes", next(sns_colors), next(linestyles), "Cumulative Update Success Count")
        self._plotMetric(self._snapshots_totalUpdateFailureCount, "cumulative_count_update_failures", next(sns_colors), next(linestyles), "Cumulative Update Failure Count")

        ## Discrete counts
        self._plotMetric(self._snapshots_intervalOccupancyCount, "discrete_count_occupancy", next(sns_colors), next(linestyles), "Discrete Occupancy Count")
        self._plotMetric(self._snapshots_intervalPacketsProcessedCount, "discrete_count_packets_processed", next(sns_colors), next(linestyles), "Discrete Packets Processed Count")
        self._plotMetric(self._snapshots_intervalPacketsDroppedCount, "discrete_count_packets_dropped", next(sns_colors), next(linestyles), "Discrete Packets Dropped Count")
        self._plotMetric(self._snapshots_intervalInsertAttemptCount, "discrete_count_insert_attempts", next(sns_colors), next(linestyles), "Discrete Insertion Attempt Count")
        self._plotMetric(self._snapshots_intervalInsertSuccessCount, "discrete_count_insert_successes", next(sns_colors), next(linestyles), "Discrete Insertion Success Count")
        self._plotMetric(self._snapshots_intervalInsertFailureCount, "discrete_count_insert_failures", next(sns_colors), next(linestyles), "Discrete Insertion Failure Count")
        self._plotMetric(self._snapshots_intervalRecirculationCount, "discrete_count_recirculations", next(sns_colors), next(linestyles), "Discrete Recirculation Count")
        self._plotMetric(self._snapshots_intervalEvictionCount, "discrete_count_evictions", next(sns_colors), next(linestyles), "Discrete Eviction Count")
        self._plotMetric(self._snapshots_intervalUpdateAttemptCount, "discrete_count_update_attempts", next(sns_colors), next(linestyles), "Discrete Update Attempt Count")
        self._plotMetric(self._snapshots_intervalUpdateSuccessCount, "discrete_count_update_successes", next(sns_colors), next(linestyles), "Discrete Update Success Count")
        self._plotMetric(self._snapshots_intervalUpdateFailureCount, "discrete_count_update_failures", next(sns_colors), next(linestyles), "Discrete Update Failure Count")
        
        ## Distributions
        dur_ms = [d/1000 for d in self._distribution_validEvictionDuration]
        self._plotMetricCDF(dur_ms, "cdf_cumulative_valid_evictions_duration", next(sns_colors), next(linestyles), "Valid Evictions Duration CDF ({} Samples)")
        dur_ms = [d/1000 for d in self._distribution_reinsertionDuration]
        self._plotMetricCDF(dur_ms, "cdf_cumulative_reinsertion_duration", next(sns_colors), next(linestyles), "Reinsertions Duration CDF ({} Samples)")
        if self._tab_type == "packet":
            dur_ms = [d/1000 for d in self._distribution_sampledEvictionDuration]
            self._plotMetricCDF(dur_ms, "cdf_cumulative_sampled_evictions_duration", next(sns_colors), next(linestyles), "Sampled Evictions Duration CDF ({} Samples)")

        ## Plot custom combinations
        self._plotPacketFate()
        self._plotInsertionStats()
        self._plotDuration()

        return

    ##################################################

    def stateMismatchInfo(self, packets_count):

        if self._tab_type == "flow":
            tab = "FT"
        else:
            tab = "PT"

        if packets_count+1 < self._totalPacketsProcessed:
            self._custom_print("\t Counter mismatch ({}): Simulation processed packets {} < Processed packets {}".format(tab, packets_count+1, self._totalPacketsProcessed))
        if self._totalPacketsProcessed < self._totalOccupancy:
            self._custom_print("\t Counter mismatch ({}): Packets processed {} < Occupancy {}".format(tab, self._totalPacketsProcessed, self._totalOccupancy))
        if self._totalPacketsProcessed < self._totalPacketsDropped:
            self._custom_print("\t Counter mismatch ({}): Packets processed {} < Dropped {}".format(tab, self._totalPacketsProcessed, self._totalPacketsDropped))
        if self._totalPacketsProcessed < self._totalInsertAttempts:
            self._custom_print("\t Counter mismatch ({}): Packets processed {} < Insert attempts {}".format(tab, self._totalPacketsProcessed, self._totalInsertAttempts))
        if self._totalInsertAttempts < self._totalInsertSuccesses:
            self._custom_print("\t Counter mismatch ({}): Insert attempts {} < Insert successes {}".format(tab, self._totalInsertAttempts, self._totalInsertSuccesses))
        if self._totalInsertAttempts < self._totalInsertFailures:
            self._custom_print("\t Counter mismatch ({}): Insert attempts {} < Insert failures {}".format(tab, self._totalInsertAttempts, self._totalInsertFailures))
        if not self._totalInsertAttempts == self._totalInsertSuccesses + self._totalInsertFailures:
            self._custom_print("\t Counter mismatch ({}): Insert attempts {} <> Insert successes {} + Insert failures {}".format(
                    tab, self._totalInsertAttempts, self._totalInsertSuccesses, self._totalInsertFailures))
        if self._totalPacketsProcessed * self._recirculations < self._totalRecirculations:
            self._custom_print("\t Counter mismatch ({}): Packets processed {} * Allowed recirculations {} < Actual recirculations {}".format(
                    tab, self._totalPacketsProcessed, self._recirculations, self._totalRecirculations))
        if self._totalInsertAttempts * self._recirculations < self._totalRecirculations:
            self._custom_print("\t Counter mismatch ({}): Insert attempts {} * Allowed recirculations {} < Actual recirculations {}".format(
                    tab, self._totalInsertAttempts, self._recirculations, self._totalRecirculations))
        if self._totalPacketsProcessed < self._totalUpdateAttempts:
            self._custom_print("\t Counter mismatch ({}): Packets processed {} < Update attempts {}".format(tab, self._totalPacketsProcessed, self._totalUpdateAttempts))
        if self._totalUpdateAttempts < self._totalUpdateSuccesses:
            self._custom_print("\t Counter mismatch ({}): Update attempts {} < Update successes {}".format(tab, self._totalUpdateAttempts, self._totalUpdateSuccesses))
        if self._totalUpdateAttempts < self._totalUpdateFailures:
            self._custom_print("\t Counter mismatch ({}): Update attempts {} < Update failures {}".format(tab, self._totalUpdateAttempts, self._totalUpdateFailures))
        if not self._totalUpdateAttempts == self._totalUpdateSuccesses + self._totalUpdateFailures:
            self._custom_print("\t Counter mismatch ({}): Update attempts {} <> Update successes {} + Update failures {}".format(
                    tab, self._totalUpdateAttempts, self._totalUpdateSuccesses, self._totalUpdateFailures))
    
    ##################################################

    def stateValidationInfo(self, time_elapsed):

        if self._tab_type == "flow":
            tab = "Flow"
        else:
            tab = "Packet"

        accounted_for_count = self._totalPacketsDropped + self._totalInsertSuccesses + self._totalInsertFailures \
                                + self._totalUpdateSuccesses + self._totalUpdateFailures
        if not accounted_for_count == self._totalPacketsProcessed:
            self._custom_print("{} Round {}/{}: {} Table Validation SEQ+ACK FAILED!".format(time_elapsed, self._round_number, self._max_round_number, tab))
            self._custom_print("{} Round {}/{}: Validation (overall) for {} Table: {} Packets; {} Dropped + \
                                {} Insert Successes + {} Insert Failures + {} Update Successes + {} Update Failures = {} Accounted-For".format(
                    time_elapsed, self._round_number, self._max_round_number, tab, self._totalPacketsProcessed,
                    self._totalPacketsDropped, self._totalInsertSuccesses, self._totalInsertFailures,
                    self._totalUpdateSuccesses, self._totalUpdateFailures, accounted_for_count))
        
        accounted_for_count = self._totalSEQPacketsDropped + self._totalInsertSuccesses + self._totalInsertFailures \
                                + self._totalSEQUpdateSuccesses + self._totalSEQUpdateFailures
        if not accounted_for_count == self._totalSEQPacketsProcessed:
            self._custom_print("{} Round {}/{}: {} Table Validation SEQ FAILED!".format(time_elapsed, self._round_number, self._max_round_number, tab))
            self._custom_print("{} Round {}/{}: Validation (SEQ leg) for {} Table: {} Packets; {} Dropped + \
                                {} Insert Successes + {} Insert Failures + {} Update Successes + {} Update Failures = {} Accounted-For".format(
                    time_elapsed, self._round_number, self._max_round_number, tab, self._totalSEQPacketsProcessed,
                    self._totalSEQPacketsDropped, self._totalInsertSuccesses, self._totalInsertFailures,
                    self._totalSEQUpdateSuccesses, self._totalSEQUpdateFailures, accounted_for_count))
        
        accounted_for_count = self._totalACKPacketsDropped + self._totalACKUpdateSuccesses + self._totalACKUpdateFailures
        if not accounted_for_count == self._totalACKPacketsProcessed:
            self._custom_print("{} Round {}/{}: {} Table Validation ACK FAILED!".format(
                                time_elapsed, self._round_number, self._max_round_number, tab))
            self._custom_print("{} Round {}/{}: Validation (ACK leg) for {} Table: {} Packets; {} Dropped + \
                                {} Update Successes + {} Update Failures = {} Accounted-For".format(
                    time_elapsed, self._round_number, self._max_round_number, tab, self._totalACKPacketsProcessed,
                    self._totalACKPacketsDropped, self._totalACKUpdateSuccesses, self._totalACKUpdateFailures,
                    accounted_for_count))


        # accounted_for_count = self._totalPacketsDropped + self._totalInsertSuccesses + self._totalInsertFailures \
        #                         + self._totalUpdateSuccesses + self._totalUpdateFailures
        # if not accounted_for_count == self._totalPacketsProcessed:
        #     self._custom_print("{} Round {}/{}: {} Table Validation SEQ+ACK FAILED!".format(self._time_elapsed(), self._round_number, self._max_round_number, tab))
        #     self._custom_print("{} Round {}/{}: Validation (overall) for {} Table: {} Packets; {} Dropped + \
        #                         {} Insert Successes + {} Insert Failures + {} Update Successes + {} Update Failures = {} Accounted-For".format(
        #             self._time_elapsed(), self._round_number, self._max_round_number, tab, self._totalPacketsProcessed,
        #             self._totalPacketsDropped, self._totalInsertSuccesses, self._totalInsertFailures,
        #             self._totalUpdateSuccesses, self._totalUpdateFailures, accounted_for_count))
        
        # accounted_for_count = self._totalSEQPacketsDropped + self._totalInsertSuccesses + self._totalInsertFailures
        # if not accounted_for_count == self._totalSEQPacketsProcessed:
        #     self._custom_print("{} Round {}/{}: {} Table Validation SEQ FAILED!".format(self._time_elapsed(), self._round_number, self._max_round_number, tab))
        #     self._custom_print("{} Round {}/{}: Validation (SEQ leg) for {} Table: {} Packets; {} Dropped + \
        #                         {} Insert Successes + {} Insert Failures = {} Accounted-For".format(
        #             self._time_elapsed(), self._round_number, self._max_round_number, tab, self._totalSEQPacketsProcessed,
        #             self._totalSEQPacketsDropped, self._totalInsertSuccesses, self._totalInsertFailures,
        #             accounted_for_count))
        
        # accounted_for_count = self._totalACKPacketsDropped + self._totalACKUpdateSuccesses + self._totalACKUpdateFailures
        # if not accounted_for_count == self._totalACKPacketsProcessed:
        #     self._custom_print("{} Round {}/{}: {} Table Validation ACK FAILED!".format(self._time_elapsed(), self._round_number, self._max_round_number, tab))
        #     self._custom_print("{} Round {}/{}: Validation (ACK leg) for {} Table: {} Packets; {} Dropped + \
        #                         {} Update Successes + {} Update Failures = {} Accounted-For\n".format(
        #             self._time_elapsed(), self._round_number, self._max_round_number, tab, self._totalACKPacketsProcessed,
        #             self._totalACKPacketsDropped, self._totalACKUpdateSuccesses, self._totalACKUpdateFailures,
        #             accounted_for_count))