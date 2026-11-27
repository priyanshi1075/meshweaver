"""Week 2 - Part A: peer discovery with a Kademlia-style DHT.

A new node only needs the address of ONE existing node (the bootstrap).
It asks that node "who is close to me?", then asks those nodes, and so on,
until it knows most of the mesh. No central server, no hardcoded peer list.
"""
import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field

K = 8  # how many peers we hand out in one answer


def make_id(host, port):
    """Every node gets a 160-bit ID made from its address (like Kademlia)."""
    return int(hashlib.sha1(f"{host}:{port}".encode()).hexdigest(), 16)


@dataclass
class Peer:
    """What we remember about one neighbour."""
    host: str
    port: int
    cpu: float = 0.0
    ram: float = 0.0
    last_seen: float = field(default_factory=time.time)

    @property
    def key(self):
        return (self.host, self.port)

    @property
    def node_id(self):
        return make_id(self.host, self.port)


class DHTNode(asyncio.DatagramProtocol):
    def __init__(self, host, port, bootstrap=None):
        self.host, self.port = host, port
        self.id = make_id(host, port)
        self.bootstrap = bootstrap        # (host, port) of any existing node
        self.peers = {}                   # our routing table: (host, port) -> Peer
        self.cpu, self.ram = 0.0, 0.0     # our own load (gossip.py keeps it fresh)
        self.transport = None

    # ---- Step 1: socket plumbing ----------------------------------------
    def connection_made(self, transport):
        self.transport = transport

    def error_received(self, exc):
        pass  # Windows reports "port unreachable" for dead peers; ignore it

    def datagram_received(self, data, addr):
        try:
            self.on_message(json.loads(data), addr)
        except (ValueError, KeyError):
            pass  # ignore garbage

    def send(self, msg, addr):
        msg.update({"port": self.port, "cpu": self.cpu, "ram": self.ram})
        self.transport.sendto(json.dumps(msg).encode(), addr)

    # ---- Step 2: joining the mesh ---------------------------------------
    def join(self):
        """Say hello to the bootstrap node and ask who is near us."""
        self.send({"type": "PING"}, self.bootstrap)
        self.send({"type": "FIND_NODE", "target": self.id}, self.bootstrap)

    # ---- Step 3: the XOR distance rule ----------------------------------
    def closest(self, target, n=K):
        """Peers whose ID is closest to target (XOR distance, as in Kademlia)."""
        return sorted(self.peers.values(), key=lambda p: p.node_id ^ target)[:n]

    # ---- Step 4: remember who we heard from -----------------------------
    def touch(self, host, port, cpu, ram):
        """Update (or add) a peer. Returns True if it was new to us."""
        if (host, port) == (self.host, self.port):
            return False
        peer = self.peers.get((host, port))
        is_new = peer is None
        if is_new:
            peer = self.peers[(host, port)] = Peer(host, port)
            print(f"[{self.port}] discovered peer {port}")
        peer.cpu, peer.ram, peer.last_seen = cpu, ram, time.time()
        return is_new

    # ---- Step 5: handle every incoming message --------------------------
    def on_message(self, msg, addr):
        host, port = addr[0], msg["port"]
        is_new = self.touch(host, port, msg.get("cpu", 0), msg.get("ram", 0))
        kind = msg["type"]

        if kind == "PING":
            self.send({"type": "PONG"}, (host, port))

        elif kind == "FIND_NODE":
            near = self.closest(msg["target"])
            self.send({"type": "NODES",
                       "peers": [[p.host, p.port] for p in near]}, (host, port))

        # NODES and STATE messages carry a list of peers we may not know yet.
        for h, p in msg.get("peers", []):
            if (h, p) != (self.host, self.port) and (h, p) not in self.peers:
                self.send({"type": "PING"}, (h, p))   # they will PONG -> we learn them

        # A brand-new peer: ask it for ITS neighbours too (keeps the search going)
        if is_new and kind in ("PING", "PONG"):
            self.send({"type": "FIND_NODE", "target": self.id}, (host, port))
