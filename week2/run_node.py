"""Run one mesh node.

First node:   python week2/run_node.py 9000
Other nodes:  python week2/run_node.py 9001 --bootstrap 9000
              python week2/run_node.py 9002 --bootstrap 9000
"""
import argparse
import asyncio
import time

from dht import DHTNode
from gossip import gossip_loop, read_load


async def main(port, bootstrap_port, interval):
    loop = asyncio.get_running_loop()
    bootstrap = ("127.0.0.1", bootstrap_port) if bootstrap_port else None
    node = DHTNode("127.0.0.1", port, bootstrap)
    await loop.create_datagram_endpoint(lambda: node, local_addr=("127.0.0.1", port))
    node.cpu, node.ram = read_load()
    print(f"[{port}] node started" + (f", bootstrap = {bootstrap_port}" if bootstrap else ""))
    if bootstrap:
        node.join()
    asyncio.create_task(gossip_loop(node, interval))

    while True:                                   # print what we know every cycle
        await asyncio.sleep(interval)
        print(f"\n--- node {port}: knows {len(node.peers)} peers "
              f"(my cpu {node.cpu:.0f}%, ram {node.ram:.0f}%) ---")
        for p in sorted(node.peers.values(), key=lambda p: p.port):
            print(f"   port {p.port}  cpu {p.cpu:5.1f}%  ram {p.ram:5.1f}%  "
                  f"seen {time.time() - p.last_seen:.0f}s ago")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("port", type=int)
    ap.add_argument("--bootstrap", type=int, help="port of ANY running node")
    ap.add_argument("--interval", type=float, default=5, help="gossip seconds")
    a = ap.parse_args()
    try:
        asyncio.run(main(a.port, a.bootstrap, a.interval))
    except KeyboardInterrupt:
        pass
