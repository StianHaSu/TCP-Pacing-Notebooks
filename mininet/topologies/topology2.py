from mininet.topo import Topo
from mininet.link import TCLink
from mininet.node import Host
from mininet.net import Mininet

class HostWithLocalname(Host):
    def config(self, **params):
        r = super().config(**params)

        self.cmd('hostname %s' % self.name)

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

    for h in net.hosts:
        h.cmd(
            'xterm -T {n} -e bash -lc '
            '"hostname {n}; '
            'PS1=\'\\u@{n}:\\w# \'; '
            'echo --- {n} ---; '
            'ip -brief addr; '
            'exec bash" &'.format(n=h.name)
        )

    # (Example) Start iperf server on h2, client on h1
    h1, h2, h3 = net.get('h1', 'h2', 'h3')

    multiplier = 10

    h1.cmd('sudo sysctl -w net.ipv4.tcp_ss_pacing_multiplier=', multiplier)
    h2.cmd('sudo sysctl -w net.ipv4.tcp_ss_pacing_multiplier=', multiplier)
    h3.cmd('sudo sysctl -w net.ipv4.tcp_ss_pacing_multiplier=', multiplier)

    h3.popen('iperf -s', shell=True)

    print(h1.name, 'iperf ->', h1.cmd('iperf -c %s -t 30' % h3.IP()))
    print(h2.name, 'iperf ->', h2.cmd('iperf -c %s -t 30' % h3.IP()))

    CLI(net)
    net.stop()

# Topology entry point
topos = {'mytopo': SimpleTopology}


if __name__ == '__main__':
    run()