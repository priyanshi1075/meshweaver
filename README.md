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
| 2 | Kademlia-style DHT for joining and finding peers | Gossip protocol (CPU/RAM every 5 s) | In progress |
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
├── requirements.txt
└── README.md
```

More modules (`dht.py`, `gossip.py`, `heartbeat.py`, `scheduler.py`, `executor.py`, `security.py`, `node.py`, `dashboard.py`) are added as each week is completed.

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

## Security notes

- Deserializing task payloads runs code. Later weeks verify an HMAC signature before any payload is unpickled, so only nodes with the shared secret can send tasks. The Week 1 demo does not do this yet, so run it only on your own machine.

## License

MIT
