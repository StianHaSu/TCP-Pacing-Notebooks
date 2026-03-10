from holoviews.plotting.bokeh.styles import font_size
from matplotlib import pyplot as plt
import numpy as np

import json

with open("../graph_config.json", "r") as f:
    graph_config = json.load(f)

def _rtt_to_bdp_plus_queue(rtts, queues, bandwidth):
    result = []

    for i in range(len(rtts)):
        result.append(
            # Bandwidth times rtt in seconds, divided by 8 to get BDP in bytes, divided by MSS
            # Plus the queue size
            ((bandwidth * (rtts[i] / 1000) / 8) / 1448) + queues[i]
        )

    return result



def plot_ssthresh_and_queue_size(queues: list[int], bdp_packets: int, sshtresh: list[int], second_ssthresh: list[int] = None, title: str = None, color: str = "green", save: bool = False):
    fig = plt.figure(figsize=(10, 6))

    plt.scatter(queues, sshtresh, marker='o', color=color, label="Max packets in flight")

    if second_ssthresh is not None:
        plt.plot(queues, second_ssthresh, marker='x', color='yellow', label="Second loss")

    #bdp_and_queue = _rtt_to_bdp_plus_queue(rtts, queues, 50 * (10**6))
    #plt.plot(queues, bdp_and_queue, marker='x', color='red', label='BDP + queue size')

    #optimal_line_x = [queue for queue in queues]
    #optimal_line_y = [ 2*(bdp_packets + x) for x in optimal_line_x ]

    #plt.plot(optimal_line_x, optimal_line_y, color='purple', label="2 * (BDP + queue)")

    plt.xlabel('Queue size (packets)', fontsize=32)
    plt.ylabel('Packets', fontsize=32)
    plt.legend(loc='upper left', fontsize=20)

    #if title is not None:
    #    plt.title(title, fontsize=20)

    plt.grid(True)

    plt.xticks(np.arange(min(queues)-5, max(queues)+5, step=500), fontsize=24)
    plt.yticks(np.arange(0, max(sshtresh) + 1000, step=200), fontsize=24)
    plt.show()

    if save:
        name = "_".join(title.split())
        fig.savefig(name + ".pdf", bbox_inches="tight", pad_inches=0.05)

def plot_ssthresh_w_backoff(queues: list[int], bdp_packets: int, sshtresh: list[int], second_ssthresh: list[int] = None, title: str = None, color: str = "green", save: bool = False, backoff: float = 0.5, show_double_backoff: bool = False):
    fig = plt.figure(figsize=(10, 6))

    plt.scatter(queues, sshtresh, marker='o', color=color, label="First ssthresh after slowstart")

    if second_ssthresh is not None:
        plt.scatter(queues, second_ssthresh, marker='x', color='red', label="Final ssthresh after slowstart")

    #bdp_and_queue = _rtt_to_bdp_plus_queue(rtts, queues, 50 * (10**6))
    #plt.plot(queues, bdp_and_queue, marker='x', color='red', label='BDP + queue size')

    optimal_line_x = [queue for queue in queues]
    optimal_line_y = [ bdp_packets + x for x in optimal_line_x ]
    expected_after_backoff = [2 * backoff * (bdp_packets + x) for x in optimal_line_x]
    expected_after_double_backoff = [backoff * (bdp_packets + x) for x in optimal_line_x]


    #plt.plot(optimal_line_x, optimal_line_y, color='purple', label="BDP + queue")
    plt.plot(optimal_line_x, expected_after_backoff, color='black', label=f"{2 * backoff} * (BDP + queue)")

    if show_double_backoff:
        plt.plot(optimal_line_x, expected_after_double_backoff, color='black', linestyle='--', label=f"{backoff} * (BDP + queue)")

    plt.xlabel('Queue size (packets)', fontsize=28)
    plt.ylabel('Packets', fontsize=28)
    plt.legend(loc='upper left', fontsize=16)

    if title is not None:
        plt.title(title, fontsize=20)

    plt.grid(True)

    plt.xticks(np.arange(min(queues)-5, max(queues)+5, step=25), fontsize=24)
    plt.yticks(np.arange(0, max(sshtresh) + 50, step=50), fontsize=24)
    plt.show()

    if save:
        name = "_".join(title.split())
        fig.savefig(name + ".pdf", bbox_inches="tight", pad_inches=0.05)

def plot_ssthresh_and_queue_size_multiple(queues: list[int],
                                          sshtresh_normal: list[int],
                                          sshtresh_pacing: list[int],
                                          sshtresh_custom: list[int],
                                          algorithm: str,
                                          bdp: int,
                                          title: str,
                                          save: bool = False):
    fig = plt.figure(figsize=(10, 6))

    plt.scatter(queues, sshtresh_normal, marker=graph_config["no_pacing"]["marker"], color=graph_config["no_pacing"]["color"], label=f"{algorithm} no pacing")
    plt.scatter(queues, sshtresh_pacing, marker=graph_config["default_pacing"]["marker"], color=graph_config["default_pacing"]["color"], label=f"{algorithm} default pacing")
    plt.scatter(queues, sshtresh_custom, marker=graph_config["log_pacing"]["marker"], color=graph_config["log_pacing"]["color"], label=f"{algorithm} log2 pacing")

    #bdp_and_queue = _rtt_to_bdp_plus_queue(rtts, queues, 50 * (10**6))
    #plt.plot(queues, bdp_and_queue, marker='x', color='red', label='BDP + queue size')

    optimal_line_x = [queue for queue in range(5, 255, 5)]
    optimal_line_y = [ 2 * (bdp + x) for x in optimal_line_x ]

    plt.plot(optimal_line_x, optimal_line_y, color='purple', label="2 x (BDP + queue)")

    plt.xlabel('Queue size (packets)', fontsize=16)
    plt.ylabel('Packets', fontsize=16)
    plt.legend(loc='upper left')

    plt.grid(True)

    plt.xticks(np.arange(0, 251, step=25))
    plt.yticks(np.arange(0, max(optimal_line_y) + 50, step=50))
    plt.show()

    if save:
        name = "_".join(title.split())
        fig.savefig(name + ".pdf", bbox_inches="tight", pad_inches=0.05)

