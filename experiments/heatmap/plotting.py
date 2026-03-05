from matplotlib import pyplot as plt
from pandas import DataFrame
import seaborn as sns


def plot_heatmap(data: DataFrame, title: str = None):
    ax = sns.heatmap(data, annot=True, fmt="d", center=100, cmap="viridis")
    cbar = ax.collections[0].colorbar
    cbar.set_label("Percentage", fontsize=20)

    ax.set_ylabel("Bandwidth (Mbs)", fontsize=20)
    ax.set_xlabel("Queue size (packets)", fontsize=20)

    ax.invert_yaxis()

    if title is not None:
        plt.title(title, fontsize=22)

    plt.show()