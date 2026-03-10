from holoviews.plotting.bokeh.styles import font_size
from matplotlib import pyplot as plt
from pandas import DataFrame
import seaborn as sns


def plot_heatmap(data: DataFrame, title: str = None, output_path: str = None):
    fig = plt.figure(figsize=(10, 8))
    ax = sns.heatmap(data, annot=True, fmt="d", center=100, cmap="viridis", annot_kws={"size": 18})
    cbar = ax.collections[0].colorbar
    cbar.set_label("Percentage", fontsize=26)

    ax.set_ylabel("Bandwidth (Mbs)", fontsize=26)
    ax.set_xlabel("Queue size (packets)", fontsize=26)

    ax.tick_params(axis='x', labelsize=20)
    ax.tick_params(axis='y', labelsize=20)

    cbar.ax.tick_params(labelsize=20)

    ax.invert_yaxis()

    if output_path is not None:
        name = "_".join(title.split())
        fig.savefig(output_path + "/" + name + ".pdf", bbox_inches="tight", pad_inches=0.05)

    plt.show()


def plot_heatmap_stddev(data: DataFrame, title: str = None, output_path: str = None):
    fig = plt.figure(figsize=(10, 8))

    ax = sns.heatmap(data, annot=True, fmt=".0f", center=100, cmap="viridis", annot_kws={"size": 18})
    cbar = ax.collections[0].colorbar
    cbar.set_label("Percentage", fontsize=26)

    ax.set_ylabel("Bandwidth (Mbs)", fontsize=26)
    ax.set_xlabel("Queue size (packets)", fontsize=26)

    ax.tick_params(axis='x', labelsize=20)
    ax.tick_params(axis='y', labelsize=20)

    cbar.ax.tick_params(labelsize=20)

    ax.invert_yaxis()

    if output_path is not None:
        name = "_".join(title.split())
        fig.savefig(output_path + "/" + name + ".pdf", bbox_inches="tight", pad_inches=0.05)

    plt.show()