import pandas as pd
from pandas import DataFrame
from pandas.core.indexes.base import str_t


def transform_to_matrix(filename: str, bandwidths: list[int], queues: list[int]) -> DataFrame:
    matrix = []
    for _ in bandwidths:
        matrix.append([])

    with open(filename, "r+") as f:
        bandwidth_counter = 0
        line_counter = 0
        for line in f:
            line = int(line)
            matrix[bandwidth_counter].append(line)
            line_counter += 1

            if line_counter >= len(queues):
                bandwidth_counter += 1
                line_counter = 0



    return pd.DataFrame(matrix, index=bandwidths, columns=queues)

def transform_to_matrix_mean(means: list[int], bandwidths: list[int], queues: list[int]) -> DataFrame:
    matrix = []
    for _ in bandwidths:
        matrix.append([])

    bandwidth_counter = 0
    line_counter = 0
    for mean in means:
        matrix[bandwidth_counter].append(mean)
        line_counter += 1

        if line_counter >= len(queues):
            bandwidth_counter += 1
            line_counter = 0

    return pd.DataFrame(matrix, index=bandwidths, columns=queues)

def transform_to_matrix_stddev(stddevs: list[int], bandwidths: list[int], queues: list[int]) -> DataFrame:
    matrix = []
    for _ in bandwidths:
        matrix.append([])

    bandwidth_counter = 0
    line_counter = 0
    for stddev in stddevs:
        matrix[bandwidth_counter].append(stddev)
        line_counter += 1

        if line_counter >= len(queues):
            bandwidth_counter += 1
            line_counter = 0

    return pd.DataFrame(matrix, index=bandwidths, columns=queues)

def get_bdp_in_packets(bandwidths: list[int], rtt: int):
    return [(int((bandwidth * 10**6 * (rtt / 1000)) / 8 / 1500)) for bandwidth in bandwidths]

def get_bdp_plus_queue_matrix(bandwidths: list[int], queues: list[int], rtt: int) -> DataFrame:
    matrix = []
    for bandwidth in bandwidths:
        row = []
        for queue in queues:
            row.append(2 * (((bandwidth * 10**6 * (rtt / 1000)) / 8 / 1500) + queue))

        matrix.append(row)

    bdps = get_bdp_in_packets(bandwidths, 30)

    return pd.DataFrame(matrix, index=bandwidths, columns=queues)


def get_as_percentage_matrix(max_flight_matrix: DataFrame, bandwidths: list[int], queues: list[int], rtt: int) -> DataFrame:
    bdp_queue = get_bdp_plus_queue_matrix(bandwidths, queues, rtt)

    return (max_flight_matrix / bdp_queue) * 100


def aggregate_data(filename: str, runs: int):
    counter = 0
    row = 0

    matrix = []
    with open(filename, "r+") as f:
        for line in f:
            if counter == 0:
                matrix.append([])

            matrix[row].append(int(line))
            counter += 1

            if counter == runs:
                counter = 0
                row += 1

    all_runs = pd.DataFrame(matrix, index=range(row), columns=range(runs))

    return all_runs

def get_statistics(aggregated_data: DataFrame):
    return pd.DataFrame({
        "mean": aggregated_data.mean(axis=1),
        "std": aggregated_data.std(axis=1),
        "min": aggregated_data.min(axis=1),
        "max": aggregated_data.max(axis=1)
    })













