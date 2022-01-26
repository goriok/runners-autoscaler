"""Basic client API classes to be inherited from"""

import subprocess
from subprocess import Popen, PIPE
from json.decoder import JSONDecodeError

import requests
from requests.auth import HTTPBasicAuth

from autoscaler.core.helpers import fail
from autoscaler.core.logger import logger
from autoscaler.core.exceptions import PipesHTTPError


BITBUCKET_BASE_URL = 'https://api.bitbucket.org'


class BearerAuth(HTTPBasicAuth):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers['Authorization'] = f'Bearer {self.token}'
        return r


class BaseAPIService:
    MAX_REQUEST_TIMEOUT = 5
    RETRY_AFTER_DEFAULT = 10
    _auth = None

    def make_http_request(self, url, method='get', json=None, headers=None, ignore_exc=None, **kwargs):
        with requests.request(method, url, auth=self._auth, json=json, headers=headers,
                              timeout=self.MAX_REQUEST_TIMEOUT, **kwargs) as response:
            logger.debug(f"{method.upper()} request to {url}")
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as exc:
                logger.debug(f"Got {exc}. Status: {response.status_code}")
                if ignore_exc is None or (response.status_code not in ignore_exc):
                    raise PipesHTTPError(response.text, status_code=response.status_code)

                if ignore_exc and response.status_code in ignore_exc:
                    logger.warning(f"Obtained status {response.status_code} for {url}. Ignoring...")

            try:
                data = response.json()
            except JSONDecodeError:
                data = response.text
        return data, response.status_code


class BaseSubprocessAPIService:
    BASE_CLI = "kubectl"
    MAX_SUBPROCESS_TIMEOUT = 10

    def run_command(self, command, fail_if_error=True):
        logger.debug(f"RUN command: {' '.join(command)}")

        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=self.MAX_SUBPROCESS_TIMEOUT)
            result.check_returncode()
        except subprocess.CalledProcessError as exc:
            msg = f"Command: {' '.join(command)}.\nOutput: {exc.stderr}"
            if fail_if_error:
                logger.error(msg)
                fail(f"Return code: {exc.returncode}")
            else:
                logger.warning(msg)

        return result.stdout, result.returncode

    def run_piped_command(self, command_1, command_2):
        p1 = Popen(command_1, stdout=PIPE)
        p2 = Popen(command_2, stdin=p1.stdout, stdout=PIPE)
        p1.stdout.close()

        output = p2.communicate()[0]

        if p2.returncode != 0:
            fail(f"Subprocess: Return code for command: {p2.returncode}")

        return output
