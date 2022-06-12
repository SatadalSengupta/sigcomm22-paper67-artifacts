import os

##################################################

class LoggerPeriodic(object):

    ##################################################

    def __init__(self, stage_size, num_stages, total_packets):

        self._numRecords    = 0
        self._stageSize     = stage_size
        self._numStages     = num_stages
        self._total_packets = total_packets

        ## Log counters
        self._tableOccupancy   = 0
        self._packetsProcessed = 0
        self._packetsDropped   = 0
        self._insertAttempts   = 0
        self._insertSuccesses  = 0
        self._insertFailures   = 0
        self._recirculations   = 0
        self._evictions        = 0
        self._updateAttempts   = 0
        self._updateSuccesses  = 0
        self._updateFailures   = 0

        ## Rates
        self._snapshots_tableOccupancyRate   = []
        self._snapshots_packetsProcessedRate = []
        self._snapshots_packetsDroppedRate   = []
        self._snapshots_insertAttemptRate    = []
        self._snapshots_insertSuccessRate    = []
        self._snapshots_insertFailureRate    = []
        self._snapshots_recirculationRate    = []
        self._snapshots_evictionRate         = []
        self._snapshots_updateAttemptRate    = []
        self._snapshots_updateSuccessRate    = []
        self._snapshots_updateFailureRate    = []

        ## Counts
        self._snapshots_tableOccupancyCount   = []
        self._snapshots_packetsProcessedCount = []
        self._snapshots_packetsDroppedCount   = []
        self._snapshots_insertAttemptCount    = []
        self._snapshots_insertSuccessCount    = []
        self._snapshots_insertFailureCount    = []
        self._snapshots_recirculationCount    = []
        self._snapshots_evictionCount         = []
        self._snapshots_updateAttemptCount    = []
        self._snapshots_updateSuccessCount    = []
        self._snapshots_updateFailureCount    = []

    ##################################################

    def setNumRecords(self, num_records):
        self._numRecords = num_records

    ##################################################

    def _getTableOccupancyRate(self):
        return round(self._numRecords * 100 / (self._stageSize * self._numStages), 2)

    ##################################################

    def _getPacketsProcessedRate(self):
        return round(self._packetsProcessed * 100 / self._total_packets, 2)
    
    ##################################################

    def _getPacketsDroppedRate(self):
        return round(self._packetsDropped * 100 / self._packetsProcessed, 2)
    
    ##################################################

    def _getInsertAttemptRate(self):
        return round(self._insertAttempts * 100 / self._packetsProcessed, 2)
    
    ##################################################

    def _getInsertSuccessRate(self):
        return round(self._insertSuccesses * 100 / self._insertAttempts, 2)
    
    ##################################################

    def _getInsertFailureRate(self):
        return round(self._insertFailures * 100 / self._insertAttempts, 2)
    
    ##################################################

    def _getRecirculationRate(self):
        return round(self._recirculations * 100 / self._insertAttempts, 2)

    ##################################################

    def _getEvictionRate(self):
        return round(self._evictions * 100 / self._insertAttempts, 2)

    ##################################################

    def _getUpdateAttemptRate(self):
        return round(self._updateAttempts * 100 / self._packetsProcessed, 2)

    ##################################################

    def _getUpdateSuccessRate(self):
        return round(self._updateSuccesses * 100 / self._updateAttempts, 2)

    ##################################################

    def _getUpdateFailureRate(self):
        return round(self._updateFailures * 100 / self._updateAttempts, 2)

    ##################################################

    def _createSnapshot(self, t, explicit=False):

        

##################################################