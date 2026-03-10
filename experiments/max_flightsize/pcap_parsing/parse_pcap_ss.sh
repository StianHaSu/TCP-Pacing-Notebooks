#!/bin/bash
tcpdump -ntt -r $1 > input.txt
python3 pcap_ss.py input.txt 10.100.24.4 X 10.100.25.5 X 1448
