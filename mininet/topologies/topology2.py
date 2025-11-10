from mininet.topo import Topo
from mininet.link import TCLink

class SimpleTopology(Topo):
    def build(self):
        # Add hosts and switches
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')
        s1 = self.addSwitch("s1")
        
        # Add links
        self.addLink(h1, s1, cls=TCLink, bw=50, delay="50ms", max_queue_size=25, fq_rate="10Mbit")
        self.addLink(h2, s1, cls=TCLink, bw=50, delay="50ms", max_queue_size=25, fq_rate="10Mbit")
        self.addLink(h3, s1, cls=TCLink, bw=50, delay="50ms", max_queue_size=25, fq_rate="10Mbit")

# Topology entry point
topos = {'mytopo': SimpleTopology}
