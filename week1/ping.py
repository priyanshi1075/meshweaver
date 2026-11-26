import asyncio
import sys


class PingProtocol(asyncio.DatagramProtocol):
    def connection_made(self, transport):
        self.transport = transport              # socket is open and ready

    def datagram_received(self, data, addr):
        message = data.decode()
        print(f"received {message!r} from {addr}")
        if message.startswith("PING"):
            self.transport.sendto(b"PONG", addr)   # answer back


async def main(my_port, other_port):
    loop = asyncio.get_running_loop()
    transport, _ = await loop.create_datagram_endpoint(
        PingProtocol, local_addr=("127.0.0.1", my_port))
    print(f"listening on UDP {my_port}")
    count = 0
    while True:
        count += 1
        transport.sendto(f"PING {count}".encode(), ("127.0.0.1", other_port))
        await asyncio.sleep(2)


if __name__ == "__main__":
    try:
        asyncio.run(main(int(sys.argv[1]), int(sys.argv[2])))
    except KeyboardInterrupt:
        pass