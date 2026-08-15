from mcstatus import JavaServer, LegacyServer

import asyncio
import ipaddress
import socket

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

app = FastAPI(title="Minecraft Server Scanner")
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
sephamore = asyncio.Semaphore(200)

# added to make sure static website can access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RateLimitExceeded)
async def _rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Rate limit exceeded. Please don't do this."}
    )

def isInternal(ip):
    try:
        address = ipaddress.ip_address(ip)
        return not address.is_global
    except ValueError:
        return True

async def scanJava(address):
    try:
        server = await JavaServer.async_lookup(address)
        status = await server.async_status()

        return {
            "online": True,
            "motd": status.motd,
            "version": status.version.name,
            "protocol": status.version.protocol,
            "players": {
                "online": status.players.online,
                "max": status.players.max
            },
            "playersList": status.players.sample,
            "favicon": status.icon,
        }

    except Exception as e:
        print("JavaServer error:", repr(e))
        return None

async def scanLegacy(address):
    try:
        server = await asyncio.to_thread(LegacyServer.lookup, address)
        status = await server.async_status()

        return {
            "online": True,
            "motd": status.motd,
            "version": status.version.name,
            "protocol": status.version.protocol,
            "players": {
                "online": status.players.online,
                "max": status.players.max
            },
            "favicon": "",
        }
    except Exception as e:
        print("LegacyServer error:", repr(e))
        return None

@app.get("/scan/{address}")
@limiter.limit("5000/hour")
async def scan(request: Request, address: str):
    ip, port = address.rsplit(":", 1)

    if not (0 < int(port) <= 65535) or isInternal(ip):
        raise HTTPException(status_code=400, detail="Invalid address")

    async with sephamore:
        try:
            result = await asyncio.wait_for(scanJava(address), timeout=5)
            if result is not None:
                return result
        except asyncio.TimeoutError:
            pass

        try:
            result = await asyncio.wait_for(scanLegacy(address), timeout=5)
            if result is not None:
                return result
        except asyncio.TimeoutError:
            pass

    return {"online": False}