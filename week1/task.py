import asyncio
import struct
import sys

import cloudpickle


async def send_msg(writer, data: bytes):
    writer.write(struct.pack("!I", len(data)) + data)   # [4-byte length][data]
    await writer.drain()


async def read_msg(reader) -> bytes:
    (length,) = struct.unpack("!I", await reader.readexactly(4))
    return await reader.readexactly(length)


# ---------------- RECEIVER ----------------
async def handle(reader, writer):
    data = await read_msg(reader)
    func, args = cloudpickle.loads(data)        # rebuild the function
    print(f"running {func.__name__}{args}")
    result = func(*args)                        # execute it
    await send_msg(writer, cloudpickle.dumps(result))
    writer.close()


async def receiver(port):
    server = await asyncio.start_server(handle, "127.0.0.1", port)
    print(f"receiver waiting on TCP {port}")
    async with server:
        await server.serve_forever()


# ---------------- SENDER ----------------
def square_sum(n):
    return sum(i * i for i in range(n))


async def sender(port):
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    payload = cloudpickle.dumps((square_sum, (1000,)))
    await send_msg(writer, payload)
    result = cloudpickle.loads(await read_msg(reader))
    print("result from receiver:", result)
    writer.close()


if __name__ == "__main__":
    role, port = sys.argv[1], int(sys.argv[2])
    try:
        asyncio.run(receiver(port) if role == "receiver" else sender(port))
    except KeyboardInterrupt:
        pass