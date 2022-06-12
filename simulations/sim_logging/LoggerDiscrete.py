from logging.LoggerPeriodic import LoggerPeriodic
import os

##################################################

class LoggerDiscrete(LoggerPeriodic):

    ##################################################

    def __init__(self, stage_size, num_stages, total_packets):

        LoggerPeriodic.__init__(stage_size, num_stages, total_packets)

    ##################################################

    def _getTableOccupancyRate(self, len_cumulativeOccupancy, entry_cumulativeOccupancy):

        if len_cumulativeOccupancy < 2:
            return round(self._numRecords * 100 / (self._stageSize * self._numStages), 2)
        else:
            return round(self._numRecords * 100 / (self._stageSize * self._numStages), 2) - entry_cumulativeOccupancy
    
    ##################################################

##################################################
