from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.node import Node

class Router(Node):
    def config(self, **params):
        super(Router, self).config(**params)
        self.cmd('sysctl -w net.ipv4.ip_forward=1')  # enable routing

        # Configure iptables for NAT with proper security
        # Clear existing rules
        self.cmd('iptables -t nat -F')
        self.cmd('iptables -t nat -X')
        self.cmd('iptables -F')
        self.cmd('iptables -X')
        
        # Set restrictive default policies for security
        self.cmd('iptables -P INPUT ACCEPT')
        self.cmd('iptables -P FORWARD DROP')
        self.cmd('iptables -P OUTPUT ACCEPT')
        
        # Configure NAT (masquerading) for traffic going out through external interface
        self.cmd('iptables -t nat -A POSTROUTING -s 10.0.0.0/8 -o r1-eth2 -j MASQUERADE')
        
        # Allow forwarding from internal networks to external (outbound only)
        self.cmd('iptables -A FORWARD -s 10.0.0.0/8 -i r1-eth1 -o r1-eth2 -j ACCEPT')
        
        # Allow established and related connections back from external to internal
        self.cmd('iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT')
        


class MyTopo( Topo ):
    "Simple topology example."

    def build( self ):
        "Create custom topo."

        # Bebouw A
        # verdieping 1
        switch1 = self.addSwitch( 's1' , dpid='0000000000000001', cls=OVSSwitch, protocols='OpenFlow13')
        router1 = self.addNode( 'r1' , cls=Router )
        controller = self.addHost( 'c1' , ip='10.0.0.2/24', defaultRoute='via 10.0.0.254' )
        host1 = self.addHost( 'h1', ip='10.0.100.2/24' , defaultRoute='via 10.0.100.254' )

        # verdieping 2
        switch2 = self.addSwitch( 's2' , dpid='0000000000000002', cls=OVSSwitch, protocols='OpenFlow13')
        host2 = self.addHost( 'h2', ip='10.0.100.3/24' , defaultRoute='via 10.0.100.254' )
        host3 = self.addHost( 'h3', ip='10.0.200.2/24' , defaultRoute='via 10.0.200.254' )

        # overig
        isp = self.addHost( 'isp', ip='221.1.1.1/28', defaultRoute='via 221.1.1.2' )

        # Add links
        self.addLink( switch1, host1, port1=1, port2=1 )
        self.addLink( switch1 , controller, port1=22, port2=1 )
        self.addLink( switch1, router1, port1=23, port2=1 )        
        self.addLink( switch1, switch2, port1=24, port2=24 )
        
        self.addLink( router1, isp, port1=2, port2=1 )

        self.addLink( switch2, host2, port1=1, port2=1 )
        self.addLink( switch2, host3, port1=2, port2=1 )
        



def run():
    topo = MyTopo()
    net = Mininet(topo=topo, controller=None, switch=OVSSwitch, autoSetMacs=True)
    net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)
    net.start()

    r1 = net.get('r1')
    r1.cmd('ifconfig r1-eth1 10.0.0.1/24')
    r1.cmd('ifconfig r1-eth2 221.1.1.2/28')
    r1.cmd('route add default gw 221.1.1.1 r1-eth2')
    r1.cmd('route add -net 10.0.0.0/8 gw 10.0.0.254')
    
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()
