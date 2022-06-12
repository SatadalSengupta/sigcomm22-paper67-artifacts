from LoggerDirection import LoggerDirection
from datetime import datetime, timedelta
from ipaddress import IPv4Address
from copy import deepcopy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import itertools
from zlib import crc32
import os, sys

##################################################

def Logger(object):

    ##################################################

    def __init__(self, tab_type, tab_params):

        self._tab_type      = tab_type
        self._total_packets = tab_params["total_packets"]
        self._stage_size    = tab_params["stage_size"]
        self._num_stages    = tab_params["num_stages"]

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

        ## Individual directions
        loggerSEQ = LoggerDirection(self._stage_size, self._num_stages, self._total_packets)
        loggerACK = LoggerDirection(self._stage_size, self._num_stages, self._total_packets)

        ## Distribution Data Points
        self._distribution_validEvictionDuration  = []
        self._distribution_forcedEvictionDuration = []
    
    ##################################################

##################################################