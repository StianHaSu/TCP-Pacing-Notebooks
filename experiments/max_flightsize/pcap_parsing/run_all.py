import subprocess
import sys

def run_all_in_experiments_single(experiment: str, queues: list[int]):
    for i in queues:
        run = f"{experiment}/{experiment}_del_15_down_10000mbit_up_10000mbit_aqm_pfifo_tcp_newreno_bs_{i}_run_0_ganon.dmp"
        subprocess.run(["bash", "parse_pcap_ss.sh", run], check=True)
