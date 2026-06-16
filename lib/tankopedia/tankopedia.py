import ast
import requests

from the_retry import retry
from functools import lru_cache

from .exceptions import *
from .data_classes import *

class Tankopedia:
    def __init__(self, region: str):
        if region.lower() in ["ru", "lesta"]:
            self.region = "ru"
        else:
            self.region = "eu"
        self.ru = "https://armor.wotinspector.com/static/armorinspector/tank_db_tanksblitz.js"
        self.eu = "https://armor.wotinspector.com/static/armorinspector/tank_db_blitz.js"


    @lru_cache(maxsize=5)
    @retry(
        expected_exception = [
            requests.exceptions.RequestException
        ],
        attempts = 3
    )
    def _get_data(self):
        _link = self.ru if self.region == "ru" else self.eu
        response = requests.get(_link)
        text = response.text[10:]
        return ast.literal_eval(text)


    def _format_tanks(self, data: dict):
        types = {0: "LT", 1: "MT", 2: "HT", 3: "AT-SPG"}
        result = {}

        for tank_id, tank in data.items():
            tags = tank["tags"]
            result[str(tank_id)] = {
                "id": tank_id,
                "en_name": tank["en"],
                "ru_name": tank["ru"],
                "level": tank["tier"],
                "category": types[tank["type"]],
                "is_premium": bool(tank["premium"]),
                "is_collectible": "collectible" in tags,
                "is_secret": "secret" in tags
            }

        return result


    def _validate_tanks(self, data: dict):
        return [TankData(**data[item]) for item in data]


    def _get_validated_data(self):
        data = self._get_data()
        formatted_data = self._format_tanks(data)
        validated_data = self._validate_tanks(formatted_data)
        return validated_data


    def get_tanks_data(
            self,
            secret: bool = None,
            collectible: bool = None,
            premium: bool = None,
            level: int | None = None,
            category: str | None = None
    ) -> list[TankData]:
        data = self._get_validated_data()
        result = []

        for tank in data:
            # фильтр по level
            if level is not None and tank.level != level:
                continue

            # фильтр по category
            if category is not None and tank.category != category:
                continue

            # фильтр по типам
            if secret is not None and tank.is_secret != secret:
                continue

            if collectible is not None and tank.is_collectible != collectible:
                continue

            if premium is not None and tank.is_premium != premium:
                continue

            result.append(tank)

        return result


    def get_total_tanks(self, level: set[int] | list[int] | int | None = None) -> int:
        data = self._get_validated_data()
        if level is None:
            return len(data)
        elif isinstance(level, int):
            return len([tank for tank in data if tank.level == level])
        elif isinstance(level, set) or isinstance(level, list):
            return len([tank for tank in data if tank.level in level])
        return []


    def get_tank_by_id(self, _id: int) -> TankData | None: 
        data = self._get_validated_data()
        for tank_data in data:
            if tank_data.id == _id:
                return tank_data
        return None


    def get_tank_by_name(self, ru_name: str | None = None, en_name: str | None = None) -> TankData | None:
        if ru_name is None and en_name is None:
            raise NameNotSpecified("ru_name or en_name either was not specified.")
        data = self._get_validated_data()
        for tank_data in data:
            if (ru_name is not None and tank_data.ru_name == ru_name) \
            or (ru_name is not None and tank_data.ru_name.startswith(ru_name)):
                return tank_data
            if (en_name is not None and tank_data.en_name == en_name) \
                or (en_name is not None and tank_data.en_name.startswith(en_name)):
                return tank_data
        return None
