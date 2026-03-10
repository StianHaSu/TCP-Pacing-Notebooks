from attr import dataclass


@dataclass
class ExperimentConfig:
    experiment_name: str
    bandwidths: list[int]
    delay_ms: int
    queues: list[int]
    runs: int
    pcap_suffix: str

