from LoggerCumulative import LoggerCumulative
from LoggerDiscrete import LoggerDiscrete

##################################################

class LoggerDirection(object):

    ##################################################

    def __init__(self, stage_size, num_stages, total_packets):

        loggerCumulative = LoggerCumulative(stage_size, num_stages, total_packets)
        loggerDiscrete   = LoggerDiscrete(stage_size, num_stages, total_packets)
    
    ##################################################

##################################################
