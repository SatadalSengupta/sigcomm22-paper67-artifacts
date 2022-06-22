# sigcomm22-paper67-artifacts

Dear AEC evaluator, thank you for agreeing to evaluate our paper's artifacts!
Below, you will find the steps to execute our code and reproduce our results (wherever possible).

## Note: Restrictions on Data Sharing

We used a 15 mins. campus trace dataset to perform many of the evaluations in our paper (Figure 6, and Figures 9 through 14).
The access to our campus traces is restricted by the Institutional Review Board (IRB) and the Institutional Review Panel for the use of Administrative Data in Research (PADR).
Unfortunately, this means that we are not allowed to share these traces with anyone who is not an approved signatory on the IRB and PADR applications related to this study.
This also means that we are not allowed to store these network traces anywhere except our institutional servers.
We try to work around this limitation by requesting the AEC evaluator to evaluate our code against a publicly available network trace instead of the 15 mins. campus trace mentioned in our paper.

<!-- ## Data Provided for Artifact Evaluation

We provide the following datasets for the artifact evaluation process:
1. Interception attack trace to reproduce Figure 8: `pcaps/interception_attack_trace.pcap`
2. [A public trace](https://tcpreplay.appneta.com/wiki/captures.html) ([smallFlows.pcap](https://s3.amazonaws.com/tcpreplay-pcap-files/smallFlows.pcap)) in lieu of our 15 mins. campus trace to obtain plots equivalent to Figures 9 through 14: `pcaps/smallFlows.pcap`

We are able to share the interception attack trace because both end-hosts are controlled by us, and as such there is no sensitive information pertaining to any other user on our campus. We choose `smallFlows.pcap` for the other evaluations since it is commonly used to test `tcptrace`, a passive RTT measurement tool (a variant of which is also our baseline). -->

## Instructions to Execute the Tofino Prototype

While we make our P4 code public, the Tofino SDE package required to execute this code is owned by Intel and we are not allowed to share it publicly.
What we do instead, is set up an Amazon AWS EC2 instance with the Tofino packages already built and installed.
In this section of the README, we explain the steps to execute to log in to the EC2 instance, execute our P4 code, and reproduce Figure 8 of our paper.

### Step 1: Logging into the AWS EC2 Instance

1. Copy the SSH key in the HotCRP comments to a text file called `sigcomm22-paper67-aws-key.pem`.

2. Move this file to your system's `.ssh` directory by executing in a terminal:
```
mv sigcomm22-paper67-aws-key.pem ~/.ssh
```

3. Change the file permissions of the SSH key file to one permitted by AWS, by executing in a terminal:
```
chmod 400 ~/.ssh/sigcomm22-paper67-aws-key.pem
```

4. Log into the EC2 instance by executing in a terminal:
```
ssh -i ~/.ssh/sigcomm22-paper67-aws-key.pem ubuntu@ec2-54-82-111-53.compute-1.amazonaws.com
```
You should be logged into the EC2 instance as user `ubuntu` and should be automatically `cd`'d into the directory `~/bf-sde-9.7.0`.

Please reach out to us via HotCRP comments if you face any issues during login and we will try to resolve them immediately.

### Step 2: Checking to see whether other AEC evaluators are active

Since there are multiple AEC evaluators, it is possible that more than one reviewer might try to execute our code at the same time.
This will not work since multiple instances of the Tofino model and the Tofino switch-driver cannot be launched at the same time.
Therefore, it is necessary to check whether other AEC evaluators are active once logged into the EC2.
Please perform both the following steps (1 & 2) to confirm that you are the only AEC evaluator active at the moment.

1. Please execute the following from a terminal inside the EC2 instance:
```
ps -ef | grep run_tofino_model | wc -l
```
If the response is `1`, you are the only active AEC evaluator; please proceed with **Step 3**.
If the response is `2` or more, someone else is actively executing the Tofino processes and you should try later once they are finished.
If they seem to be active for too long (e.g., hours), it is possible that the evaluator forgot to kill the processes once they completed their evaluation; please reach out to them via HotCRP or otherwise in that case.

2. Please execute the following from a terminal inside the EC2 instance:
```
ps -ef | grep run_switchd | wc -l
```
If the response is `1`, you are the only active AEC evaluator.
If the response is `2` or more, someone else is actively executing the Tofino processes and you should try later once they are finished.
If they seem to be active for too long (e.g., hours), it is possible that the evaluator forgot to kill the processes once they completed their evaluation; please reach out to them via HotCRP or otherwise in that case.

### Step 3: Getting acquainted with the code and data

1. We have open-sourced our Tofino prototype's P4 code in this repo. The code is in the `prototype` directory.
We have cloned this repo in the EC2 instance already at `~/sigcomm22-paper67-artifacts`, and the code is up-to-date.
Feel free to execute `cd ~/sigcomm22-paper67-artifacts && git pull` anyway if you wish to ensure that this code is the same as the one in the GitHub repo.

2. We used the 15 mins. campus trace to produce Figure 7 in the paper.
As mentioned before, we are not allowed to share this trace due to IRB and PADR protections.
We request the reviewer to proceed to Figure 8 instead, since we can share the data for it, and it allows for evaluation of our prototype just as Figure 7 would.
<!-- We have instead shared [a public trace](https://tcpreplay.appneta.com/wiki/captures.html) ([smallFlows.pcap](https://s3.amazonaws.com/tcpreplay-pcap-files/smallFlows.pcap)).
The trace is available in the GitHub repo and in the EC2 instance at `~/sigcomm22-paper67-artifacts/pcaps/smallFlows.pcap`.
While Figure 7 can't be exactly reproduced using this dataset, we provide instructions later to produce a figure that emulates the main workflow and features of our prototype. -->

3. The network trace we use to produce Figure 8 in the paper is a trace captured inside our campus.
We initiated a BGP interception attack using the PEERING testbed for this experiment, as described in the paper.
This trace captured communication between a host in our campus and a remote host on the US West Coast.
The attacking host was located in Amsterdam and the attack was initiated sometime during the course of this communication.
We are able to expose this trace to the AEC evaluators because the trace captures communication between hosts *we control*, and not to/from other hosts in our campus network (that data is protected by the IRB and PADR as explained before).
However, using an abundance of caution, we do not wish to publicly share this trace since it still captures *real* user-traffic.
We therefore place this trace locally in the EC2 instance but not in the GitHub repo.
It is located at `~/sigcomm22-paper67-artifacts/pcaps/interception_attack_trace.pcap`.
Please refrain from sharing this trace with anyone due to the reasons stated above.

If you choose to change directories during *Step 3* (to perform `git pull`, etc.), please change back to the SDE directory before the next step by executing `cd ~/bf-sde-9.7.0`.

### Step 4: Executing the Tofino prototype code

1. From inside the `~/bf-sde-9.7.0` directory, execute the following to build the Tofino prototype code:
```
./p4_build.sh -p ~/sigcomm22-paper67-artifacts/prototype/p4rtt_tofino1.p4
```
Wait for the build to finish. It may take a few (usually between 1-4) minutes.
The next few steps will engage a terminal each, so please login from 4 different terminals or use `tmux` to split your terminal.

2. From inside the `~/bf-sde-9.7.0` directory, execute the following to start the Tofino model:
```
./run_tofino_model.sh -p p4rtt_tofino1
```
Wait until you see the message `CLI listening on port 8000`. This terminal will now be engaged &mdash; please move to the next terminal.

3. From inside the `~/bf-sde-9.7.0` directory, execute the following to start the Tofino switch-driver:
```
./run_switchd.sh -p p4rtt_tofino1
```
Wait until you the `bfshell> ` shell has been activated. This terminal will now be engaged &mdash; please move to the next terminal.

<!-- ### Step 5: Replaying the smallFlows trace to generate a graph similar to Figure 7

1. From any directory, execute the following to start capturing the outcoming packets on the virtual interface `veth8`:
```
sudo tcpdump -i veth8 -w ~/sigcomm22-paper67-artifacts/output_traces/direction_rtts.pcap
``` -->

### Step 5: Replaying the interception attack trace through our Tofino prototype

1. From any directory, execute the following to start capturing the outcoming packets on the switch interface `veth8`:
```
sudo tcpdump -i veth8 -w ~/sigcomm22-paper67-artifacts/output_traces/attack_rtts.pcap
```
The output RTT samples from our deployed P4 code will now be saved to this `pcap` file.
This terminal will now be engaged &mdash; please move to the next terminal.

2. From any directory, execute the following to replay the interception attack trace on the switch interface `veth0`:
```
sudo tcpreplay -i veth0 -p 100 ~/sigcomm22-paper67-artifacts/pcaps/interception_attack_trace.pcap
```
Wait until `tcpreplay` has finished executing.

3. Once `tcpreplay` has exited, press `Ctrl+C` in the terminal where `tcpdump` was running.
All the RTT output data is now saved in the `pcap` file `~/sigcomm22-paper67-artifacts/output_traces/attack_rtts.pcap`.

### Step 6: Exit all processes

In order to allow other AEC evaluators to execute our code without issues, please exit the running processes.

1. Please press `Ctrl+C` on the terminal where `run_tofino_model.sh` was running.
Wait until the process has exited.

2. Performing **1** should also kill the process on the terminal where `run_switchd.sh` was running.
Please double-check.

3. Double-check that the `tcpreplay` and `tcpdump` processes have also exited.

### Step 7: Reproduce Figure 8

1. Please execute the following command to generate the interception-attack-detection plot from the saved output trace file `~/sigcomm22-paper67-artifacts/output_traces/attack_rtts.pcap`:
```
python3 ~/sigcomm22-paper67-artifacts/prototype/plot_rtt_samples_interception_attack.py ~/sigcomm22-paper67-artifacts/output_traces/attack_rtts.pcap
```
The resulting plot will be located in `~/sigcomm22-paper67-artifacts/plots/interception_attack_rtts.pdf`.

2. Download the generated plot to your local system to view it by executing:
```
scp -i ~/.ssh/sigcomm22-paper67-aws-key.pem ubuntu@ec2-54-82-111-53.compute-1.amazonaws.com:~/sigcomm22-paper67-artifacts/plots/interception_attack_rtts.pdf <local_system_path>
```

## Instructions to Execute the Simulator

The simulation code is present in `simulations`.
This code can be used to obtain plots equivalent to Figures 9&mdash;14, by feeding `pcaps/smallFlows.pcap` as the input.
The following steps take the evaluator through this process to generating the relevant plots from the network trace file.

### Step 1: Preprocessing network trace data

1. Please ensure that you are logged in to the EC2 instance.
From a terminal, execute the following command to navigate to the correct directory for the simulations:
```
cd ~/sigcomm22-paper67-artifacts/simulations
```

2. Preprocess the network trace by executing the following command on the terminal:
```
python3 -u preprocess_trace.py ../pcaps/smallFlows.pcap intermediate/smallFlows.pickle
```
The pre-processed trace is now saved in the intermediate file `smallFlows.pickle`.
We will use this pre-processed file to run our simulations.

### Step 2: Reproducing figures equivalent to Figures 9&mdash;11

1. Generate all the TCP RTTs from the `smallFlows.pcap` network trace using the `tcptrace` tool by executing the following command:
```
tcptrace -nrlZ --output_dir=intermediate/rtts ../pcaps/smallFlows.pcap > intermediate/tcptrace_nlrZ.txt
```
The RTT samples are written in individual files inside `intermediate/rtts`.

2. 

### Step 3: Reproducing a figure equivalent to Figure 12

1. Please ensure that you are in the `simulations` directory by executing:
```
cd ~/sigcomm22-paper67-artifacts/simulations
```

2. Execute the following command to generate a figure equivalent to Figure 12 in the paper:
```
python3 rtt_analysis_wnwo_handshakes.py
```
The code reports statistics regarding connections and successful handshakes.

3. Download the generated plot to your local system to view it by executing:
```
scp -i ~/.ssh/sigcomm22-paper67-aws-key.pem ubuntu@ec2-54-82-111-53.compute-1.amazonaws.com:~/sigcomm22-paper67-artifacts/plots/figure_12_equivalent.pdf <local_system_path>
```
Please note that in our original 15 mins. campus trace, we see a high number of unsuccessful handshakes due to SYN flooding attempts.
We do not see such a phenomenon in the `smallFlows.pcap` file. As such, the number of unsuccessful handshakes is actually `zero`.
Instead of reporting this on the plot, we report the number of *missing* handshakes, i.e., the number of connections where the handshakes were never seen, because the trace capture started after these handshakes were already complete.
This is for completion.

The main point this figure makes is that the percentage of handshake RTTs is sufficiently low such that we can avoid collecting them without any significant penalty. This holds true even for `smallFlows.pcap` (~8.6% of all RTTs are handshake RTTs).

### Step 4: Reproducing a figure equivalent to Figure 13

### Step 5: Reproducing a figure equivalent to Figure 14


## Cleanup

Please clean up after yourself so that other AEC evaluators can start from scratch, and can perform all the above steps without needing to care about existing files/plots.
We provide the script `cleanup.sh` for this purpose.

1. Please ensure you are in the parent git directory by executing:
```
cd ~/sigcomm22-paper67-artifacts
```

2. Please execute the cleanup script by executing:
```
./cleanup.sh
```