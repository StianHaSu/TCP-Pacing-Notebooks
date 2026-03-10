#!/usr/bin/env python3
import sys
import math
from dataclasses import dataclass
from typing import Optional, TextIO

MSS = 1448
IW = 10 * MSS


# ----------------------------
# Helpers
# ----------------------------

def usage_exit() -> None:
    print("Usage: script.py <filename>")
    sys.exit(1)


def iter_tokens(file: TextIO):
    """Yield whitespace-split token lists until EOF."""
    for raw in file:
        line = raw.split()
        if line:
            yield line


def is_firstloss_line(line: list[str]) -> bool:
    return len(line) > 9 and line[9] == "firstloss"


def compute_round_from_firstloss(line: list[str], iw: float) -> int:
    # Original: round = log2(cwnd) - log2(iw)
    return int(math.log2(float(line[4])) - math.log2(float(iw)))


def should_print_line(line: list[str], initcwnd: float) -> bool:
    # Original condition: if cwnd >= initcwnd or ssthresh line
    return float(line[4]) >= initcwnd or line[1] == "ssthresh"


def is_send_line(line: list[str]) -> bool:
    return line[1] == "snd"


# ----------------------------
# Phase 1: find round
# ----------------------------

def find_round(file: TextIO, iw: float) -> Optional[int]:
    """
    Scan file for the first line containing 'firstloss' in token 9.
    Compute and return 'round'. Return None if not found.
    """
    for line in iter_tokens(file):
        if is_firstloss_line(line):
            return compute_round_from_firstloss(line, iw)
    return None


# ----------------------------
# Phase 2: main printing
# ----------------------------

@dataclass
class PrintState:
    first: bool
    initcwnd: float
    inittime: float
    prev_time: float
    pktno: float


def init_state(iw: float, round_: int) -> PrintState:
    initcwnd = iw * (2 ** round_) + 1  # +1 because the round begins when the first ACK arrives
    return PrintState(
        first=True,
        initcwnd=float(initcwnd),
        inittime=-1.0,
        prev_time=-1.0,
        pktno=0.0,
    )


def maybe_print_header(state: PrintState, round_: int, time: float) -> None:
    if not state.first:
        return
    state.first = False
    print(
        "Round:", round_,
        "Init.cwnd:", int(state.initcwnd) if state.initcwnd.is_integer() else state.initcwnd,
        "Time since preceding entry:", time - state.prev_time if state.prev_time >= 0 else -1
    )
    state.inittime = time


def update_pktno_if_send(state: PrintState, line: list[str]) -> None:
    if is_send_line(line):
        state.pktno += float(line[2])


def print_line(state: PrintState, line: list[str], time: float) -> None:
    print(time - state.inittime, " ".join(line), end="")
    if is_firstloss_line(line):
        print(" Round_pktno", state.pktno)
    else:
        print()


def process_file(file: TextIO, round_: int, iw: float) -> None:
    state = init_state(iw, round_)

    for line in iter_tokens(file):
        time = float(line[0])

        if should_print_line(line, state.initcwnd):
            maybe_print_header(state, round_, time)
            update_pktno_if_send(state, line)
            print_line(state, line, time)

        state.prev_time = time


# ----------------------------
# Entrypoint
# ----------------------------

def main(argv: list[str]) -> int:
    if len(argv) != 2:
        usage_exit()

    filename = argv[1]

    try:
        with open(filename, "r") as f:
            round_ = find_round(f, IW)
            if round_ is None:
                # Original code would end up with round=-1 and proceed; you can keep that
                # behavior by setting round_ = -1. But it's usually nicer to tell the user.
                round_ = -1

            f.seek(0)
            process_file(f, round_, IW)

        return 0

    except IOError:
        print("couldn't read the input file.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
