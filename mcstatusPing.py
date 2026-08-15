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

@app.get("/scan/{address}")
@limiter.limit("5000/hour")
async def scan(request: Request, address: str):
    ip, port = address.rsplit(":", 1)

    if not (0 < int(port) <= 65535) or isInternal(ip):
        raise HTTPException(status_code=400, detail="Invalid address")

    try:
        server = JavaServer.lookup(address)
        status = await asyncio.to_thread(server.status)

        return {
            "online": True,
            "motd": status.motd,
            "version": status.version.name,
            "protocol": status.version.protocol,
            "players_online": status.players.online,
            "players_max": status.players.max,
            "players_list": status.players.sample,
            "favicon": status.icon,
        }

    except Exception as e:
        print("JavaServer error:", repr(e))

    try:
        server = LegacyServer.lookup(address)
        status = await asyncio.to_thread(server.status)

        return {
            "online": True,
            "motd": status.motd,
            "version": status.version.name,
            "protocol": status.version.protocol,
            "players_online": status.players.online,
            "players_max": status.players.max,
            "favicon": "",
        }
    except Exception as e:
        print("LegacyServer error:", repr(e))
        return {"online": False}