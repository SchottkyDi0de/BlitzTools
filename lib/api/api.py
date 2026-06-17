import requests
from the_retry import retry

from lib.tankopedia.data_classes import TankData
from lib.config.handler import ConfigHandler

class BlitzAPI:
    def __init__(self):
        self.config = ConfigHandler()
        self.base_url = self.config.config.api.base_url.rstrip("/")
        self.timeout = self.config.config.api.timeout

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
        response = self._request("GET", f"/v1/tankopedia/{region}/tanks", params=params)
        response.raise_for_status()
        return [TankData(**item) for item in response.json()]

    def get_tanks_count(self, region: str, level: int | None = None) -> int:
        params = {"level": level} if level is not None else None
        response = self._request("GET", f"/v1/tankopedia/{region}/tanks/count", params=params)
        response.raise_for_status()
        return response.json()["count"]

    def get_tank_by_id(self, region: str, tank_id: int) -> TankData | None:
        response = self._request("GET", f"/v1/tankopedia/{region}/tanks/{tank_id}")
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
        response = self._request("GET", f"/v1/tankopedia/{region}/tanks/search", params=params)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return TankData(**response.json())
