from scapy.all import rdpcap
from scapy.layers.inet import IP, TCP
import gzip
import shutil

def count_acks_until_first_dupack(
    pcap_file_in: str,
    mss_payload: int = 1448,
    gzipped: bool | None = None,
):
    pcap_file_unzipped = pcap_file_in.replace(".dmp.gz", ".pcap")

    with gzip.open(pcap_file_in, "rb") as f_in, open(pcap_file_unzipped, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)

    pkts = rdpcap(pcap_file_unzipped)

    last_ack = {}  # (src, sport, dst, dport) -> last ack
    one_seg = 0
    two_seg = 0
    other_adv = 0

    stop_info = None  # will hold info about first dupack

    for p in pkts:  # IMPORTANT: keep time/capture order
        if IP not in p or TCP not in p:
            continue

        ip = p[IP]
        tcp = p[TCP]

        # Need ACK flag, and ignore SYN/FIN/RST packets
        if not tcp.flags.A or tcp.flags.S or tcp.flags.F or tcp.flags.R:
            continue

        # ACK-only (no TCP payload). This matches Wireshark dupack analysis best.
        if len(tcp.payload) != 0:
            continue

        flow = (ip.src, int(tcp.sport), ip.dst, int(tcp.dport))
        ack = int(tcp.ack)

        prev = last_ack.get(flow)
        if prev is not None:
            delta = ack - prev

            if delta == 0:
                stop_info = {"flow": flow, "ack": ack, "pkt_time": float(p.time)}
                break

            if delta == mss_payload:
                one_seg += 1
            elif delta == 2 * mss_payload:
                two_seg += 1
            else:
                other_adv += 1

        last_ack[flow] = ack

    return {
        "one_seg": one_seg,
        "two_seg": two_seg,
        "other_adv": other_adv,
        "stopped_on_dupack": stop_info is not None,
        "dupack_info": stop_info,
    }


def get_double_acks(experiment: str):
    with open("acks2.txt", "a+") as f:
        for queue in range(5, 255, 5):
            f.write(str(count_acks_until_first_dupack(experiment + "/" + experiment + "_del_15_down_50mbit_up_50mbit_aqm_pfifo_tcp_newreno_bs_"+ str(queue) +"_run_0_zelda_10Ga_router.dmp.gz")["two_seg"]))
            f.write("\n")

if __name__ == '__main__':
    get_double_acks("exp_20260123-151534")