from abc import ABC, abstractmethod
import time
from hashlib import sha1
import requests


class RequestsHandler(ABC):
    @abstractmethod
    def get(self, url, headers=None):
        pass

    @abstractmethod
    def post(self, url, json=None, headers=None):
        pass

    @abstractmethod
    def set_cookies(self, cookiejar):
        pass

    @abstractmethod
    def get_cookie(self, name):
        pass

    @staticmethod
    def get_auth_header(sapisid):
        timestring = str(int(time.time()))
        return f"SAPISIDHASH {timestring}_" + sha1(" ".join([timestring, sapisid, "https://www.youtube.com"]).encode()).hexdigest()

    @staticmethod
    def add_authorization_header_from_sapisid(func):
        def wrapper(self, *args, headers=None, **kwargs):
            sapisid = self.get_cookie("SAPISID")

            if sapisid and headers:
                headers["Authorization"] = RequestsHandler.get_auth_header(sapisid)

            return func(self, *args, headers=headers, **kwargs)

        return wrapper


class DefaultRequestsHandler(RequestsHandler):
    def __init__(self):
        self._session = requests.Session()

    @RequestsHandler.add_authorization_header_from_sapisid
    def get(self, url, headers=None):
        return self._session.get(
            url,
            headers=headers,
        )

    @RequestsHandler.add_authorization_header_from_sapisid
    def post(self, url, json=None, headers=None):
        return self._session.post(
            url,
            json=json,
            headers=headers,
        )

    def set_cookies(self, cookiejar):
        self._session.cookies = cookiejar

    def get_cookie(self, name):
        return requests.utils.dict_from_cookiejar(self._session.cookies).get(name)


_requests_handler = DefaultRequestsHandler()


def set_requests_handler(requests_handler):
    global _requests_handler
    _requests_handler = requests_handler


def get_requests_handler():
    return _requests_handler
