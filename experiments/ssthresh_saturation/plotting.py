from matplotlib import pyplot as plt
import numpy as np

def plot_ssthresh_and_queue_size(queues: list[int], sshtresh: list[int]):
    plt.scatter(queues, sshtresh, marker='+', color='black')

    optimal_line_x = [x for x in range(251)]
    optimal_line_y = [ 125 + x for x in range(251) ]

    plt.plot(optimal_line_x, optimal_line_y, color='purple')

    plt.xlabel('Queue size')
    plt.ylabel('SSThresh')

    plt.grid(True)

    plt.yticks(np.arange(0, 2100, step=125))
    plt.show()

