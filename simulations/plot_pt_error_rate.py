import enum
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import random
import math
import os

########################################

sns.set()
sns.set_style("whitegrid")
font = {'family' : 'serif',
        # 'weight' : 'bold',
        'size'   : 25}
matplotlib.rc('font', **font)
plt.rc('xtick',labelsize=23)
plt.rc('ytick',labelsize=25)
plt.rc('axes',labelsize=30)
plt.rc('legend',fontsize=23)

########################################

def plot_error (x_axis, sim_path, plt_path, x_label, with_abs=False, with_max=False):
    
    error_50p = []
    error_95p = []
    error_99p = []
    error_50p_pct = []
    error_95p_pct = []
    error_99p_pct = []
    error_max     = []
    error_max_pct = []
    loc_error_max = []
    loc_error_max_pct = []

    for i, mem in enumerate(x_axis):

        # print("Process for x-axis value: {}; round {} of {}".format(mem, i+1, len(x_axis)))

        round_path = os.path.join(sim_path, "simulation_round_{}".format(i))
        tcptrace_path = os.path.join(round_path, "rtt_samples_tcptrace_const.txt")
        dart_path = os.path.join(round_path, "rtt_samples_p4rtt.txt")

        # print("Load data")
        with open(tcptrace_path) as fp:
            tcptrace_rtts = [float(line.strip()) for line in fp.readlines()]
        with open(dart_path) as fp:
            dart_rtts     = [float(line.strip()) for line in fp.readlines()]
        
        if with_max:
            # print("Compute max error")
            error_all = []
            error_all_pct = []
            for p in range(5, 96):
                tcptrace_pp = np.percentile(tcptrace_rtts, p)
                dart_pp     = np.percentile(dart_rtts, p)
                diff_pp     = round(tcptrace_pp - dart_pp, 2)
                if with_abs:
                    diff_pp = abs(diff_pp)
                diff_pp_pct = round(diff_pp*100.0/tcptrace_pp, 2)
                error_all.append(diff_pp)
                error_all_pct.append(diff_pp_pct)

            abs_error_all = [abs(e) for e in error_all]
            abs_error_all_pct = [abs(e) for e in error_all_pct]
            idx_abs_err_max = abs_error_all.index(max(abs_error_all))
            idx_abs_err_max_pct = abs_error_all_pct.index(max(abs_error_all_pct))
            error_max.append(error_all[idx_abs_err_max])
            error_max_pct.append(error_all_pct[idx_abs_err_max_pct])
            loc_error_max.append(idx_abs_err_max)
            loc_error_max_pct.append(idx_abs_err_max_pct)
        
        # print("Compute 50p error")
        tcptrace_50p = np.percentile(tcptrace_rtts, 50)
        dart_50p     = np.percentile(dart_rtts, 50)
        diff_50p     = round(tcptrace_50p - dart_50p, 2)
        if with_abs:
            diff_50p = abs(diff_50p)
        diff_50p_pct = round(diff_50p*100.0/tcptrace_50p, 2)
        error_50p.append(diff_50p)
        error_50p_pct.append(diff_50p_pct)

        # print("Compute 95p error")
        tcptrace_95p = np.percentile(tcptrace_rtts, 95)
        dart_95p     = np.percentile(dart_rtts, 95)
        diff_95p     = round(tcptrace_95p - dart_95p, 2)
        if with_abs:
            diff_95p = abs(diff_95p)
        diff_95p_pct = round(diff_95p*100.0/tcptrace_95p, 2)
        error_95p.append(diff_95p)
        error_95p_pct.append(diff_95p_pct)

        # print("Compute 99p error")
        tcptrace_99p = np.percentile(tcptrace_rtts, 99)
        dart_99p     = np.percentile(dart_rtts, 99)
        diff_99p     = round(tcptrace_99p - dart_99p, 2)
        if with_abs:
            diff_99p = abs(diff_99p)
        diff_99p_pct = round(diff_99p*100.0/tcptrace_99p, 2)
        error_99p.append(diff_99p)
        error_99p_pct.append(diff_99p_pct)

    if with_max:
        errors_abs = [error_max, error_50p, error_95p, error_99p]
        errors_pct = [error_max_pct, error_50p_pct, error_95p_pct, error_99p_pct]
    else:
        errors_abs = [error_50p, error_95p, error_99p]
        errors_pct = [error_50p_pct, error_95p_pct, error_99p_pct]
    
    # if with_max:
        # print("\nRaw Error:\nMax: {}\nMax. for p={}\n50p: {}\n95p: {}\n99p: {}\n".format(
            # error_max, loc_error_max, error_50p, error_95p, error_99p))
        # print("Percentage Error:\nMax: {}\nMax. for p={}\n50p: {}\n95p: {}\n99p: {}\n".format(
            # error_max_pct, loc_error_max_pct, error_50p_pct, error_95p_pct, error_99p_pct))
    # else:
        # print("\nRaw Error:\n50p: {}\n95p: {}\n99p: {}\n".format(
            # error_50p, error_95p, error_99p))
        # print("Percentage Error:\n50p: {}\n95p: {}\n99p: {}\n".format(
            # error_50p_pct, error_95p_pct, error_99p_pct))

    if with_max:
        linestyles = ["-", "--", "-.", ":", ]
        labels = ["Max. in [5, 95]th percentile", "50th percentile", "95th percentile", "99th percentile"]
        markers = ["o", "^", "*", "+"]
    else:
        linestyles = ["-", "--", ":"]
        labels = ["50th percentile", "95th percentile", "99th percentile"]
        markers = ["o", "^", "*"]

    plt.figure(figsize=(12,8))
    x = [i for i in range(len(x_axis))]
    for i in range(len(errors_pct)):
        plt.plot(x, errors_pct[i], linewidth=5, linestyle=linestyles[i], label=labels[i], marker=markers[i], markersize=20)
    
    plt.xticks(ticks=x, labels=[str(m) for m in x_axis])

    plt.xlabel(x_label)
    ylbl = "RTT Collection Error (%)"
    if with_abs:
        ylbl = "Absolute RTT Collection Error (%)"
    plt.ylabel(ylbl)

    # plt.ylim(0, 100)

    plt.legend()
    plt.tight_layout()

    plt.savefig(plt_path, format="pdf", dpi=300)

    plt.close()
    plt.clf()

########################################

def plot_memory_comparison():

    print("Plot error rate vs. memory\n")
    sim_path = "/home/ubuntu/sigcomm22-paper67-artifacts/simulations/intermediate/dart_simulations/simulation_batch_000"
    plt_path = "/home/ubuntu/sigcomm22-paper67-artifacts/plots/figure_13_equivalent.pdf"
    x_axis   = [1024, 2048, 4096, 8192, 16384, 32768, 65536]
    x_label  = "PT Table Memory Size"
    plot_error(x_axis, sim_path, plt_path, x_label, with_abs=False, with_max=True)
    print("Plot equivalent to Figure 13 generated.")

########################################

def plot_stages_comparison():

    print("\nPlot error rate vs. no. of stages\n")
    sim_path = "/u/satadals/scratch/simulations/simulation_batch_030"
    plt_path = "/u/satadals/scratch/trace_04_07_2020/pt_table_stages{}{}.{}"
    x_axis   = [1, 2, 3, 4, 5, 6, 7, 8]
    x_label  = "No. of Stages in PT Table"
    plot_error(x_axis, sim_path, plt_path, x_label, with_abs=False, with_max=True)
    print("Plot equivalent to Figure 14 generated.")

########################################

def main():

    plot_memory_comparison()
    # plot_stages_comparison()

########################################

if __name__ == "__main__":
    main()

########################################