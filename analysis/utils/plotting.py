from xmlrpc.client import MAXINT

import numpy as np
from scapy.layers.inet import TCP
from matplotlib import pyplot as plt
import matplotlib.ticker as ticker
from scapy.utils import rdpcap, PcapReader

from analysis.utils.GraphConfig import GraphConfig
from analysis.utils.GraphData import GraphData
from mpl_toolkits.axes_grid1.inset_locator import zoomed_inset_axes, mark_inset

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
    graph_config: GraphConfig, graph_data: GraphData = None, cutoff: int = -1, exit_after_ss: bool = True
):

    graph_data = graph_data if graph_data is not None else get_data_from_pcap(graph_config, exit_after_ss)
    plot_packets(graph_data, graph_config, cutoff)

    return graph_data


def plot_packets_from_pcap_files(
    graph_config_list: list[GraphConfig], graphs: list[tuple[GraphConfig, GraphData]] = None,  cutoff: int = -1,
        title = "All runs"
):
    graphs = graphs if graphs is not None else get_data_from_pcap_files(graph_config_list)

    plot_packets_from_multiple_files(graphs, title, cutoff)

    return graphs


def get_data_from_pcap_files(graph_config_list: list[GraphConfig]):
    return [(graph_config, get_data_from_pcap(graph_config)) for graph_config in graph_config_list]


def get_data_from_pcap(graph_config: GraphConfig, exit_after_ss: bool):
    packets = get_data_from_packets(graph_config.filename, graph_config.start, graph_config.end, exit_after_ss)

    graph_data = GraphData(packets[0], packets[1], packets[2], packets[3])

    return graph_data


def get_data_from_packets(packets, start: int = None, end: int = None, exit_after_ss: bool = True):
    data_x = []
    data_y = []
    ack_x = []
    ack_y = []

    start_time = None
    smallest_seq = MAXINT
    smallest_ack = MAXINT

    packs = 0
    acks = 0

    acks_per_rtt = {}
    packets_per_rtt = {}
    double_acks_per_rtt = {}

    last_ack = 0
    dupacks = 0
    with PcapReader(packets) as pcap:
        for pkt in pcap:
            if TCP in pkt:
                tcp = pkt[TCP]

                if tcp.seq < 1 or tcp.ack < 2:
                    continue

                if end is not None and packs > end:
                    break

                if start_time is None:
                    start_time = pkt.time

                delta_ms = (pkt.time - start_time) * 1000 # Time since start in ms

                flags = tcp.flags

                payload_len = len(bytes(tcp.payload))
                if payload_len > 0:
                    if tcp.seq < smallest_seq:
                        smallest_seq = tcp.seq

                    rtt_round = int(delta_ms / 30)

                    if rtt_round not in packets_per_rtt:
                        packets_per_rtt[rtt_round] = 0

                    packets_per_rtt[rtt_round] += 1

                    packs += 1

                    if start is None or packs > start:
                        data_x.append(delta_ms)
                        data_y.append(packs)



                elif packs < 1:
                    continue
                else:
                    rtt_round = int(delta_ms / 30)

                    #if tcp.ack - last_ack > 1448:
                    #    print(f"RTT: {rtt_round} Double ack: {acks+1} is: {tcp.ack - last_ack}")

                    if tcp.ack - last_ack < 1:
                        #print(f"Dup ACK in RTT: {rtt_round} {tcp.ack} {tcp.ack - last_ack}")
                        dupacks += 1
                        if dupacks > 2 and exit_after_ss:
                            print(f"Total sent packets before third dupack: {packs}")
                            break

                    last_ack = tcp.ack

                    if rtt_round not in acks_per_rtt:
                        acks_per_rtt[rtt_round] = 0

                    acks_per_rtt[rtt_round] += 1

                    acks += 1

                    ack_x.append(delta_ms)
                    ack_y.append(acks)


    return data_x, data_y, ack_x, ack_y


def plot_packets(graph_data: GraphData, graph_config: GraphConfig, cutoff: int = -1):
    sl = slice(None) if cutoff == -1 else slice(0, cutoff)

    data_x = graph_data.x_data[sl]
    data_y = graph_data.y_data[sl]
    ack_x  = graph_data.x_acks[sl]
    ack_y  = graph_data.y_acks[sl]

    fig = plt.figure(figsize=(10, 6))

    plt.scatter(data_x, data_y, color=graph_config.color, label="Data packets", alpha=0.6)
    if graph_config.include_acks:
        plt.scatter(ack_x, ack_y, color="red", label="ACKs", alpha=0.6, marker="x")

    start_x = int(float(min(data_x)) - 0.2)  if graph_config.start is not None else 0
    start_y = int(float(min(data_y))) if graph_config.start is not None else 0

    plt.xticks(np.arange(start_x, int(max(data_x)) + graph_config.tick_step_x, graph_config.tick_step_x), fontsize=24)
    plt.yticks(np.arange(start_y, int(max(data_y)) + graph_config.tick_step_y, graph_config.tick_step_y), fontsize=24)

    # Styling on main axis
    plt.xlabel("Time since beginning (ms)", fontsize=32)
    plt.ylabel("Normalized seq. nr.", fontsize=32)
    #plt.title(graph_config.title)
    #plt.legend()
    plt.tight_layout()
    plt.grid(True)

    # Avoid tight_layout/constrained_layout with insets; adjust manually if needed
    #fig.subplots_adjust(left=0.12, right=0.98, top=0.92, bottom=0.12)

    if graph_config.save_plot:
        name = "_".join(graph_config.title.split())

        if graph_config.start is not None:
            name += "_start=" + str(graph_config.start)

        if graph_config.end is not None:
            name += "_end=" + str(graph_config.end)

        fig.savefig(name + ".pdf")

    return fig


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


    plt.xticks(np.arange(0, 300, 25))
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