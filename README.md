# MeshWeaver: Zero-Dependency P2P Async Task Broker

MeshWeaver is a pure Python, decentralized task queue for distributed and edge computing. Nodes form a peer-to-peer mesh using `asyncio` and a Kademlia-style Distributed Hash Table (DHT). When a node submits a task, the mesh sends it to the peer with the lowest CPU load. If that peer dies, the task is re-routed automatically. There is no central broker (no Redis, no RabbitMQ), so there is no single point of failure.

## Problem

Distributed task queues like Celery need heavy central infrastructure. For edge setups (for example hundreds of Raspberry Pis in the field), a central message broker is a single point of failure and adds a lot of configuration overhead.

## Key modules

- **Asynchronous networking (`asyncio` and sockets):** non-blocking UDP and TCP communication between peer nodes.
- **Distributed Hash Table (Kademlia-style):** nodes discover each other and the network state without a central database.
- **Gossip protocol engine:** nodes broadcast their CPU/RAM load to their nearest neighbours.
- **Task serializer (`cloudpickle`):** Python functions and arguments are serialized, sent over the wire and executed remotely.
- **Fault tolerance:** heartbeat monitoring detects dead nodes and re-routes their tasks.
- **Security:** signed messages (HMAC) and optional TLS.
- **Live dashboard:** a `rich` CLI view of mesh topology and task execution.

## Progress

| Week | Distributed networking | Task execution and reliability | Status |
|---|---|---|---|
| 1 | Base asyncio UDP mesh: two instances ping each other | Task serialization with cloudpickle | Done |
| 2 | Kademlia-style DHT for joining and finding peers | Gossip protocol (CPU/RAM every 5 s) | Done |
| Mid-project | Network audit: 10 local nodes discover each other | Serialization check with a math function | Planned |
| 3 | Route tasks to the lowest-CPU node | Heartbeat monitor and task re-routing | Planned |
| 4 | Signed messages and TLS | Live `rich` CLI dashboard | Planned |
| Final | Decentralized mesh that survives node dropouts | Lightweight deployable package | Planned |

## Project structure

```
meshweaver/
├── week1/
│   ├── ping.py        # two nodes ping each other over UDP (asyncio)
│   └── task.py        # send a function with cloudpickle and run it remotely
├── week2/
│   ├── dht.py         # Kademlia-style peer discovery (XOR distance)
│   ├── gossip.py      # nodes share CPU/RAM load every 5 seconds
│   └── run_node.py    # starts one mesh node
├── requirements.txt
└── README.md
```

More modules ( `heartbeat.py`, `scheduler.py`, `executor.py`, `security.py`, `dashboard.py`) are added as each week is completed.

## Installation

```bash
git clone https://github.com/priyanshi1075/meshweaver.git
cd meshweaver
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac / Linux
pip install -r requirements.txt
```

Requires Python 3.10 or newer. Dependencies: `cloudpickle`, `psutil`, `rich`.

## Usage (Week 1)

**1. UDP ping between two nodes** (two terminals)

```bash
python week1/ping.py 9000 9001
python week1/ping.py 9001 9000
```

The first number is the node's own port and the second is the other node's port. Each node prints the `PING` and `PONG` messages it receives.

**2. Run a function on another process** (two terminals)

```bash
python week1/task.py receiver 9100
python week1/task.py sender 9100
```

The sender packs a function with `cloudpickle` and sends it over TCP. The receiver rebuilds it, runs it and returns the result (`332833500` for the demo function).


## Usage (Week 2)

Start a mesh of nodes, one per terminal. Only the first node is started without a bootstrap. Every other node is given just one existing node's port.

```bash
python week2/run_node.py 9000
python week2/run_node.py 9001 --bootstrap 9000
python week2/run_node.py 9002 --bootstrap 9000
```

Add `--interval 2` to see gossip updates faster. After about 10 seconds, each node prints the peers it has discovered, along with their CPU and RAM usage:

```
--- node 9002: knows 2 peers (my cpu 12%, ram 82%) ---
   port 9000  cpu   13.0%  ram  82.4%  seen 3s ago
   port 9001  cpu   10.2%  ram  82.8%  seen 9s ago
```

### How it works

- **DHT discovery:** a new node contacts only its bootstrap node and sends `FIND_NODE`. The reply lists the peers closest to it by XOR distance. The node pings those peers and asks them the same question, until it knows most of the mesh. No peer list is hardcoded.
- **Gossip:** every 5 seconds each node measures its own CPU and RAM and sends them, plus a sample of known peers, to 3 random neighbours.


## Security notes

- Deserializing task payloads runs code. Later weeks verify an HMAC signature before any payload is unpickled, so only nodes with the shared secret can send tasks. The Week 1 demo does not do this yet, so run it only on your own machine.

## License

MIT

## Known limitations (so far)

- The DHT uses a flat peer table with XOR-distance lookups instead of full k-buckets.
- UDP messages are not signed or encrypted yet, so run the mesh only on a trusted network. Signing and TLS are planned for Week 4.
- Dead nodes are not removed yet. They only show a growing "seen ... ago" time. Heartbeat detection and task re-routing are planned for Week 3.
