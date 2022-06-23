import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pickle
import os

########################################

sns.set()
sns.set_style("whitegrid")
font = {'family' : 'serif',
        'size'   : 25}
matplotlib.rc('font', **font)
plt.rc('xtick',labelsize=23)
plt.rc('ytick',labelsize=25)
plt.rc('axes',labelsize=30)
plt.rc('legend',fontsize=23)

########################################

def plot_rtt_samples_comparison():

    path = "/home/ubuntu/sigcomm22-paper67-artifacts/simulations/intermediate"
    path_tcptrace_rtts_all   = os.path.join(path, "tcptrace_rtts_all.pickle")
    path_tcptrace_rtts_nosyn = os.path.join(path, "tcptrace_rtts_nosyn.pickle")
    path = "/home/ubuntu/sigcomm22-paper67-artifacts/simulations/intermediate/dart_simulations_infmem"
    path_dart_inf_mem_syn   = os.path.join(path, "rtt_samples_tcptrace_const_syn.txt")
    path_dart_inf_mem_nosyn = os.path.join(path, "rtt_samples_tcptrace_const_nosyn.txt")

    tcptrace_rtts_all = []
    with open(path_tcptrace_rtts_all, "rb") as fp:
        data = pickle.load(fp)
        for conn_tuple in data:
            for sample in data[conn_tuple]:
                tcptrace_rtts_all.append(sample[1])
    
    tcptrace_rtts_nosyn = []
    with open(path_tcptrace_rtts_nosyn, "rb") as fp:
        data = pickle.load(fp)
        for conn_tuple in data:
            for sample in data[conn_tuple]:
                tcptrace_rtts_nosyn.append(sample[1])

    with open(path_dart_inf_mem_syn) as fp:
        dart_inf_mem_syn   = [float(line.strip()) for line in fp.readlines()]
    with open(path_dart_inf_mem_nosyn) as fp:
        dart_inf_mem_nosyn = [float(line.strip()) for line in fp.readlines()]

    print("tcptrace(+SYN): {}".format(len(tcptrace_rtts_all)))
    print("Dart(+SYN): {}".format(len(dart_inf_mem_syn)))
    print("tcptrace(-SYN): {}".format(len(tcptrace_rtts_nosyn)))
    print("Dart(-SYN): {}".format(len(dart_inf_mem_nosyn)))
    
    plt.figure(figsize=(12,8))
    x = ["Dart(-SYN)", "tcptrace(-SYN)", "Dart(+SYN)", "tcptrace(+SYN)"]
    y = [round(len(dart_inf_mem_nosyn)/1000, 2), round(len(tcptrace_rtts_nosyn)/1000, 2), 
            round(len(dart_inf_mem_syn)/1000, 2), round(len(tcptrace_rtts_all)/1000, 2)]
    bars = plt.barh(x, y)
    bars[0].set_color('r')
    bars[2].set_color('r')
    for i, v in enumerate(y):
        plt.text(v, i, str(v)+" K", color='grey', fontweight='bold')
    plt.xlabel("No. of RTT samples (thousand)")
    plt.ylabel("RTT Tool (+/- handshake RTT)")
    plt.tight_layout()
    plt.savefig("/home/ubuntu/sigcomm22-paper67-artifacts/plots/figure_9_equivalent.pdf", format="pdf", dpi=300)
    plt.close()
    plt.clf()
    print("Plot equivalent to Figure 9 generated.")

    return tcptrace_rtts_all, tcptrace_rtts_nosyn, dart_inf_mem_syn, dart_inf_mem_nosyn

########################################

def plot_rtt_distribution_comparison(tcptrace_rtts_all, tcptrace_rtts_nosyn, dart_inf_mem_syn, dart_inf_mem_nosyn, is_cdf, xlog, ylog):

    x1 = np.sort(tcptrace_rtts_all)
    x2 = np.sort(tcptrace_rtts_nosyn)
    x3 = np.sort(dart_inf_mem_syn)
    x4 = np.sort(dart_inf_mem_nosyn)

    X = [x1, x2, x3, x4]
    Y_cdf  = []
    Y_ccdf = []
    for x in X:
        cdf  = np.arange(1, len(x)+1)/len(x)
        ccdf = [1.0-c for c in cdf]
        Y_cdf.append(cdf)
        Y_ccdf.append(ccdf)

    cutoff_indices = []
    for j, x in enumerate(X):
        for i, val in enumerate(x):
            if val>=100:
                cutoff_indices.append(i-1)
                break

    indices = []
    for j, x in enumerate(X):
        if xlog:
            idx = [i for i in range(cutoff_indices[j], len(x))]
        else:
            idx = np.round(np.linspace(0, len(x) - 1, 100000)).astype(int)
        indices.append(idx)

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
    
    labels = ["tcptrace(+SYN)", "tcptrace(-SYN)", "Dart(+SYN)", "Dart(-SYN)"]
    linestyles = ["-", "--", "-.", ":"]

    plt.figure(figsize=(12,8))
    if is_cdf:
        for i, (x, y) in enumerate(zip(X_plot, Y_cdf_plot)):
            plt.plot(x, y, linewidth=5, linestyle=linestyles[i], label=labels[i])
    else:
        for i, (x, y) in enumerate(zip(X_plot, Y_ccdf_plot)):
            plt.plot(x, y, linewidth=5, linestyle=linestyles[i], label=labels[i])

    plt.xlabel("Round-Trip Time (ms)")
    if is_cdf:
        plt.ylabel("CDF")
        plt.xlim(0, 300)
    else:
        plt.ylabel("CCDF (1-CDF)")
        plt.xlim(100, 10000)

    if xlog:
        plt.xscale("log")
    if ylog:
        plt.yscale("log")
    plt.legend()
    plt.tight_layout()

    if is_cdf:
        out_path = "/home/ubuntu/sigcomm22-paper67-artifacts/plots/figure_10_equivalent.pdf"
    else:
        out_path = "/home/ubuntu/sigcomm22-paper67-artifacts/plots/figure_11_equivalent.pdf"

    plt.savefig(out_path, format="pdf", dpi=300)
    plt.close()
    plt.clf()

    if is_cdf:
        print("Plot equivalent to Figure 10 generated.")
    else:
        print("Plot equivalent to Figure 11 generated.")

########################################

def main():

    tcptrace_rtts_all, tcptrace_rtts_nosyn, dart_inf_mem_syn, dart_inf_mem_nosyn = plot_rtt_samples_comparison()
    plot_rtt_distribution_comparison(tcptrace_rtts_all, tcptrace_rtts_nosyn, dart_inf_mem_syn, dart_inf_mem_nosyn,
                                        is_cdf=True, xlog=False, ylog=False)
    plot_rtt_distribution_comparison(tcptrace_rtts_all, tcptrace_rtts_nosyn, dart_inf_mem_syn, dart_inf_mem_nosyn,
                                        is_cdf=False, xlog=True, ylog=True)

########################################

if __name__ == "__main__":
    main()

########################################
