from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info


class MyTopo( Topo ):
    "Simple topology example."

    def build( self ):
        "Create custom topo."

        # Bebouw A
        # verdieping 1
        switch1 = self.addSwitch( 's1' )
        router1 = self.addHost( 'r1' )
        controller = self.addHost( 'c1' )

        # verdieping 2
        switch2 = self.addSwitch( 's2' )
        host1 = self.addHost( 'h1' )

        # Add links
        self.addLink( switch1, switch2 )
        self.addLink( switch1, router1 )
        self.addLink( switch1 , controller )

        self.addLink( switch2, host1 )




def run():
    topo = MyTopo()
    net = Mininet(topo=topo, switch=OVSSwitch, controller=RemoteController)
    net.start()
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()