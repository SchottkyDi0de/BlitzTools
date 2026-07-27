import winreg
from pathlib import Path

class GameLocator:
    def __init__(self):
        pass

    def _normalize_region(self, region: str) -> str:
        return region.lower()

    def _search_registry_install_location(self, region: str = 'ru'):
        region_key = self._normalize_region(region)
        if region_key == 'ru':
            include_keywords = ('Tanks Blitz',)
            exclude_keywords = ('World of Tanks',)
        else:
            include_keywords = ('World of Tanks Blitz',)
            exclude_keywords = ('Lesta',)

        found = []

        for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                key = winreg.OpenKey(hive, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
            except Exception:
                continue
            for i in range(0, 5000):
                try:
                    sub = winreg.EnumKey(key, i)
                    subk = winreg.OpenKey(key, sub)
                    try:
                        display = winreg.QueryValueEx(subk, 'DisplayName')[0]
                    except Exception:
                        display = ''
                    try:
                        install = winreg.QueryValueEx(subk, 'InstallLocation')[0]
                    except Exception:
                        install = ''

                    if 'tanks blitz' in display.lower() or 'tanks blitz' in install.lower():
                        pass

                    has_include = any(kw.lower() in display.lower() for kw in include_keywords)
                    has_exclude = any(kw.lower() in display.lower() for kw in exclude_keywords)

                    if has_include and not has_exclude and install:
                        found.append(Path(install))
                    elif has_include and has_exclude:
                        pass
                except OSError:
                    break

        return found

def get_game_paths_from_regedit():
    """
    Получает пути к установленным версиям игры World of Tanks Blitz из реестра Windows.
    Возвращает словарь {регион: путь} или пустой словарь, если ничего не найдено.
    """
    locator = GameLocator()
    paths = {}
    regions = ['ru', 'eu']
    for region in regions:
        found_paths = locator._search_registry_install_location(region)
        if found_paths:
            paths[region] = str(found_paths[0])
    return paths


if __name__ == "__main__":
    print(get_game_paths_from_regedit())
