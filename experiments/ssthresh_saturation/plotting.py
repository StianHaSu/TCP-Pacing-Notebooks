from matplotlib import pyplot as plt
import numpy as np

def _rtt_to_bdp_plus_queue(rtts, queues, bandwidth):
    result = []

    for i in range(len(rtts)):
        result.append(
            # Bandwidth times rtt in seconds, divided by 8 to get BDP in bytes, divided by MSS
            # Plus the queue size
            ((bandwidth * (rtts[i] / 1000) / 8) / 1448) + queues[i]
        )

    return result


def plot_ssthresh_and_queue_size(queues: list[int], sshtresh: list[int], rtts: list[int], cwnds):
    plt.plot(queues, sshtresh, marker='+', color='black', label="Measured")

    #bdp_and_queue = _rtt_to_bdp_plus_queue(rtts, queues, 50 * (10**6))
    #plt.plot(queues, bdp_and_queue, marker='x', color='red', label='BDP + queue size')

    optimal_line_x = [x for x in range(5, 255, 5)]
    optimal_line_y = [ 129 + x for x in optimal_line_x ]

    plt.plot(optimal_line_x, optimal_line_y, color='purple')

    plt.xlabel('Queue size')
    plt.ylabel('SSThresh')
    plt.legend(loc='upper left')

    plt.grid(True)

    plt.xticks(np.arange(0, 251, step=25))
    plt.yticks(np.arange(0, max(optimal_line_y) + 50, step=25))
    plt.show()

