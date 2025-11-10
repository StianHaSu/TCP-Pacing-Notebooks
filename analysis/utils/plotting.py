from xmlrpc.client import MAXINT

import numpy as np
from scapy.layers.inet import TCP
from matplotlib import pyplot as plt
import matplotlib.ticker as ticker
from scapy.utils import rdpcap

from analysis.utils.GraphConfig import GraphConfig
from analysis.utils.GraphData import GraphData

plt.rcParams.update({
    'font.size': 16,          # base font size
    'axes.titlesize': 20,     # title size
    'axes.labelsize': 18,     # x and y labels
    'xtick.labelsize': 14,    # x-axis tick labels
    'ytick.labelsize': 14,    # y-axis tick labels
    'legend.fontsize': 14,    # legend text
    'figure.titlesize': 20    # figure title
})

def plot_packets_from_pcap_file(
    graph_config: GraphConfig, graph_data: GraphData = None, cutoff: int = -1
):

    graph_data = graph_data if graph_data is not None else get_data_from_pcap(graph_config.filename)
    plot_packets(graph_data, graph_config, cutoff)

    return graph_data


def plot_packets_from_pcap_files(
    graph_config_list: list[GraphConfig], graphs: list[tuple[GraphConfig, GraphData]] = None,  cutoff: int = -1
):
    graphs = graphs if graphs is not None else get_data_from_pcap_files(graph_config_list)

    plot_packets_from_multiple_files(graphs, "All runs", cutoff)

    return graphs


def get_data_from_pcap_files(graph_config_list: list[GraphConfig]):
    return [(graph_config, get_data_from_pcap(graph_config.filename)) for graph_config in graph_config_list]


def get_data_from_pcap(filename: str):
    pcap = rdpcap(filename)
    packets = get_data_from_packets(pcap)

    graph_data = GraphData(packets[0], packets[1], packets[2], packets[3])

    return graph_data


def get_data_from_packets(packets):
    data_x = []
    data_y = []
    ack_x = []
    ack_y = []

    start_time = None
    smallest_seq = MAXINT
    smallest_ack = MAXINT

    packs = 0
    acks = 0
    for pkt in packets:
        if TCP in pkt:
            tcp = pkt[TCP]

            #if tcp.seq < 2 or tcp.ack < 2:
            #    continue

            if start_time is None:
                start_time = pkt.time

            delta_ms = (pkt.time - start_time) * 1000 # Time since start in ms

            flags = tcp.flags

            if not "A" == flags:
                if tcp.seq < smallest_seq:
                    smallest_seq = tcp.seq

                data_x.append(delta_ms)
                data_y.append(packs)
                packs += 1
            else:
                if tcp.ack < smallest_ack:
                    smallest_ack = tcp.ack

                ack_x.append(delta_ms)
                ack_y.append(acks)
                acks += 1

    return data_x, data_y, ack_x, ack_y


def plot_packets(graph_data: GraphData, graph_config: GraphConfig, cutoff: int = -1):
    plt.figure(figsize=(10, 6))

    data_x = graph_data.data_x[0:cutoff]
    data_y = graph_data.data_y[0:cutoff]
    ack_x = graph_data.ack_x[0:cutoff]
    ack_y = graph_data.ack_y[0:cutoff]

    plt.scatter(data_x, data_y, color='blue', label='Data packets', alpha=0.6)
    if graph_config.include_acks:
        plt.scatter(ack_x, ack_y, color='red', label='ACKs', alpha=0.6, marker="x")

    plt.xlabel('Time since beginning (ms)')
    plt.ylabel('Sequence / ACK Number')
    plt.title(graph_config.title)
    plt.legend()
    plt.yscale('linear')
    plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{int(x):,}'))
    plt.grid(True)
    plt.tight_layout()

    if graph_config.save_plot:
        name = "_".join(graph_config.title.split(" "))
        print("Name: ", name)
        plt.savefig(name + ".pdf")


def plot_packets_from_multiple_files(graphs: list[tuple[GraphConfig, GraphData]], title: str, cutoff: int = -1):
    plt.figure(figsize=(10, 6))

    for graph_config, graph_data in graphs:
        data_x = graph_data.x_data[0:cutoff]
        data_y = graph_data.y_data[0:cutoff]
        ack_x = graph_data.x_acks[0:cutoff]
        ack_y = graph_data.y_acks[0:cutoff]

        plt.scatter(data_x, data_y, color=graph_config.color, label=graph_config.label, alpha=0.6, marker=graph_config.marker)
        if graph_config.include_acks:
            plt.scatter(ack_x, ack_y, color='red', label='ACKs', alpha=0.6, marker="x")

    #optimal = generate_optimal_data(cutoff, 200, 10)
    #plt.plot(optimal[0], optimal[1], 'ro', label='Optimal')

    plt.xlabel('Time since beginning (ms)')
    plt.ylabel('Sequence / ACK Number')
    plt.title(title)
    plt.legend()
    plt.yscale('linear')
    plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{int(x):,}'))
    plt.grid(True)
    plt.tight_layout()


def plot_optimal(cutoff, rtt, multiplier):
    optimal = generate_optimal_data(cutoff, rtt, multiplier)
    plt.plot(optimal[0], optimal[1], 'ro', label='Optimal')


def generate_optimal_data(cutoff, rtt, multiplier):
    x_values = []
    y_values = []

    for i in range(10):
        y_values.append(i)
        x_values.append(0)


    for i in range(10, cutoff):
        y_values.append(i)

        x = 1000 / (rtt * (np.log2(i+1) - np.log2(i)))
        #x *= multiplier
        x_values.append(x)

    return x_values, y_values


def normalize_y_axis(seq_nrs: list[int], low: int):
    normalized = []
    for seq_nr in seq_nrs:
        normalized.append(seq_nr - low)

    return normalized