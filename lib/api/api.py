import random
import string
import asyncio
import requests
import threading
import webbrowser

from the_retry import retry

from lib.tankopedia.data_classes import TankData
from lib.config.handler import ConfigHandler
from lib.api.models import AccountSearchItem, AccountStatsItem, TankStats
from utils.singleton_factory import singleton

# Legacy root endpoint; switch to "/versions/blitztools" when API is updated.
_VERSION_PATH = "/version"


def generate_token(size: int = 10) -> str:
    symbols = string.ascii_letters + string.digits
    return ''.join(random.choice(symbols) for _ in range(size))

@singleton
class BlitzAPI:
    def __init__(self):
        self.config = ConfigHandler()
        self.base_url = self.config.config.api.base_url.rstrip("/")
        self.timeout = self.config.config.api.timeout
        self.token_data = {}

    @retry(
        expected_exception=[requests.exceptions.RequestException],
        attempts=3,
    )
    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{path}"
        response = requests.request(method, url, timeout=self.timeout, **kwargs)
        return response

    def get_tanks(
        self,
        region: str,
        *,
        secret: bool | None = None,
        collectible: bool | None = None,
        premium: bool | None = None,
        level: int | None = None,
        category: str | None = None,
    ) -> list[TankData]:
        params = {
            key: value
            for key, value in {
                "secret": secret,
                "collectible": collectible,
                "premium": premium,
                "level": level,
                "category": category,
            }.items()
            if value is not None
        }
        response = self._request("GET", f"/tankopedia/{region}/tanks", params=params)
        response.raise_for_status()
        return [TankData(**item) for item in response.json()]

    def get_tanks_count(self, region: str, level: int | None = None) -> int:
        params = {"level": level} if level is not None else None
        response = self._request("GET", f"/tankopedia/{region}/tanks/count", params=params)
        response.raise_for_status()
        return response.json()["count"]

    def get_tank_by_id(self, region: str, tank_id: int) -> TankData | None:
        response = self._request("GET", f"/tankopedia/{region}/tanks/{tank_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return TankData(**response.json())

    def search_tank(
        self,
        region: str,
        *,
        ru_name: str | None = None,
        en_name: str | None = None,
    ) -> TankData | None:
        params = {
            key: value
            for key, value in {"ru_name": ru_name, "en_name": en_name}.items()
            if value is not None
        }
        response = self._request("GET", f"/tankopedia/{region}/tanks/search", params=params)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return TankData(**response.json())

    def get_version(self) -> str:
        try:
            if _VERSION_PATH == "/version":
                server_root = self.base_url.removesuffix("/api/v1").rstrip("/")
                response = requests.get(
                    f"{server_root}{_VERSION_PATH}",
                    timeout=self.timeout,
                )
            else:
                response = self._request("GET", _VERSION_PATH)
            response.raise_for_status()
            version = response.json().get("version")
            return version if isinstance(version, str) else "?.?.?"
        except requests.RequestException:
            return "?.?.?"

    # --- accounts ---

    def search_accounts(
        self,
        region: str,
        *,
        nickname: str,
        search_type: str = "startswith",
        limit: int = 10,
    ) -> list[AccountSearchItem]:
        """GET /accounts/{region}/search"""
        params = {
            "nickname": nickname,
            "search_type": search_type,
            "limit": limit,
        }
        response = self._request("GET", f"/accounts/{region}/search", params=params)
        response.raise_for_status()
        return [AccountSearchItem(**item) for item in response.json()]

    def get_accounts_stats(
        self,
        region: str,
        *,
        ids: list[int] | str,
        access_token: str | None = None,
    ) -> list[AccountStatsItem]:
        """GET /accounts/{region}/stats — ids: comma-separated account IDs."""
        params = {
            "ids": ",".join(map(str, ids)) if isinstance(ids, list) else ids,
            "access_token": access_token or "",
        }
        response = self._request("GET", f"/accounts/{region}/stats", params=params)
        response.raise_for_status()
        json_data = response.json()
        accounts = []
        for item in json_data:
            user_data = item.get("stats", {}).get("data", {})
            accounts.append(AccountStatsItem(**user_data))
        return accounts

    def get_account_tank_stats(
        self,
        region: str,
        account_id: int,
        *,
        tank_ids: list[int] | str,
    ) -> list[TankStats]:
        """GET /accounts/{region}/{account_id}/tanks/stats — tank_ids: comma-separated tank IDs."""
        params = {
            "tank_ids": ",".join(map(str, tank_ids)) if isinstance(tank_ids, list) else tank_ids,
        }
        response = self._request(
            "GET", f"/accounts/{region}/{account_id}/tanks/stats", params=params
        )
        response.raise_for_status()
        return [TankStats(**item) for item in response.json()]

    # --- access_tokens ---

    def _validate_authorization(self, url: str) -> tuple[int, dict]:
        response = self._request("GET", url)
        response.raise_for_status()
        data = response.json()
        status = data.get("status")

        match status:
            case "success":
                return 0, data
            case "pending":
                return 1, data
            case "cancelled":
                return 2, data
            case "not_found":
                return 3, data
            case _:
                return 4, data

    async def _validate_cycle(self, url: str) -> dict:
        retries = 5
        while True:
            code, data = self._validate_authorization(url)

            match code:
                case 0:
                    self.token_data = data
                    return data
                case 1:
                    await asyncio.sleep(0.5)
                    continue
                case 2:
                    return data
                case 3:
                    retries -= 1
                    if retries == 0:
                        return data
                case 4:
                    raise TypeError("Unknown status detected.")

    def authorize(self, region: str) -> None:
        """GET /access_tokens/{region}/authorize"""
        local_token = generate_token()
        url = f"{self.base_url}/access_tokens/{region}/authorize?local_token={local_token}"
        webbrowser.open(url)
        cycle_url = f"/access_tokens/{region}/get_local_token?local_token={local_token}"
        asyncio.run(self._validate_cycle(url = cycle_url))
