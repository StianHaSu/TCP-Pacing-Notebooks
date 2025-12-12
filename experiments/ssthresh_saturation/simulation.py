from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.node import OVSController
from mininet.log import setLogLevel, info
import time
from datetime import datetime
import os

class SimpleTopology(Topo):
    """
    h1 --- s1 --- h2
    """
    def build(self, max_queue_size, bw, delay="7.5ms"):
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        s1 = self.addSwitch("s1")

        self.addLink(
            h1, s1,
            cls=TCLink,
            bw=1000,
            delay=delay,
            #max_queue_size=max_queue_size
        )

        self.addLink(
            h2, s1,
            cls=TCLink,
            bw=bw,
            delay=delay,
            #max_queue_size=max_queue_size,
        )


def attach_aqm_to_switch(net, max_queue_size):
    """
    Attach fq_codel as child qdisc on the switch ports.

    Layout we aim for (per s1-ethX):

        root htb ...
          class ...
            qdisc 10: netem delay 7.5ms
              qdisc 20: fq_codel  (AQM queue)

    Mininet normally uses handle 10: for netem; we use that as parent.
    """
    s1 = net.get('s1')

    # Adjust interface names if Mininet uses different ones
    switch_intfs = ['s1-eth1', 's1-eth2']

    for intf in switch_intfs:
        # Optional: see what Mininet created
        print(s1.cmd(f'tc qdisc show dev {intf}'))

        # Attach fq_codel under the existing netem qdisc (handle 10:)
        # limit controls how many packets can sit in the fq_codel queue
        s1.cmd(
            f'tc qdisc add dev {intf} parent 10: handle 20: '
            f'fq_codel limit {max_queue_size}'
        )

        # Optional: verify
        print(s1.cmd(f'tc qdisc show dev {intf}'))


def run_experiments(output_dir, queue_sizes, iperf_time=10, iperf_bandwidth=50):
    """
    Run one Mininet experiment per queue size.
      - queue_sizes: list of max_queue_size values (in packets)
      - iperf_time: duration of each iperf run (seconds)
      - iperf_bandwidth: iperf -b value if using UDP (optional)
    """
    for q in queue_sizes:
    
        topo = SimpleTopology(max_queue_size=q, bw=iperf_bandwidth)
        net = Mininet(topo=topo, link=TCLink, controller=OVSController)
        net.start()

        attach_aqm_to_switch(net, max_queue_size=q)
        
        h1, h2 = net.get('h1', 'h2')
        net.get('s1')

        h2.cmd("iperf -s &")
        time.sleep(1)  # Give server time to start
        
        log_file = f"{output_dir}/complete/log-{q}.txt"
        monitor_cmd = (
            'while true; do '
            'ts=$(date +%H:%M:%S.%N); '
            'ss -tin | sed "s/^/$ts /"; '
            'echo ""; '
            'sleep 0.1; '
            f'done > {log_file} 2>&1 &'
        )
        
        h1.cmd(monitor_cmd)
        time.sleep(0.5)  

        # Pacing add: --fq-rate 100M
        h1.cmd(f"iperf -c {h2.IP()} -t {iperf_time} ")

        time.sleep(1)

        h1.cmd("killall -9 sh")

        h2.cmd("killall -9 iperf")
        
        h1.cmd(f"wc -l {log_file}")

        ssthresh_log = f"{output_dir}/ssthresh/sstresh-queue-{q}.txt"
        h1.cmd(f"grep 'ssthresh:' {log_file} | head -100 > {ssthresh_log}")
        
        net.stop()


def main():
    setLogLevel('info')

    # Define the queue sizes (in packets) you want to test
    queue_sizes = [x for x in range(5, 255, 5)]

    time = datetime.now()
    time = str(time).replace(" ", "_")

    os.mkdir(time)
    os.mkdir(time+"/ssthresh")
    os.mkdir(time+"/complete")
    run_experiments(time, queue_sizes, 10)


if __name__ == "__main__":
    main()
