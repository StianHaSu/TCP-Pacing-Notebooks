from mininet.topo import Topo
from mininet.link import TCLink
from mininet.node import Host
from mininet.net import Mininet

class HostWithLocalname(Host):
    def config(self, **params):
        # Run normal Host setup first
        r = super().config(**params)

        # Ensure the runtime hostname is the Mininet host name (h1, h2, ...)
        self.cmd('hostname %s' % self.name)

        # Make sure the host can resolve its own name (fixes sudo/PAM lookups)
        # Idempotent: only appends if the name isn't already present.
        self.cmd('grep -qE "\\s%s(\\s|$)" /etc/hosts || echo "127.0.0.1 %s" >> /etc/hosts'
                 % (self.name, self.name))
        return r

class SimpleTopology(Topo):
    def build(self):
        # Add hosts and switch (using our custom host class for all hosts)
        h1 = self.addHost('h1', cls=HostWithLocalname)
        h2 = self.addHost('h2', cls=HostWithLocalname)
        h3 = self.addHost('h3', cls=HostWithLocalname)
        s1 = self.addSwitch("s1")

        # Add links
        self.addLink(h1, s1, cls=TCLink, bw=50, delay="50ms", max_queue_size=25, fq_rate="10Mbit")
        self.addLink(h2, s1, cls=TCLink, bw=50, delay="50ms", max_queue_size=25, fq_rate="10Mbit")
        self.addLink(h3, s1, cls=TCLink, bw=50, delay="50ms", max_queue_size=25, fq_rate="10Mbit")


def run():
    topo = SimpleTopology()
    net = Mininet(topo=topo, link=TCLink, controller=None, autoSetMacs=True, autoStaticArp=True)
    net.start()

    multiplier = 10

    for h in net.hosts:
        print(h.name, '->', h.cmd('ip -brief addr show'))
        h.cmd('sudo sysctl -w net.ipv4.tcp_ss_pacing_multiplier=', multiplier)

    for h in net.hosts:
        # Keep the terminal open by ending with 'exec bash'
        h.cmd('xterm -T %s -e bash -lc "echo --- %s ---; hostname; ip -brief addr; exec bash" &' % (h.name, h.name))

    h1, h2, h3 = net.get('h1', 'h2', 'h3')

    for h in net.hosts:
        h.cmd('sudo sysctl net.ipv4.tcp_ss_pacing_multiplier')

    print(h3.name, 'iperf ->', h3.cmd('iperf -s1'))
    print(h1.name, 'iperf ->', h1.cmd('iperf -c %s -t 30' % h3.IP()))
    print(h2.name, 'iperf ->', h2.cmd('iperf -c %s -t 30' % h3.IP()))

    # Drop to interactive CLI when you’re ready
    CLI(net)
    net.stop()

# Topology entry point
topos = {'mytopo': SimpleTopology}


if __name__ == '__main__':
    run()