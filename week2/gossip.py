"""Week 2 - Part B: gossip protocol.

Every few seconds each node tells a few random neighbours:
  1. how busy it is (CPU % and RAM %), and
  2. a handful of other peers it knows.
News spreads through the mesh like a rumour, so nobody needs a central database.
(The CPU/RAM numbers ride along in every message; see DHTNode.send.)
"""
import asyncio
import random

try:
    import psutil
except ImportError:
    psutil = None


def read_load():
    """Return (cpu %, ram %) of this computer."""
    if psutil:
        return psutil.cpu_percent(interval=None), psutil.virtual_memory().percent
    return random.uniform(5, 60), 0.0   # stand-in if psutil is missing


async def gossip_loop(node, interval=5):
    read_load()                              # first call primes psutil's counter
    while True:
        await asyncio.sleep(interval)
        node.cpu, node.ram = read_load()     # Step 1: measure ourselves
        peers = list(node.peers.values())

        if not peers and node.bootstrap:     # Step 2: lonely? try the bootstrap again
            node.join()
            continue

        known = [[p.host, p.port] for p in random.sample(peers, min(10, len(peers)))]
        for p in random.sample(peers, min(3, len(peers))):   # Step 3: pick 3 neighbours
            node.send({"type": "STATE", "peers": known}, p.key)  # Step 4: tell them
