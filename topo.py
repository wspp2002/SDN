from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSSwitch
from mininet.nodelib import NAT
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.node import Node
import time
        


class MyTopo( Topo ):
    "Simple topology example."

    def build( self ):
        "Create custom topo."

        # Bebouw A
        # verdieping 1
        switch1 = self.addSwitch( 's1' , dpid='0000000000000001', cls=OVSSwitch, protocols='OpenFlow13')
        controller = self.addHost( 'c1' , ip='10.0.0.3/24', defaultRoute='via 10.0.0.254' )
        # leave h1 without a static IP so it can receive one via DHCP
        host1 = self.addHost( 'h1', ip='0.0.0.0' ) # Host op office vlan

        DHCP_Vlan1 = self.addHost( 'dhcp1', ip='10.0.100.10/24', defaultRoute='via 10.0.100.254' )
        DHCP_Vlan2 = self.addHost( 'dhcp2', ip='10.0.200.10/24', defaultRoute='via 10.0.200.254' )
        DHCP_Vlan3 = self.addHost( 'dhcp3', ip='10.0.0.10/24', defaultRoute='via 10.0.0.254' )

        # verdieping 2
        switch2 = self.addSwitch( 's2' , dpid='0000000000000002', cls=OVSSwitch, protocols='OpenFlow13')
        host2 = self.addHost( 'h2', ip='0.0.0.0'  ) # Office vlan
        host3 = self.addHost( 'h3', ip='0.0.0.0' ) # Guest vlan

        # gebouw B
        # verdieping 1
        switch3 = self.addSwitch( 's3' , dpid='0000000000000003', cls=OVSSwitch, protocols='OpenFlow13')
        host4 = self.addHost( 'h4', ip='0.0.0.0' ) # office vlan
        c2 = self.addHost( 'c2' , ip='10.0.0.4/24', defaultRoute='via 10.0.0.254' )

        # verdieping 2
        switch4 = self.addSwitch( 's4' , dpid='0000000000000004', cls=OVSSwitch, protocols='OpenFlow13')
        host5 = self.addHost( 'h5', ip='0.0.0.0' ) # Management vlan

        # verdieping 3
        switch5 = self.addSwitch( 's5' , dpid='0000000000000005', cls=OVSSwitch, protocols='OpenFlow13')
        host6 = self.addHost( 'h6', ip='0.0.0.0' ) # Guest vlan

        # overig
        isp = self.addHost( 'isp', ip='221.1.1.1/28', defaultRoute='via 221.1.1.3' )

        # Add NAT node to connect the networks
        nat1 = self.addNode('nat1', cls=NAT, ip='10.0.0.1/24', defaultRoute='via 10.0.0.254')
        nat2 = self.addNode('nat2', cls=NAT, ip='10.0.0.2/24', defaultRoute='via 10.0.0.254')
        # Add links
        self.addLink( switch1, host1, port1=1, port2=1 )
        self.addLink( switch1, DHCP_Vlan1, port1=18, port2=1 )
        self.addLink( switch1, DHCP_Vlan2, port1=19, port2=1 )
        self.addLink( switch1, DHCP_Vlan3, port1=20, port2=1 )
        self.addLink( switch1, switch3, port1=21, port2=24 )
        self.addLink( switch1 , controller, port1=22, port2=1 )
        self.addLink( switch1, nat1, port1=23, port2=1 )        
        self.addLink( switch1, switch2, port1=24, port2=24 )

        self.addLink( switch2, host2, port1=1, port2=1 )
        self.addLink( switch2, host3, port1=2, port2=1 )

        self.addLink( switch3, host4, port1=1, port2=1 )
        self.addLink( switch3, c2, port1=2, port2=1 )
        self.addLink( switch3, nat2, port1=21, port2=1 )
        self.addLink( switch3, switch5, port1=22, port2=24 )
        self.addLink( switch3, switch4, port1=23, port2=24 )

        self.addLink( switch4, host5, port1=1, port2=1 )

        self.addLink( switch5, host6, port1=1, port2=1 )

        self.addLink( nat1, isp, port1=2, port2=1 )
        self.addLink( nat2, isp, port1=2, port2=2 )



def run():
    topo = MyTopo()
    net = Mininet(topo=topo, controller=None, switch=OVSSwitch, autoSetMacs=True)
    net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)
    net.start()

    nat1_node = net.get('nat1')
    nat2_node = net.get('nat2')
    isp_node = net.get('isp')
    isp_node.cmd('ifconfig isp-eth2 221.1.1.2/28')
    nat1_node.cmd('ifconfig nat1-eth2 221.1.1.3/28')
    nat2_node.cmd('ifconfig nat2-eth2 221.1.1.4/28')

    DHCP_Vlan1 = net.get('dhcp1')
    DHCP_Vlan2 = net.get('dhcp2')
    DHCP_Vlan3 = net.get('dhcp3')
    DHCP_Vlan1.cmd('dnsmasq --interface=dhcp1-eth1 --bind-interfaces --dhcp-range=10.0.100.11,10.0.100.200,12h --dhcp-sequential-ip --dhcp-option=3,10.0.100.254 --dhcp-option=6,8.8.8.8 --no-daemon &')
    DHCP_Vlan2.cmd('dnsmasq --interface=dhcp2-eth1 --bind-interfaces --dhcp-range=10.0.200.11,10.0.200.200,12h --dhcp-sequential-ip --dhcp-option=3,10.0.200.254 --dhcp-option=6,8.8.8.8 --no-daemon &')
    DHCP_Vlan3.cmd('dnsmasq --interface=dhcp3-eth1 --bind-interfaces --dhcp-range=10.0.0.11,10.0.0.200,12h --dhcp-sequential-ip --dhcp-option=3,10.0.0.254 --dhcp-option=6,8.8.8.8 --no-daemon &')

    time.sleep(2)  # wait a bit for DHCP servers to start
    dhcp_client_names = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
    for name in dhcp_client_names:
        host = net.get(name)
        # use eth1 inside each Mininet host
        host.cmd('dhclient -v %s-eth1 &' % name)

    CLI(net)
    # DHCP blijft draaien op de VM zelf dus kill the process
    DHCP_Vlan1.cmd('sudo pkill dnsmasq')
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()
