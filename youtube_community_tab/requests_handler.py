import os
from requests_cache import CachedSession

dirname = os.path.dirname(__file__)
CACHE_FILE_PATH = os.path.join(dirname, "requests_cache.sqlite")

requests_cache = CachedSession(allowable_methods=("GET", "POST"), cache_name=CACHE_FILE_PATH)
