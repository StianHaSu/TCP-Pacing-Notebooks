import subprocess

from experiments.max_flightsize.pcap_parsing.experiment_config import ExperimentConfig
from experiments.max_flightsize.pcap_parsing.pcap_ss import pcap_get_max_flight_size_slow_start

INPUT_DATA_PATH = "../raw_data"
OUTPUT_DATA_PATH = "../parsed_data"

def run_all_in_experiment(experiment_config: ExperimentConfig):
    for bandwidth in experiment_config.bandwidths:
        for queue in experiment_config.queues:
            for run in range(experiment_config.runs):
                run = (f"{INPUT_DATA_PATH}/{experiment_config.experiment_name}/{experiment_config.experiment_name}"
                       f"_del_{experiment_config.delay_ms}_down_{bandwidth}mbit_up_{bandwidth}"
                       f"mbit_aqm_pfifo_tcp_newreno_bs_{queue}_run_{run}_{experiment_config.pcap_suffix}")

                subprocess.run(["bash", f"tcpdump -ntt -r {run} > input.txt"])
                pcap_get_max_flight_size_slow_start([
                    "input.txt",
                    "10.100.24.4",
                    "X",
                    "10.100.25.5",
                    "X",
                    1448,
                    experiment_config,
                    OUTPUT_DATA_PATH + f"/{experiment_config.experiment_name}_max_flight_size.txt"])
    