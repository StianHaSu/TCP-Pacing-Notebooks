import subprocess
import sys

def run_all_in_experiment(experiment: str, bandwidths: list[int], queues: list[int]):
    for bandwidth in bandwidths:
        for queue in queues:
            run = f"{experiment}/{experiment}_del_15_down_{bandwidth}mbit_up_{bandwidth}mbit_aqm_pfifo_tcp_newreno_bs_{queue}_run_0_ganon.dmp"
            subprocess.run(["bash", "parse_pcap_ss.sh", run], check=True)
        
if __name__ == "__main__":
    run_all_in_experiment(sys.argv[1], [50, 100, 250, 500, 750, 1000], [10, 25, 50, 75, 100, 250, 500])