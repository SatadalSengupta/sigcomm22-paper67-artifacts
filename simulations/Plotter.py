import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pickle
import os

##################################################

class Plotter(object):

    ##################################################

    def __init__(self, simulation_dir):

        self._simulation_dir = simulation_dir

        return
    
    ##################################################

    def _custom_print(self, text="", flush=True):
        print(text, flush=flush)

    ##################################################

    def plotPerformanceComparison(self, tcptrace_rtt_samples, p4rtt_rtt_samples, tcptrace_sample_count, p4rtt_sample_count):

        ## Data processing
        sorted_flow_keys = sorted(tcptrace_rtt_samples, key=lambda k: len(tcptrace_rtt_samples[k]))

        ### RTT sample counts
        tcptrace_samples_counts = []
        p4rtt_samples_counts    = []
        missing_flow_keys       = 0
        for flow_key in sorted_flow_keys:
            tcptrace_samples_counts.append(len(tcptrace_rtt_samples[flow_key]))
            if flow_key not in p4rtt_rtt_samples:
                p4rtt_samples_counts.append(0)
                missing_flow_keys += 1
            else:
                p4rtt_samples_counts.append(len(p4rtt_rtt_samples[flow_key]))
        
        comparison_stats = {"tcptrace": {}, "p4rtt": {}}
        for key in comparison_stats:
            comparison_stats[key] = {"avg": 0.0, "p50": 0, "p90": 0, "p95": 0, "p99": 0}
        ## tcptrace
        comparison_stats["tcptrace"]["avg"] = round(tcptrace_sample_count/len(tcptrace_samples_counts), 1)
        comparison_stats["tcptrace"]["p50"] = int(np.percentile(tcptrace_samples_counts, 50))
        comparison_stats["tcptrace"]["p90"] = int(np.percentile(tcptrace_samples_counts, 90))
        comparison_stats["tcptrace"]["p95"] = int(np.percentile(tcptrace_samples_counts, 95))
        comparison_stats["tcptrace"]["p99"] = int(np.percentile(tcptrace_samples_counts, 99))
        ## p4rtt
        comparison_stats["p4rtt"]["avg"] = round(p4rtt_sample_count/len(p4rtt_samples_counts), 1)
        comparison_stats["p4rtt"]["p50"] = int(np.percentile(p4rtt_samples_counts, 50))
        comparison_stats["p4rtt"]["p90"] = int(np.percentile(p4rtt_samples_counts, 90))
        comparison_stats["p4rtt"]["p95"] = int(np.percentile(p4rtt_samples_counts, 95))
        comparison_stats["p4rtt"]["p99"] = int(np.percentile(p4rtt_samples_counts, 99))

        self._custom_print("Comparison:: Missing {} flow keys in P4RTT vs. tcptrace".format(missing_flow_keys))

        ### RTT sample values
        tcptrace_samples = []
        p4rtt_samples    = []
        for flow_key in sorted_flow_keys:
            tcptrace_samples.extend([rtt for (_, rtt) in tcptrace_rtt_samples[flow_key]])
            if flow_key in p4rtt_rtt_samples:
                p4rtt_samples.extend([rtt for (_, rtt) in p4rtt_rtt_samples[flow_key]])

        ## Plot flow sample counts
        plt.figure(figsize=(6,4))
        fmt_str = "{} (avg={}, p50={}, p90={}, p99={})"
        tcptrace_str = fmt_str.format("tcptrace", comparison_stats["tcptrace"]["avg"],
                                        comparison_stats["tcptrace"]["p50"], comparison_stats["tcptrace"]["p90"],
                                        comparison_stats["tcptrace"]["p99"])
        p4rtt_str = fmt_str.format("p4rtt", comparison_stats["p4rtt"]["avg"],
                                        comparison_stats["p4rtt"]["p50"], comparison_stats["p4rtt"]["p90"],
                                        comparison_stats["p4rtt"]["p99"])
        plt.plot(tcptrace_samples_counts, color="r", linestyle="-", label=tcptrace_str)
        plt.plot(p4rtt_samples_counts, alpha=0.3, color="b", linestyle="--", label=p4rtt_str)
        plt.xlabel("Flows")
        plt.ylabel("Sample Count")
        if tcptrace_samples_counts[-1] >= 1000:
            plt.yscale("log")
        plt.legend(loc="upper left")
        plt.title("RTT Samples/Flow (Samples: tcptrace={}, p4rtt={})".format(tcptrace_sample_count, p4rtt_sample_count))
        plt.tight_layout()
        plot_path = os.path.join(self._simulation_dir, "rtt_comparison_samples_per_flow" + ".png")
        plt.savefig(plot_path, dpi=300)
        plt.clf()
        plt.close("all")

        ## Plot CDFs
        plt.figure(figsize=(6,4))
        x1 = np.sort(tcptrace_samples)
        x2 = np.sort(p4rtt_samples)
        cdf_x1 = np.arange(1, len(x1)+1)/len(x1)
        cdf_x2 = np.arange(1, len(x2)+1)/len(x2)
        plt.plot(x1, cdf_x1, color="r", linestyle="-", label="tcptrace_const ({} samples)".format(tcptrace_sample_count))
        plt.plot(x2, cdf_x2, color="b", linestyle="--", label="p4rtt ({} samples)".format(p4rtt_sample_count))
        plt.xlabel("Time (ms)")
        plt.ylabel("CDF")
        plt.xscale("log")
        plt.legend()
        plt.tight_layout()
        plot_path = os.path.join(self._simulation_dir, "rtt_comparison_cdf_only" + ".png")
        plt.savefig(plot_path, dpi=300)
        plt.clf()
        plt.close("all")

        try:
            with open(os.path.join(self._simulation_dir, "rtt_comparison_cdf_data.pickle"), "w") as fp:
                pickle.dump((x1, x2, cdf_x1, cdf_x2), fp)
        except:
            pass

        ## Plot RTT samples
        plt.figure(figsize=(6,4))
        x1 = np.sort(tcptrace_samples)
        x2 = np.sort(p4rtt_samples)
        bins = np.geomspace(10**-3, 10**6, num=10)
        hist_tcptrace = {}
        hist_p4rtt = {}
        hist_tcptrace["counts"], hist_tcptrace["bins"], _ = plt.hist(x1, bins, alpha=0.5, color="r", edgecolor="r", linewidth=2, label="tcptrace_const")
        hist_p4rtt["counts"], hist_p4rtt["bins"], _ = plt.hist(x2, bins, alpha=0.5, color="b", edgecolor="b", linewidth=2, label="p4rtt")
        plt.xlabel("Time (ms)")
        plt.ylabel("No. of RTT samples")
        plt.xscale("log")
        plt.yscale("log")
        plt.legend()

        # self._custom_print()
        # self._custom_print("Histogram tcptrace: {}".format(hist_tcptrace))
        # self._custom_print()
        # self._custom_print("Histogram p4rtt: {}".format(hist_p4rtt))
        # self._custom_print()

        comparison_stats = {"tcptrace": {}, "p4rtt": {}}
        for key in comparison_stats:
            comparison_stats[key] = {"avg": 0.0, "p50": 0, "p90": 0, "p95": 0, "p99": 0}
        ## tcptrace
        comparison_stats["tcptrace"]["avg"] = int(np.mean(tcptrace_samples))
        comparison_stats["tcptrace"]["p50"] = int(np.percentile(tcptrace_samples, 50))
        comparison_stats["tcptrace"]["p90"] = int(np.percentile(tcptrace_samples, 90))
        comparison_stats["tcptrace"]["p95"] = int(np.percentile(tcptrace_samples, 95))
        comparison_stats["tcptrace"]["p99"] = int(np.percentile(tcptrace_samples, 99))
        ## p4rtt
        comparison_stats["p4rtt"]["avg"] = int(np.mean(p4rtt_samples))
        comparison_stats["p4rtt"]["p50"] = int(np.percentile(p4rtt_samples, 50))
        comparison_stats["p4rtt"]["p90"] = int(np.percentile(p4rtt_samples, 90))
        comparison_stats["p4rtt"]["p95"] = int(np.percentile(p4rtt_samples, 95))
        comparison_stats["p4rtt"]["p99"] = int(np.percentile(p4rtt_samples, 99))
        # plt.title("RTT Dist. Comp.; avg: {}/{}/{}%, p50: {}/{}/{}%, p90: {}/{}/{}%, p99: {}/{}/{}%".format(
        #             round(ks_stats[0], 2), round(ks_critical, 2), round(ks_stats[1], 2)))
        plt.title("RTT Dist. Comparison; mean: {}/{}/{}%, \n p50: {}/{}/{}%, p90: {}/{}/{}%, p99: {}/{}/{}%".format(
                    comparison_stats["tcptrace"]["avg"], comparison_stats["p4rtt"]["avg"], 
                    round((comparison_stats["p4rtt"]["avg"] - comparison_stats["tcptrace"]["avg"]) * 100 / comparison_stats["tcptrace"]["avg"], 1),
                    comparison_stats["tcptrace"]["p50"], comparison_stats["p4rtt"]["p50"], 
                    round((comparison_stats["p4rtt"]["p50"] - comparison_stats["tcptrace"]["p50"]) * 100 / comparison_stats["tcptrace"]["p50"], 1),
                    comparison_stats["tcptrace"]["p90"], comparison_stats["p4rtt"]["p90"], 
                    round((comparison_stats["p4rtt"]["p90"] - comparison_stats["tcptrace"]["p90"]) * 100 / comparison_stats["tcptrace"]["p90"], 1),
                    comparison_stats["tcptrace"]["p99"], comparison_stats["p4rtt"]["p99"], 
                    round((comparison_stats["p4rtt"]["p99"] - comparison_stats["tcptrace"]["p99"]) * 100 / comparison_stats["tcptrace"]["p99"], 1)
        ))
        plt.tight_layout()
        plot_path = os.path.join(self._simulation_dir, "rtt_comparison_hist_only" + ".png")
        plt.savefig(plot_path, dpi=300)
        plt.clf()
        plt.close("all")

        plt.figure(figsize=(6,4))
        tcptrace_wts = np.ones_like(x1) / len(x1)
        p4rtt_wts    = np.ones_like(x2) / len(x2)
        a1, b1, _ = plt.hist(x1, weights=tcptrace_wts, bins=bins, alpha=0.5, color="r", edgecolor="r", linewidth=2, label="tcptrace_const")
        a2, b2, _ = plt.hist(x2, weights=p4rtt_wts, bins=bins, alpha=0.5, color="b", edgecolor="b", linewidth=2, label="p4rtt")
        plt.xlabel("RTT (ms)")
        plt.ylabel("Normed. RTT sample count")
        plt.xscale("log")
        plt.yscale("log")
        plt.legend()
        plt.title("Normalized Count of RTT Samples")
        plt.tight_layout()
        plot_path = os.path.join(self._simulation_dir, "rtt_comparison_hist_normalized" + ".png")
        plt.savefig(plot_path, dpi=300)
        plt.clf()
        plt.close("all")

        # self._custom_print()
        # self._custom_print("Normed histogram tcptrace:: Sum Counts: {}, Counts: {}, Bins: {}".format(np.sum(a1), a1, b1))
        # self._custom_print()
        # self._custom_print("Normed histogram p4rtt:: Sum Counts: {}, Counts: {}, Bins: {}".format(np.sum(a2), a2, b2))
        # self._custom_print()

    ##################################################

##################################################
