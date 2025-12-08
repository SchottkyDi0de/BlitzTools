from kivy import Logger
from lib.locales.handler import get_supported_locales

_log = Logger


def run():
    _log.info('Tests: testing locales access...')
    available_locales = get_supported_locales()
    assert (len(available_locales) > 0), 'locales not found!'
    
    _log.info(f'Tests: locales test passed!, found locales: {available_locales}')
