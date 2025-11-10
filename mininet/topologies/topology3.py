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
        h4 = self.addHost('h4', cls=HostWithLocalname)

        s1 = self.addSwitch("s1")

        # Add links
        self.addLink(h1, s1, cls=TCLink, bw=50, delay="50ms", max_queue_size=25, fq_rate="10Mbit")
        self.addLink(h2, s1, cls=TCLink, bw=50, delay="50ms", max_queue_size=25, fq_rate="10Mbit")
        self.addLink(h3, s1, cls=TCLink, bw=50, delay="50ms", max_queue_size=25, fq_rate="10Mbit")
        self.addLink(h4, s1, cls=TCLink, bw=50, delay="50ms", max_queue_size=25, fq_rate="10Mbit")

# Topology entry point
topos = {'mytopo': SimpleTopology}
