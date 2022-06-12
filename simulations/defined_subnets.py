from ipaddress import IPv4Address, ip_network

##################################################

# Princeton subnets (all specified subnets, both included and excluded)
PU_SNETS     = []
PU_SNETS.append( ip_network("128.112.0.0/16")      )  # 00
PU_SNETS.append( ip_network("140.180.0.0/16")      )  # 01
PU_SNETS.append( ip_network("204.153.48.0/23")     )  # 02
PU_SNETS.append( ip_network("66.180.176.0/24")     )  # 03
PU_SNETS.append( ip_network("66.180.177.0/24")     )  # 04
PU_SNETS.append( ip_network("66.180.180.0/22")     )  # 05
PU_SNETS.append( ip_network("2001:470:10e::/48")   )  # 06
PU_SNETS.append( ip_network("2620:c4::/48")        )  # 07
PU_SNETS.append( ip_network("2604:4540::/32")      )  # 08
PU_SNETS.append( ip_network("192.168.0.0/16")      )  # 09
PU_SNETS.append( ip_network("172.16.0.0/12")       )  # 10
PU_SNETS.append( ip_network("10.0.0.0/8")          )  # 11
PU_SNETS.append( ip_network("fd01:8cc0:5682::/48") )  # 12
PU_SNETS.append( ip_network("140.180.240.0/20")    )  # 13
PU_SNETS.append( ip_network("10.24.0.0/15")        )  # 14
PU_SNETS.append( ip_network("10.8.0.0/15")         )  # 15
PU_SNETS.append( ip_network("192.168.12.0/23")     )  # 16
PU_SNETS.append( ip_network("192.168.0.0/24")      )  # 17
PU_SNETS.append( ip_network("172.17.0.0/16")       )  # 18
PU_SNETS.append( ip_network("fd01:8cc0:5682::/56") )  # 19

# Subnets present in the campus trace
# PU_SNETS[11]: 10.0.0.0/8
# PU_SNETS[15]: 10.8.0.0/15      (as subnet of 11)
# PU_SNETS[14]: 10.24.0.0/15     (as subnet of 11)
# PU_SNETS[13]: 140.180.240.0/20 (as subnet of 01)
# PU_SNETS[01]: 140.180.0.0/16
# PU_SNETS[03]: 66.180.176.0/24
# Some connections with endpoints in (10.8.0.0/15, 10.24.0.0/15) and (66.180.176.0/24)

##################################################

# Princeton subnet categories (relevant to our study)
DEFINED_SUBNETS = {
                    "any"      : [],
                    "wired"    : [ PU_SNETS[1], ],
                    "wireless" : [ PU_SNETS[14], PU_SNETS[15] ],
                    "eduroam"  : [ PU_SNETS[15], ],
                    "visitors" : [ PU_SNETS[14], ]
                  }

##################################################
