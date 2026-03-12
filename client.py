"""HTTP клиент к 1С OData с Basic Auth и TTL-кэшем для справочников."""
import httpx
from cachetools import TTLCache
import asyncio
import base64
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("ONEC_BASE_URL", "http://localhost:8080/odata/standard.odata")
LOGIN    = os.getenv("ONEC_LOGIN",    "Администратор")
PASSWORD = os.getenv("ONEC_PASSWORD", "admin")

_auth_header = "Basic " + base64.b64encode(f"{LOGIN}:{PASSWORD}".encode()).decode()

_http: Optional[httpx.AsyncClient] = None
_cache: TTLCache = TTLCache(maxsize=50, ttl=300)  # 5 мин для справочников
_cache_lock = asyncio.Lock()


async def http() -> httpx.AsyncClient:
    global _http
    if _http is None or _http.is_closed:
        _http = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={
                "Authorization": _auth_header,
                "Accept": "application/json",
            },
            timeout=20.0,
        )
    return _http


async def get(path: str, params: dict | None = None) -> dict:
    client = await http()
    r = await client.get(path, params=params or {})
    r.raise_for_status()
    return r.json()


async def post(path: str, body: dict) -> dict:
    client = await http()
    r = await client.post(path, json=body)
    r.raise_for_status()
    return r.json()


async def cached_get(cache_key: str, path: str, params: dict | None = None) -> dict:
    async with _cache_lock:
        if cache_key in _cache:
            return _cache[cache_key]
    result = await get(path, params)
    async with _cache_lock:
        _cache[cache_key] = result
    return result
