import enum
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import random
import math
import os

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

def compute_tcptrace_mean_rtt():

    path = "/u/satadals/scratch/trace_04_07_2020"
    path_tcptrace_rtts_all   = os.path.join(path, "tcptrace_rtts_all.txt")

    with open(path_tcptrace_rtts_all) as fp:
        tcptrace_rtts_all   = [int(line.strip()) for line in fp.readlines()]
    
    print(np.mean(tcptrace_rtts_all))

########################################

def plot_tcptrace_comparison():

    path = "/u/satadals/scratch/trace_04_07_2020"
    path_tcptrace_rtts_all   = os.path.join(path, "tcptrace_rtts_all.txt")
    path_tcptrace_rtts_nosyn = os.path.join(path, "tcptrace_rtts_nosyn.txt")
    path_tcptrace_rtts_syn   = os.path.join(path, "tcptrace_rtts_syn.txt")
    path = "/u/satadals/scratch/simulations"
    path_dart_inf_mem_syn   = os.path.join(path, "simulation_batch_026/simulation_round_0/rtt_samples_tcptrace_const.txt")
    path_dart_inf_mem_nosyn = os.path.join(path, "simulation_batch_027/simulation_round_0/rtt_samples_tcptrace_const.txt")

    with open(path_tcptrace_rtts_all) as fp:
        tcptrace_rtts_all   = [int(line.strip()) for line in fp.readlines()]
    with open(path_tcptrace_rtts_nosyn) as fp:
        tcptrace_rtts_nosyn = [int(line.strip()) for line in fp.readlines()]
    with open(path_tcptrace_rtts_syn) as fp:
        tcptrace_rtts_syn   = [int(line.strip()) for line in fp.readlines()]
    with open(path_dart_inf_mem_syn) as fp:
        dart_inf_mem_syn   = [float(line.strip()) for line in fp.readlines()]
    with open(path_dart_inf_mem_nosyn) as fp:
        dart_inf_mem_nosyn = [float(line.strip()) for line in fp.readlines()]
    # with open(path_dart_inf_mem_syn) as fp:
    #     dart_inf_mem_syn   = [int(round(float(line.strip()))) for line in fp.readlines()]
    # with open(path_dart_inf_mem_nosyn) as fp:
    #     dart_inf_mem_nosyn = [int(round(float(line.strip()))) for line in fp.readlines()]

    print("Dart(-SYN): {}".format(len(dart_inf_mem_nosyn)))
    print("Dart(+SYN): {}".format(len(dart_inf_mem_syn)))
    print("tcptrace(-SYN): {}".format(len(tcptrace_rtts_nosyn)))
    print("tcptrace(+SYN): {}".format(len(tcptrace_rtts_all)))
    
    plt.figure(figsize=(12,8))
    x = ["Dart(-SYN)", "tcptrace(-SYN)", "Dart(+SYN)", "tcptrace(+SYN)"]
    y = [round(len(dart_inf_mem_nosyn)/1000000, 2), round(len(tcptrace_rtts_nosyn)/1000000, 2), 
            round(len(dart_inf_mem_syn)/1000000, 2), round(len(tcptrace_rtts_all)/1000000, 2)]
    bars = plt.barh(x, y)
    bars[0].set_color('r')
    bars[2].set_color('r')
    for i, v in enumerate(y):
        plt.text(v, i, str(v)+" M", color='grey', fontweight='bold')
    plt.xlabel("No. of RTT samples (million)")
    plt.ylabel("RTT Tool (+/- handshake RTT)")
    plt.tight_layout()
    # plt.savefig("/u/satadals/scratch/trace_04_07_2020/tcptrace_inf_mem_count.png", format="png", dpi=300)
    plt.savefig("/u/satadals/scratch/trace_04_07_2020/tcptrace_inf_mem_count.pdf", format="pdf", dpi=300)
    plt.close()
    plt.clf()
    print("Plot 1 complete")

    x1 = np.sort(tcptrace_rtts_all)
    x2 = np.sort(tcptrace_rtts_nosyn)
    x3 = np.sort(dart_inf_mem_syn)
    x4 = np.sort(dart_inf_mem_nosyn)

    x1_50p = np.percentile(x1, 50)
    x1_75p = np.percentile(x1, 75)
    x1_99p = np.percentile(x1, 99)
    x2_50p = np.percentile(x2, 50)
    x2_75p = np.percentile(x2, 75)
    x2_99p = np.percentile(x2, 99)
    x3_50p = np.percentile(x3, 50)
    x3_75p = np.percentile(x3, 75)
    x3_99p = np.percentile(x3, 99)
    x4_50p = np.percentile(x4, 50)
    x4_75p = np.percentile(x4, 75)
    x4_99p = np.percentile(x4, 99)

    print("\ntcptrace(+SYN) :: 50p: {}, 75p: {}, 99p: {}".format(x1_50p, x1_75p, x1_99p))
    print("tcptrace(-SYN) :: 50p: {}, 75p: {}, 99p: {}".format(x2_50p, x2_75p, x2_99p))
    print("dart(+SYN) :: 50p: {}, 75p: {}, 99p: {}".format(x3_50p, x3_75p, x3_99p))
    print("dart(-SYN) :: 50p: {}, 75p: {}, 99p: {}\n".format(x4_50p, x4_75p, x4_99p))

    # count_gt_100 = 0
    # count_gt_200 = 0
    # count_gt_1000 = 0
    # count_gt_10000 = 0
    # for x in x1:
    #     if x > 100:
    #         count_gt_100 += 1
    #     if x > 1000:
    #         count_gt_1000 += 1
    #     if x > 10000:
    #         count_gt_10000 += 1
    # print(">100ms: " + str(count_gt_100))
    # print(">1s: " + str(count_gt_1000))
    # print(">10s: " + str(count_gt_10000))

    # with open("sorted_tcptrace_rtts_all.txt", "w") as fp:
    #     fp.write("\n".join([str(r) for r in x1]))
    # with open("sorted_tcptrace_rtts_nosyn.txt", "w") as fp:
    #     fp.write("\n".join([str(r) for r in x2]))
    # with open("sorted_dart_inf_mem_syn.txt", "w") as fp:
    #     fp.write("\n".join([str(r) for r in x3]))
    # with open("sorted_dart_inf_mem_nosyn.txt", "w") as fp:
    #     fp.write("\n".join([str(r) for r in x4]))

    # cutoff = 125
    xlog = True
    ylog = True
    is_cdf = False

    X = [x1, x2, x3, x4]
    Y_cdf  = []
    Y_ccdf = []
    for x in X:
        # filtered_x = [r for r in x if r <= cutoff]
        cdf  = np.arange(1, len(x)+1)/len(x)
        ccdf = [1.0-c for c in cdf]
        # X.append(filtered_x)
        Y_cdf.append(cdf)
        Y_ccdf.append(ccdf)
    print("After CDF/CCDF compute", flush=True)

    cutoff_indices = []
    for j, x in enumerate(X):
        for i, val in enumerate(x):
            if val>=100:
                cutoff_indices.append(i-1)
                print("Crosses 100 at index {} out of {}: {}%\n".format(i+1, len(x), (i+1)*100/len(x)))
                break
    print("Cutoff indices: {}".format(cutoff_indices))

    indices = []
    for j, x in enumerate(X):
        if xlog:
            # idx = np.round(np.logspace(0, math.log10(len(x) - 1), 1000000)).astype(int)
            idx = [i for i in range(cutoff_indices[j], len(x))]
        else:
            idx = np.round(np.linspace(0, len(x) - 1, 100000)).astype(int)
        indices.append(idx)
        # print("Indices len: " + str(len(idx)))
    print("After indices", flush=True)

    X_plot = []
    Y_cdf_plot  = []
    Y_ccdf_plot = []

    for j in range(len(X)):
        x_plot      = [X[j][i] for i in indices[j]]
        y_cdf_plot  = [Y_cdf[j][i] for i in indices[j]]
        y_ccdf_plot = [Y_ccdf[j][i] for i in indices[j]]
        X_plot.append(x_plot)
        Y_cdf_plot.append(y_cdf_plot)
        Y_ccdf_plot.append(y_ccdf_plot)
        print("x: {}, cdf: {}, ccdf: {}".format(x_plot[0], y_cdf_plot[0], y_ccdf_plot[0]))
    
    labels = ["tcptrace(+SYN)", "tcptrace(-SYN)", "Dart(+SYN)", "Dart(-SYN)"]
    linestyles = ["-", "--", "-.", ":"]

    print("Before plotting", flush=True)
    plt.figure(figsize=(12,8))
    if is_cdf:
        for i, (x, y) in enumerate(zip(X_plot, Y_cdf_plot)):
            plt.plot(x, y, linewidth=5, linestyle=linestyles[i], label=labels[i])
    else:
        for i, (x, y) in enumerate(zip(X_plot, Y_ccdf_plot)):
            plt.plot(x, y, linewidth=5, linestyle=linestyles[i], label=labels[i])

    # plt.plot(x1, ccdf_x1, linewidth=5, linestyle="-", label="tcptrace(+SYN)")
    # plt.plot(x2, ccdf_x2, linewidth=5, linestyle="--", label="tcptrace(-SYN)")
    # plt.plot(x3, ccdf_x3, linewidth=5, linestyle="-.", label="Dart(+SYN)")
    # plt.plot(x4, ccdf_x4, linewidth=5, linestyle=":", label="Dart(-SYN)")

    plt.xlabel("Round-Trip Time (ms)")
    if is_cdf:
        plt.ylabel("CDF")
    else:
        plt.ylabel("CCDF (1-CDF)")
    # plt.xlim(0, 125)
    plt.xlim(100, 1000000)
    # plt.ylim(0.00001, 1)

    if xlog:
        plt.xscale("log")
    if ylog:
        plt.yscale("log")
    plt.legend()
    plt.tight_layout()
    # out_path = "/u/satadals/scratch/trace_04_07_2020/tcptrace_inf_mem_dist_cdf_linx_liny_le125.pdf"
    out_path = "/u/satadals/scratch/trace_04_07_2020/tcptrace_inf_mem_dist_cdf_logx_logy_ge100_le1000s.pdf"
    plt.savefig(out_path, format="pdf", dpi=300)
    # plt.savefig("tcptrace_inf_mem.pdf", format="pdf", dpi=300)
    plt.close()
    plt.clf()
    print("Plot 2 complete")

########################################

def main():

    # plot_tcptrace_comparison()
    compute_tcptrace_mean_rtt()

########################################

if __name__ == "__main__":
    main()

########################################
