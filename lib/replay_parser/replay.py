import zipfile
from typing import BinaryIO

from .models.battle_results_dat import BattleResultsDat
from .models.data import Data
from .models.meta import Meta
from .models.region import Region
from .types import BattleResults


class Replay:
    def __init__(self, archive: zipfile.ZipFile, region: Region):
        self._archive = archive
        self._region = region

    @classmethod
    def open(cls, reader: BinaryIO, region: Region) -> "Replay":
        return cls(zipfile.ZipFile(reader), region)

    def read_battle_results_dat(self) -> BattleResultsDat:
        with self._archive.open("battle_results.dat") as handle:
            return BattleResultsDat.from_reader(handle)

    def read_battle_results(self) -> BattleResults:
        return self.read_battle_results_dat().decode(self._region)

    def read_meta(self) -> Meta:
        with self._archive.open("meta.json") as handle:
            return Meta.from_reader(handle)

    def read_data(self) -> Data:
        data_name = "data.wotreplay" if self._region == Region.EU else "data.replay"
        with self._archive.open(data_name) as handle:
            return Data.from_reader(handle)

    def close(self) -> None:
        self._archive.close()

    def __enter__(self) -> "Replay":
        return self

    def __exit__(self, *_) -> None:
        self.close()
