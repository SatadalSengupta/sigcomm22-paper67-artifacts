# sigcomm22-paper67-artifacts

Dear AEC evaluator, thank you for agreeing to evaluate our paper's artifacts!
Below, you will find the steps to execute our code and reproduce our results (wherever possible).

## Note: Restrictions on Data Sharing

We used a 15 mins. campus trace dataset to perform many of the evaluations in our paper.
The access to our campus traces is restricted by the Institutional Review Board (IRB) and the Institutional Review Panel for the use of Administrative Data in Research (PADR).
Unfortunately, this means that we are not allowed to share these traces with anyone who is not an approved signatory on the IRB and PADR applications related to this study.
This also means that we are not allowed to store these network traces anywhere except our institutional servers.
We try to work around this limitation by requesting the AEC evaluator to evaluate our code against a publicly available network trace instead of the 15 mins. campus trace mentioned in our paper.
The following section describes the details.

## Data Provided for Artifact Evaluation

We provide the following datasets for the artifact evaluation process:
1. Interception attack trace to reproduce Figure 8: `pcaps/bgp_attack.pcap`
2. [A public trace](https://tcpreplay.appneta.com/wiki/captures.html) ([smallFlows.pcap](https://s3.amazonaws.com/tcpreplay-pcap-files/smallFlows.pcap)) in lieu of our 15 mins. campus trace to obtain plots equivalent to Figures 9 through 14: `pcaps/smallFlows.pcap`

We are able to share the interception attack trace because both end-hosts are controlled by us, and as such there is no sensitive information pertaining to any other user on our campus. We choose `smallFlows.pcap` for the other evaluations since it is commonly used to test `tcptrace`, a passive RTT measurement tool (a variant of which is also our baseline).

