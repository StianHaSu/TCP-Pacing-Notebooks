import gzip
import os

SENDER_MACHINE = "ganon"
METRIC = "cwnd"

def get_completed_experiments(experiment_list_file: str) -> list[str]:
    return [f for f in open(experiment_list_file+"/experiments_completed.txt", "r").read().split("\n")]


def get_content_from_file(experiment_file: str, experiment_path: str) -> list[str]:
    with gzip.open(experiment_path + "/" + experiment_file + "_" + SENDER_MACHINE + "_" + METRIC+".log.gz", "rt", encoding="utf-8") as f:
        return [l for l in f]


def get_metric_from_list(lines: list[str], metric_type: str) -> list[tuple[int, float]]:
    metric = []
    for line in lines:
        line = line.split(" ")
        if len(line) > 3:
            ssthresh = next((w for w in line if metric_type in w), None)

            if ssthresh is not None:
                metric.append((int(ssthresh.split(":")[1]), float(line[0])))

    return metric

def get_ssthresh_from_files(experiment_path: str) -> tuple[list[int], list[int]]:
    completed_experiments = get_completed_experiments(experiment_path)
    first_ssthresh = []
    second_ssthresh = []

    for experiment in completed_experiments:
        metric = get_metric_from_list(get_content_from_file(experiment, experiment_path), "ssthresh")
        if len(metric) > 0:
            first_ssthresh.append(metric[0][0])

            # Filter entries that are less than two seconds after first loss, and that has a lower ssthresh value
            filtered = [ x[0] for x in metric if (x[1] - metric[0][1] < 0.2) and x[0] < metric[0][0] ]

            if len(filtered) > 0:
                second_ssthresh.append(min(filtered))
            else:
                second_ssthresh.append(metric[0][0])
        else:
            first_ssthresh.append(0)
            second_ssthresh.append(0)


    return first_ssthresh, second_ssthresh

def get_content_from_file_one(experiment_file: str) -> list[str]:
    with gzip.open(experiment_file, "rt", encoding="utf-8") as f:
        return [l for l in f]


def get_max_of_metric(experiment_file: str, metric: str):
    metric = get_metric_from_list(get_content_from_file_one(experiment_file), metric)
    print("max: ", max(metric))