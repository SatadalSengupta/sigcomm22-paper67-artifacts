from logging.LoggerPeriodic import LoggerPeriodic
import os

##################################################

class LoggerCumulative(LoggerPeriodic):

    ##################################################

    def __init__(self, stage_size, num_stages, total_packets):

        LoggerPeriodic.__init__(stage_size, num_stages, total_packets)

    ##################################################

##################################################
