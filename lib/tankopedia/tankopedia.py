from lib.api import BlitzAPI

from .exceptions import NameNotSpecified
from .data_classes import TankData


class Tankopedia:
    def __init__(self, region: str, api: BlitzAPI | None = None):
        if region.lower() in ["ru", "lesta"]:
            self.region = "ru"
        else:
            self.region = "eu"
        self.api = api or BlitzAPI()
        self._cache: list[TankData] | None = None

    def _get_validated_data(self) -> list[TankData]:
        if self._cache is None:
            self._cache = self.api.get_tanks(self.region)
        return self._cache

    def get_tanks_data(
        self,
        secret: bool | None = None,
        collectible: bool | None = None,
        premium: bool | None = None,
        level: int | None = None,
        category: str | None = None,
    ) -> list[TankData]:
        if any(value is not None for value in (secret, collectible, premium, level, category)):
            return self.api.get_tanks(
                self.region,
                secret=secret,
                collectible=collectible,
                premium=premium,
                level=level,
                category=category,
            )

        return list(self._get_validated_data())

    def get_total_tanks(self, level: set[int] | list[int] | int | None = None) -> int:
        if level is None:
            return self.api.get_tanks_count(self.region)

        if isinstance(level, int):
            return self.api.get_tanks_count(self.region, level=level)

        if isinstance(level, (set, list)):
            data = self._get_validated_data()
            return len([tank for tank in data if tank.level in level])

        return 0

    def get_tank_by_id(self, _id: int) -> TankData | None:
        data = self._get_validated_data()
        for tank_data in data:
            if tank_data.id == _id:
                return tank_data
        return self.api.get_tank_by_id(self.region, _id)

    def get_tank_by_name(
        self,
        ru_name: str | None = None,
        en_name: str | None = None,
    ) -> TankData | None:
        if ru_name is None and en_name is None:
            raise NameNotSpecified("ru_name or en_name either was not specified.")

        data = self._get_validated_data()
        for tank_data in data:
            if ru_name is not None and (
                tank_data.ru_name == ru_name or tank_data.ru_name.startswith(ru_name)
            ):
                return tank_data
            if en_name is not None and (
                tank_data.en_name == en_name or tank_data.en_name.startswith(en_name)
            ):
                return tank_data

        return self.api.search_tank(self.region, ru_name=ru_name, en_name=en_name)
