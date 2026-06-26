import asyncio
import base64
import json
import socket
import struct

# what is LEB128???
# https://github.com/mohanson/leb128/blob/master/leb128/__init__.py

def encode(value: int) -> bytes:
    result = bytearray()
    while True:
        b = value & 0x7F
        value = value >> 7

        if value == 0:
            result.append(b)
            return result

        result.append(0x80 | b)
    return bytes(result)

# i dunno even how this works, I just know it works

def decode(data, i):
    result = 0
    shift = 0

    while True:
        b = data[i]
        i += 1
        result |= (b & 0x7F) << shift

        if not (b & 0x80):
            break

        shift += 7
        if shift > 35:
            raise ValueError("VarInt too large")
    return result, i

async def decodeReader(reader):
    result = 0
    shift = 0

    while True:
        raw = await reader.readexactly(1)
        b = raw[0]
        result |= (b & 0x7F) << shift

        if b & 0x80 == 0:
            break

        shift += 7

        if shift > 35:
            raise ValueError("VarInt too large")
    return result

async def readPacket(reader):
    length = await decodeReader(reader)
    return await reader.readexactly(length) # make sure entire message is read

async def ping(host, port, timeout=5):
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout)

        protocol = 67 # could be anything, lol
        bites = host.encode()

        # turns out, this is like a request paylod for 0x00 with protocol, length, payload, port (in 2-byte)
        handshake = (encode(0) + encode(protocol & 0xFFFFFFFF) + encode(len(bites)) + bites + struct.pack(">H", port) + encode(1))

        # packets are (VarInt length, packet data)
        writer.write(encode(len(handshake)) + handshake)
        writer.write(b"\x01\x00")
        await writer.drain()

        packet = await asyncio.wait_for(readPacket(reader), timeout)

        packet_id = packet[0]
        if packet_id != 0:
            raise RuntimeError("Unexpected packet id")

        i = 1
        length, i = decode(packet, i)

        response = packet[i:i + length].decode("utf-8")
        data = json.loads(response)

        return {
            "online": True,
            "motd": data.get("description"),
            "version": data.get("version", {}).get("name"),
            "protocol": data.get("version", {}).get("protocol"),
            "players_online": data.get("players", {}).get("online"),
            "players_max": data.get("players", {}).get("max"),
            "favicon": data.get("favicon"),
        }

    except Exception:
        return {"online": False}

    finally:
        if writer:
            writer.close()
            await writer.wait_closed()

async def worker(server, semaphore):
    async with semaphore:
        host, port = server
        result = await ping(host, port)
        return result

async def main():
    servers = [
        ("play.hypixel.net", 25565)
    ]

    semaphore = asyncio.Semaphore(2000)

    tasks = [
        asyncio.create_task(worker(server, semaphore))
        for server in servers
    ]

    results = await asyncio.gather(*tasks)

    print(json.dumps(results, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())