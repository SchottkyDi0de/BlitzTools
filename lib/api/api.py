import aiohttp
from cacheout import Cache

API_SERVER = "http://localhost:8000"
TIMEOUT = 10

class BlitzAPI:
    def __init__(self):
        self.cache = Cache(maxsize=100, ttl=600)
