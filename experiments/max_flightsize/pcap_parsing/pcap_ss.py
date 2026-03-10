#!/usr/bin/env python3
import sys
from dataclasses import dataclass
from typing import Optional, TextIO

from bokeh.io import output_file

MSS = 1448
INITIAL_CWND = 10.0 * 1448


# ----------------------------
# Parsing + matching helpers
# ----------------------------

def parse_line(raw: str) -> list[str]:
    """Normalize a tcpdump-ish line into tokens."""
    return raw.replace(",", "").split()


def is_data_packet(flags: str) -> bool:
    """Treat anything without SYN/FIN as a data-bearing packet line."""
    return ("S" not in flags) and ("F" not in flags)


def same_address(pattern: str, actual: str) -> bool:
    """
    Match an address like '1.2.3.4.80' against the parsed address field.

    If pattern ends with 'X', treat it as a wildcard for the last dot-separated
    part (used for matching 'any port').
    Example: '1.2.3.4.X' matches '1.2.3.4.443'
    """
    if not pattern.endswith("X"):
        return pattern == actual

    last_dot = actual.rfind(".")
    if last_dot == -1:
        return False

    prefix = pattern[:-2]  # strip ".X"
    return prefix == actual[:last_dot]


def iter_tokens(file: TextIO):
    """Yield tokenized lines until EOF."""
    while True:
        raw = file.readline()
        if not raw:
            return
        line = parse_line(raw)
        if line:
            yield line


# ----------------------------
# State
# ----------------------------

@dataclass
class FlowConfig:
    filename: str
    src: str
    dst: str
    mss: float
    output_file: str


@dataclass
class LossInfo:
    first_time: float
    first_seqno: float
    loss_seqno: int


@dataclass
class CCState:
    cwnd: float
    in_fligh: float
    max_in_flight: float
    sndwnd: float
    prev_seqno: float
    prev_ackno: float
    prev_snd_time: float
    prev_ack_time: float
    loss_marked: bool
    cwnd_at_max_in_flight: float
    total_sent_bytes: float
    total_sent_bytes_at_full: float
    dupacks: int
    bytes_acked_since_full: float
    total_sent_bytes_at_max_flight: float
    acked_bytes_since_full_at_max: float
    cwnd_at_link_full: float

# ----------------------------
# Phase 1: discover first time/seq + loss seq
# ----------------------------



def maybe_set_first_time_seq(cfg: FlowConfig, line: list[str], first_time: float, first_seqno: float) -> tuple[float, float]:
    """
    If this is the first sent data packet (src + 'seq'), capture first_time and first_seqno.
    """
    if first_time >= 0:
        return first_time, first_seqno

    if same_address(cfg.src, line[2]) and line[7] == "seq":
        first_time = float(line[0])
        first_seqno = float(line[8].split(":")[0])
    return first_time, first_seqno


def maybe_update_loss_seq(cfg: FlowConfig, line: list[str], prev_ackno: int) -> tuple[int, Optional[int]]:
    """
    Track ACKs from dst. If ACK decreases or repeats, declare loss_seqno = prev_ackno and stop.
    Returns (new_prev_ackno, loss_seqno_or_None)
    """
    if same_address(cfg.dst, line[2]) and line[7] == "ack":
        ackno = int(line[8])
        if ackno <= prev_ackno:
            return prev_ackno, prev_ackno
        return ackno, None
    return prev_ackno, None


def find_loss_info(file: TextIO, cfg: FlowConfig) -> LossInfo:
    """
    Scan once to:
      - find first_time + first_seqno (first data packet from src)
      - detect first loss via non-increasing ACKs from dst
    Then rewind caller to continue.
    """
    prev_ackno = -1
    loss_seqno: Optional[int] = None
    first_time = -1.0
    first_seqno = -1.0

    for line in iter_tokens(file):
        flags = line[6]
        if is_data_packet(flags):
            first_time, first_seqno = maybe_set_first_time_seq(cfg, line, first_time, first_seqno)
            prev_ackno, loss_seqno = maybe_update_loss_seq(cfg, line, prev_ackno)
            if loss_seqno is not None:
                break

    return LossInfo(first_time=first_time, first_seqno=first_seqno, loss_seqno=int(loss_seqno if loss_seqno is not None else -1))


# ----------------------------
# Phase 2: main processing (snd/ack events)
# ----------------------------

def init_cc_state(initial_cwnd: float, first_seqno: float) -> CCState:
    return CCState(
        cwnd=float(initial_cwnd),
        in_fligh=0,
        max_in_flight=0,
        sndwnd=float(initial_cwnd),
        prev_seqno=float(first_seqno),
        prev_ackno=float(first_seqno),
        prev_snd_time=-1.0,
        prev_ack_time=-1.0,
        loss_marked=False,
        cwnd_at_max_in_flight=0.0,
        total_sent_bytes=0.0,
        total_sent_bytes_at_full=0.0,        
        dupacks=0,
        bytes_acked_since_full=0.0,
        total_sent_bytes_at_max_flight=0.0,
        acked_bytes_since_full_at_max=0.0,
        cwnd_at_link_full=0.0
    )


def snd_timegap(now: float, prev: float) -> tuple[float, float]:
    gap = now - prev if prev > 0 else -1.0
    return gap, now


def ack_timegap(now: float, prev: float) -> tuple[float, float]:
    gap = now - prev if prev > 0 else -1.0
    return gap, now

def handle_send_event(cfg: FlowConfig, info: LossInfo, st: CCState, line: list[str]) -> bool:
    """
    Handle a src 'seq' line. Returns True if we should stop processing (break).
    """
    
    time = float(line[0])
    seq_lo_str, seq_hi_str = line[8].split(":")
    seq_lo = float(seq_lo_str)
    seq_hi = float(seq_hi_str)

    gap, st.prev_snd_time = snd_timegap(time, st.prev_snd_time)
        
    st.prev_seqno = seq_hi

    sent = seq_hi - seq_lo
    
    st.sndwnd -= sent
    st.in_fligh += sent
    
    st.total_sent_bytes += sent
    
    # BDP (125 packets) + queue (100 packets)
    if st.total_sent_bytes_at_full == 0.0 and st.in_fligh >= 325800:
        st.total_sent_bytes_at_full = st.total_sent_bytes
        st.cwnd_at_link_full = st.cwnd
        with open("bytes.txt", "a+") as f:
            f.write(f"{st.total_sent_bytes}\n")

    return False


def handle_ack_event(st: CCState, line: list[str], output_file: str) -> bool:
    """Handle a dst 'ack' line."""
    time = float(line[0])

    gap, st.prev_ack_time = ack_timegap(time, st.prev_ack_time)

    ackno = float(line[8])
    acked = ackno - st.prev_ackno
    st.prev_ackno = ackno

    st.cwnd += acked
    st.sndwnd += 2.0 * acked  # ack-clocking and cwnd incr
    
    st.in_fligh -= acked
    
    if st.total_sent_bytes_at_full != 0.0:
        st.bytes_acked_since_full += acked
    
    if acked > 0:
        # Reset dupAck counter
        st.dupacks = 0
    else:
        st.dupacks += 1
        if st.dupacks > 2:
            with open (output_file, "a+") as f:
                max_p_in_flight = int(st.max_in_flight / MSS)
                f.write(f"{max_p_in_flight}\n")
                
            return True

    return False


def process_trace(file: TextIO, cfg: FlowConfig, info: LossInfo, initial_cwnd: float) -> None:
    """Main loop after we know first_time/seq and the first loss seq."""
    st = init_cc_state(initial_cwnd, info.first_seqno)

    for line in iter_tokens(file):
        time = float(line[0])
        flags = line[6]

        if (not is_data_packet(flags)) or (time < info.first_time):
            continue

        if same_address(cfg.src, line[2]) and line[7] == "seq":
            handle_send_event(cfg, info, st, line)
  

        elif same_address("10.100.21.1.6000", line[2]) and line[7] == "ack":
            should_stop = handle_ack_event(st, line, cfg.output_file)
            if should_stop:
                break
            
        else:
            print(f"dest: {cfg.dst}, line: {line[2]} line7: {line[7]}", file=sys.stderr)


# ----------------------------
# CLI + entrypoint
# ----------------------------

def usage_exit() -> None:
    print("Parameters: filename source src_port destination dst_port mss")
    print("Any port: use X  (instead of * - less problematic in scripts)")
    sys.exit(1)


def parse_args(argv: list[str]) -> FlowConfig:
    if len(argv) != 7:
        usage_exit()

    filename = argv[1]
    src = f"{argv[2]}.{argv[3]}"
    dst = f"{argv[4]}.{argv[5]}"
    mss = float(argv[6])
    output_file = argv[7]
    return FlowConfig(filename=filename, src=src, dst=dst, mss=mss, output_file=output_file)


def pcap_get_max_flight_size_slow_start(argv: list[str]) -> int:
    cfg = parse_args(argv)

    try:
        with open(cfg.filename, "r") as f:
            info = find_loss_info(f, cfg)
            f.seek(0)
            process_trace(f, cfg, info, INITIAL_CWND)
        return 0
    except IOError:
        print("couldn't read the input file.")
        return 2
