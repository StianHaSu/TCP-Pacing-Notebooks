from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.node import OVSController
from mininet.log import setLogLevel, info

class SimpleTopology(Topo):
    """
    h1 --- s1 --- h2
    Links: bw, delay, max_queue_size (parameterized)
    """

    def __init__(self, max_queue_size, bw=100, delay="30ms"):
        Topo.__init__(self)
        self.max_queue_size = max_queue_size
        self.bw = bw
        self.delay = delay
        self.build()

    def build(self):
        # Add hosts and switch
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        s1 = self.addSwitch("s1")

        # Add links with given bw/delay/queue
        self.addLink(
            h1, s1,
            cls=TCLink,
            bw=self.bw,
            delay=self.delay,
            max_queue_size=self.max_queue_size,
            use_htb=True
        )
        self.addLink(
            h2, s1,
            cls=TCLink,
            bw=self.bw,
            delay=self.delay,
            max_queue_size=self.max_queue_size,
            use_htb=True
        )

def run_experiments(queue_sizes, iperf_time=10, iperf_bandwidth="50M"):
    """
    Run one Mininet experiment per queue size.
      - queue_sizes: list of max_queue_size values (in packets)
      - iperf_time: duration of each iperf run (seconds)
      - iperf_bandwidth: iperf -b value if using UDP (optional)
    """
    for q in queue_sizes:
        info("\n===============================\n")
        info("*** Starting experiment with max_queue_size = %d packets\n" % q)

        topo = SimpleTopology(max_queue_size=q, bw=100, delay="30ms")
        net = Mininet(topo=topo, link=TCLink, controller=OVSController)

        net.start()
        h1, h2 = net.get('h1', 'h2')

        # Start iperf server on h2
        info("*** Starting iperf server on h2\n")

        h2.cmd(f"iperf -s &")

        # Run iperf client on h1 (TCP)
        info("*** Running iperf client on h1\n")
        h1.cmd("bpftrace loss.bt > loss.txt &")
        h1.cmd(f"iperf -c {h2.IP()} -t {iperf_time} --fq-rate 100M")

        # Stop iperf server
        h2.cmd("killall -q iperf")

        net.stop()
        info("*** Experiment with max_queue_size = %d done\n" % q)


def main():
    setLogLevel('info')

    # Define the queue sizes (in packets) you want to test
    queue_sizes = [25]

    run_experiments(queue_sizes)


if __name__ == "__main__":
    main()
