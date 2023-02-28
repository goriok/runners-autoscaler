"""Basic client API classes to be inherited from"""
from json.decoder import JSONDecodeError

import requests
from requests.auth import AuthBase

from autoscaler.core.exceptions import AutoscalerHTTPError
from autoscaler.core.logger import logger


class BearerAuth(AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers['Authorization'] = f'Bearer {self.token}'
        return r


class BaseAPIService:
    MAX_REQUEST_TIMEOUT = 5
    RETRY_AFTER_DEFAULT = 10
    DEFAULT_HEADERS = {'User-Agent': 'Bitbucket Runners Autoscaler'}
    _auth = None

    def make_http_request(self, url, method='get', json=None, headers=None, ignore_exc=None, **kwargs):
        if headers:
            headers.update(self.DEFAULT_HEADERS)
        else:
            headers = self.DEFAULT_HEADERS

        with requests.request(method, url, auth=self._auth, json=json, headers=headers,
                              timeout=self.MAX_REQUEST_TIMEOUT, **kwargs) as response:
            logger.debug(f"{method.upper()} request to {url}")
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as exc:
                logger.debug(f"Got {exc}. Status: {response.status_code}")
                if ignore_exc is None or (response.status_code not in ignore_exc):
                    raise AutoscalerHTTPError(response.text, status_code=response.status_code)

                if ignore_exc and response.status_code in ignore_exc:
                    logger.warning(f"Obtained status {response.status_code} for {url}. Ignoring...")

            try:
                data = response.json()
            except JSONDecodeError:
                data = response.text
        return data, response.status_code
