from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSSwitch
from mininet.nodelib import NAT
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.node import Node
import time

# OVSBridge voor 500 bench test
from mininet.node import OVSBridge

        
# NAT 2 kan inprincipe weg, maar kan later wel geen hoge prio

class MyTopo( Topo ):
    "Simple topology example."

    def build( self ):
        "Create custom topo."

        # Bebouw A
        # verdieping 1
        switch1 = self.addSwitch( 's1' , dpid='0000000000000001', cls=OVSSwitch, protocols='OpenFlow13')
        controller = self.addHost( 'c1' , ip='10.0.0.3/24', defaultRoute='via 10.0.0.254' )
        # leave h1 without a static IP so it can receive one via DHCP
        host1 = self.addHost( 'h1', ip='0.0.0.0') # Host op office vlan

        DHCP_Vlan1 = self.addHost( 'dhcp1', ip='10.0.100.10/24', defaultRoute='via 10.0.100.254' )
        DHCP_Vlan2 = self.addHost( 'dhcp2', ip='10.0.200.10/24', defaultRoute='via 10.0.200.254' )
        DHCP_Vlan3 = self.addHost( 'dhcp3', ip='10.0.0.10/24', defaultRoute='via 10.0.0.254' )

        # verdieping 2
        switch2 = self.addSwitch( 's2' , dpid='0000000000000002', cls=OVSSwitch, protocols='OpenFlow13')
        host2 = self.addHost( 'h2', ip='0.0.0.0') # Office vlan
        host3 = self.addHost( 'h3', ip='0.0.0.0' ) # Guest vlan

        # gebouw B
        # verdieping 1
        switch3 = self.addSwitch( 's3' , dpid='0000000000000003', cls=OVSSwitch, protocols='OpenFlow13')
        host4 = self.addHost( 'h4', ip='0.0.0.0' ) # office vHost1 (Office vlan)lan
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

        # Fanout-switches voor schaaltest maakt gebruik van OVSBridghe letterlijk een domme switch geen bullshit!
        fan_office = self.addSwitch('f1', cls=OVSBridge)
        fan_guest  = self.addSwitch('f2', cls=OVSBridge)
        # Koppel fanouts aan de nieuwe access-poorten
        # - s2-eth3 => native_vlan office
        # - s5-eth3 => native_vlan guest
        self.addLink(switch2, fan_office, port1=3)  # s2-eth3
        self.addLink(switch5, fan_guest,  port1=3)  # s5-eth3

        # Maak veel hosts achter de fanouts
        office_count = 250
        guest_count  = 250

#        for i in range(1, office_count + 1):
#            h = self.addHost(f'of{i}', ip='0.0.0.0')
#            self.addLink(fan_office, h)

#        for i in range(1, guest_count + 1):
#            h = self.addHost(f'gf{i}', ip='0.0.0.0')
#            self.addLink(fan_guest, h)




def run():
    topo = MyTopo()
    net = Mininet(topo=topo, controller=None, switch=OVSSwitch, autoSetMacs=True)
    net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)
    net.start()
        # ---- Dynamisch de juiste interface-namen opzoeken kan later weg wnr naam duidelijk zijn was heel irritant ----
    def intf_to_peer(node, peername):
        "Geef de interface-naam terug die naar 'peername' gaat."
        for intf in node.intfList():
            link = intf.link
            if not link:
                continue
            # kies de andere kant van de link
            other = link.intf1 if link.intf1.node != node else link.intf2
            if other.node.name == peername:
                return intf.name
        return None

    nat1_node = net.get('nat1')
    nat2_node = net.get('nat2')
    isp_node  = net.get('isp')
    c1_node  = net.get('c1')
    c2_node  = net.get('c2')

    # NAT1: LAN=link naar s1, WAN=link naar isp
    nat1_lan = intf_to_peer(nat1_node, 's1')
    nat1_wan = intf_to_peer(nat1_node, 'isp')

    # NAT2: LAN=link naar s3, WAN=link naar isp
    nat2_lan = intf_to_peer(nat2_node, 's3')
    nat2_wan = intf_to_peer(nat2_node, 'isp')

    # ISP: interface naar nat1 en naar nat2
    isp_to_nat1 = intf_to_peer(isp_node, 'nat1')
    isp_to_nat2 = intf_to_peer(isp_node, 'nat2')

    # Voor debug: print de namen (optioneel)
    print('NAT1 LAN:', nat1_lan, 'WAN:', nat1_wan)
    print('NAT2 LAN:', nat2_lan, 'WAN:', nat2_wan)
    print('ISP -> nat1:', isp_to_nat1, 'ISP -> nat2:', isp_to_nat2)

    # ---- Adressering correct zetten met 'replace' (idempotent) ----
    # ISP: zet 221.1.1.1 op de link naar nat1 en 221.1.1.2 naar nat2
    isp_node.cmd(f'ip addr flush dev {isp_to_nat1}; ip addr add 221.1.1.1/28 dev {isp_to_nat1}')
    isp_node.cmd(f'ip addr flush dev {isp_to_nat2}; ip addr add 221.1.1.2/28 dev {isp_to_nat2}')

    # NAT1: LAN=10.0.0.1/24, WAN=221.1.1.3/28, default via 221.1.1.1
    nat1_node.cmd(f'ip addr replace 10.0.0.1/24 dev {nat1_lan}')
    nat1_node.cmd(f'ip addr replace 221.1.1.3/28 dev {nat1_wan}')
    nat1_node.cmd(f'ip route replace default via 221.1.1.1 dev {nat1_wan}')

    # new
    nat1_node.cmd(f'ip route replace 10.0.100.0/24 via 10.0.0.254 dev {nat1_lan}')
    nat1_node.cmd(f'ip route replace 10.0.200.0/24 via 10.0.0.254 dev {nat1_lan}')

    # NAT2: LAN=10.0.0.2/24, WAN=221.1.1.4/28, default via 221.1.1.2 (mag als standby)
    nat2_node.cmd(f'ip addr replace 10.0.0.2/24 dev {nat2_lan}')
    nat2_node.cmd(f'ip addr replace 221.1.1.4/28 dev {nat2_wan}')
    nat2_node.cmd(f'ip route replace default via 221.1.1.2 dev {nat2_wan}')

    # ---- NAT op NAT1 (idempotent) ----
    nat1_node.cmd('sysctl -w net.ipv4.ip_forward=1')
    nat1_node.cmd('iptables -t nat -F; iptables -F')
    nat1_node.cmd(f'iptables -t nat -A POSTROUTING -o {nat1_wan} -j MASQUERADE')
    nat1_node.cmd(f'iptables -A FORWARD -i {nat1_wan} -o {nat1_lan} -m state --state ESTABLISHED,RELATED -j ACCEPT')
    nat1_node.cmd(f'iptables -A FORWARD -i {nat1_lan} -o {nat1_wan} -j ACCEPT')


    # DHCP range 
    DHCP_Vlan1 = net.get('dhcp1')
    DHCP_Vlan2 = net.get('dhcp2')
    DHCP_Vlan3 = net.get('dhcp3')

    # configue IPv6 addresses

    # find first interface name for each host
    DHCP_Vlan1_if = DHCP_Vlan1.intfList()[0].name
    DHCP_Vlan2_if = DHCP_Vlan2.intfList()[0].name
    DHCP_Vlan3_if = DHCP_Vlan3.intfList()[0].name

    c1_if  = net.get('c1').intfList()[0].name
    c2_if  = net.get('c2').intfList()[0].name
    # flush any existing IPv6 and assign the intended addresses
    DHCP_Vlan1.cmd(f'ip -6 addr flush dev {DHCP_Vlan1_if}; ip -6 addr add fe80::10/64 dev {DHCP_Vlan1_if} scope link; ip -6 addr add 2042:100::10/64 dev {DHCP_Vlan1_if}')
    DHCP_Vlan2.cmd(f'ip -6 addr flush dev {DHCP_Vlan2_if}; ip -6 addr add fe80::20/64 dev {DHCP_Vlan2_if} scope link; ip -6 addr add 2042:200::10/64 dev {DHCP_Vlan2_if}')
    DHCP_Vlan3.cmd(f'ip -6 addr flush dev {DHCP_Vlan3_if}; ip -6 addr add fe80::30/64 dev {DHCP_Vlan3_if} scope link; ip -6 addr add 2042::10/64 dev {DHCP_Vlan3_if}')

    nat1_node.cmd(f'ip -6 addr flush dev {nat1_lan}; ip -6 addr add 2042::1/64 dev {nat1_lan}')
    nat1_node.cmd(f'ip -6 addr flush dev {nat1_wan}; ip -6 addr add 2043::3/64 dev {nat1_wan}')
    nat2_node.cmd(f'ip -6 addr flush dev {nat2_lan}; ip -6 addr add 2042::2/64 dev {nat2_lan}')
    nat2_node.cmd(f'ip -6 addr flush dev {nat2_wan}; ip -6 addr add 2043::4/64 dev {nat2_wan}')
    isp_node.cmd(f'ip -6 addr flush dev {isp_to_nat1}; ip -6 addr add 2043::1/64 dev {isp_to_nat1}')
    isp_node.cmd(f'ip -6 addr flush dev {isp_to_nat2}; ip -6 addr add 2043::2/64 dev {isp_to_nat2}')
    c1_node.cmd(f'ip -6 addr flush dev {c1_if}; ip -6 addr add 2042::3/64 dev {c1_if}')
    c2_node.cmd(f'ip -6 addr flush dev {c2_if}; ip -6 addr add 2042::4/64 dev {c2_if}')
    # set routes for IPv6
    DHCP_Vlan1.cmd(f'ip -6 route replace ff02::1:2/128 dev {DHCP_Vlan1_if} scope link')
    DHCP_Vlan1.cmd(f'ip -6 route replace default via 2042:100::ffff:ffff:ffff:fffe dev {DHCP_Vlan1_if}')
    DHCP_Vlan2.cmd(f'ip -6 route replace ff02::1:2/128 dev {DHCP_Vlan2_if} scope link')
    DHCP_Vlan2.cmd(f'ip -6 route replace default via 2042:200::ffff:ffff:ffff:fffe dev {DHCP_Vlan2_if}')
    DHCP_Vlan3.cmd(f'ip -6 route replace ff02::1:2/128 dev {DHCP_Vlan3_if} scope link')
    DHCP_Vlan3.cmd(f'ip -6 route replace default via 2042::ffff:ffff:ffff:fffe dev {DHCP_Vlan3_if}')

    nat1_node.cmd(f'ip -6 route replace default via 2042::ffff:ffff:ffff:fffe dev {nat1_lan}')
    nat2_node.cmd(f'ip -6 route replace default via 2042::ffff:ffff:ffff:fffe dev {nat2_lan}')
    isp_node.cmd(f'ip -6 route replace default via 2043::3 dev {isp_to_nat1}')
    c1_node.cmd(f'ip -6 route replace default via 2042::ffff:ffff:ffff:fffe dev {c1_if}')
    c2_node.cmd(f'ip -6 route replace default via 2042::ffff:ffff:ffff:fffe dev {c2_if}')
    # enable IPv6 forwarding on NAT nodes
    nat1_node.cmd('sudo sysctl -w net.ipv6.conf.default.forwarding=1')
    nat2_node.cmd('sudo sysctl -w net.ipv6.conf.default.forwarding=1')

    DHCP_Vlan1.cmd('dnsmasq --interface=dhcp1-eth1 --bind-interfaces --dhcp-range=10.0.100.11,10.0.100.250,12h --dhcp-range=2042:100::11,2042:100::ffff,64,12h --dhcp-option=3,10.0.100.254 --dhcp-option=6,8.8.8.8 --dhcp-option=option6:dns-server,[2606:4700:4700::1111] --enable-ra --dhcp-sequential-ip --no-daemon &')
    DHCP_Vlan2.cmd('dnsmasq --interface=dhcp2-eth1 --bind-interfaces --dhcp-range=10.0.200.11,10.0.200.250,12h --dhcp-range=2042:200::11,2042:200::ffff,64,12h --dhcp-option=3,10.0.200.254 --dhcp-option=6,8.8.8.8 --dhcp-option=option6:dns-server,[2606:4700:4700::1111] --enable-ra --dhcp-sequential-ip --no-daemon &')
    DHCP_Vlan3.cmd('dnsmasq --interface=dhcp3-eth1 --bind-interfaces --dhcp-range=10.0.0.11,10.0.0.250,12h --dhcp-range=2042::11,2042::ffff,64,12h --dhcp-option=3,10.0.0.254 --dhcp-option=6,8.8.8.8 --dhcp-option=option6:dns-server,[2606:4700:4700::1111] --enable-ra --dhcp-sequential-ip --no-daemon &')

    time.sleep(2)  # wait a bit for DHCP servers to start

    # Start dhclient PARALLEL en sla speciale nodes over
    skip = ('dhcp', 'nat', 'isp', 'c')  # prefixes overslaan
    for h in net.hosts:
        name = h.name
        if name.startswith(skip):
            continue
        intf = h.intfList()[0].name   # eerste interface
        h.cmd(f'dhclient -1 {intf} & dhclient -6 -1 {intf} &')  # -1 = stop na eerste lease; & = parallel?

    CLI(net)
    # DHCP blijft draaien op de VM zelf dus kill the process
    DHCP_Vlan1.cmd('sudo pkill dnsmasq')
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()
