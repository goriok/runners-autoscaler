"""Module to interact with Bitbucket APIs:
    authentication, basic bitbucket api, bitbucket repositories, bitbucket workspaces
"""
import os
import urllib.parse

from oauthlib.oauth2 import BackendApplicationClient
from requests.auth import HTTPBasicAuth
from requests_oauthlib.oauth2_session import OAuth2Session

from autoscaler.clients.base import BaseAPIService, BearerAuth
from autoscaler.core.exceptions import NotAuthorized
from autoscaler.core.logger import logger


BITBUCKET_BASE_URL = 'https://api.bitbucket.org'
ITEMS_PER_PAGE = 100


class Auth:
    OAUTH_URL = 'https://bitbucket.org/site/oauth2/access_token'

    @classmethod
    def token_oauth(cls):
        client_id = os.getenv('BITBUCKET_OAUTH_CLIENT_ID')
        secret = os.getenv('BITBUCKET_OUATH_CLIENT_SECRET')

        client = BackendApplicationClient(client_id=client_id)
        oauth = OAuth2Session(client=client)
        token = oauth.fetch_token('https://bitbucket.org/site/oauth2/access_token', client_id=client_id,
                                  client_secret=secret)
        logger.info(f"Token expires in {token['expires_in']} seconds")
        return BearerAuth(token['access_token'])

    @classmethod
    def basic_auth(cls):
        username = os.getenv('BITBUCKET_USERNAME')
        app_password = os.getenv('BITBUCKET_APP_PASSWORD')

        if not username or not app_password:
            raise NotAuthorized(
                "Missing BITBUCKET_USERNAME and BITBUCKET_APP_PASSWORD environment variables.")

        return HTTPBasicAuth(username, app_password)


class BitbucketAPIService(BaseAPIService):
    BASE_URL = BITBUCKET_BASE_URL
    MAX_REQUEST_TIMEOUT = 12
    INTERVAL_BEFORE_REQUESTS = 3
    _auth = None

    def __init__(self, auth=None):
        if os.getenv('BITBUCKET_OAUTH_CLIENT_ID') and os.getenv('BITBUCKET_OUATH_CLIENT_SECRET'):
            self._auth = auth or Auth.token_oauth()
        elif os.getenv('BITBUCKET_USERNAME') and os.getenv('BITBUCKET_APP_PASSWORD'):
            self._auth = auth or Auth.basic_auth()
        else:
            raise NotAuthorized("Provide secret credentials to authenticate")

    @property
    def auth(self):
        return self._auth


class BitbucketRepository(BitbucketAPIService):
    MAX_REQUEST_TIMEOUT = 10
    BASE_URL = f'{BITBUCKET_BASE_URL}/2.0/repositories'
    INTERVAL_BEFORE_REQUESTS = 5

    def get_repository(self, workspace, repo_slug, **kwargs):
        if kwargs:
            repo, _ = self.make_http_request(
                f'{self.BASE_URL}/{workspace}/{repo_slug}/?{urllib.parse.urlencode(kwargs)}'
            )
        else:
            repo, _ = self.make_http_request(f'{self.BASE_URL}/{workspace}/{repo_slug}')

        return repo

    def get_raw_content(self, workspace, repo_slug, path, ref='master', **kwargs):
        url = f'{self.BASE_URL}/{workspace}/{repo_slug}/src/{ref}/{path}'
        raw_content, _ = self.make_http_request(url, **kwargs)
        return raw_content


class BitbucketWorkspace(BitbucketAPIService):
    MAX_REQUEST_TIMEOUT = 10
    BASE_URL = f'{BITBUCKET_BASE_URL}/2.0/workspaces'
    INTERVAL_BEFORE_REQUESTS = 5

    def get_workspace(self, workspace_name):
        workspace, _ = self.make_http_request(f'{self.BASE_URL}/{workspace_name}')
        return workspace


class BitbucketWorkspaceRunner(BitbucketAPIService):
    MAX_REQUEST_TIMEOUT = 10
    BASE_URL = f'{BITBUCKET_BASE_URL}/internal/workspaces'
    INTERVAL_BEFORE_REQUESTS = 5

    def get_runner(self, workspace_uuid, runner_uuid):
        url = f'{self.BASE_URL}/{workspace_uuid}/pipelines-config/runners/{runner_uuid}'
        runner, _ = self.make_http_request(url)
        return runner

    def get_runners(self, workspace_uuid):
        runners = []
        url = f'{self.BASE_URL}/{workspace_uuid}/pipelines-config/runners?pagelen={ITEMS_PER_PAGE}'

        while url:
            runners_part, _ = self.make_http_request(url)
            runners.extend(runners_part['values'])
            url = runners_part.get('next')

        return runners

    def create_runner(self, workspace_uuid, name, labels):
        url = f'{self.BASE_URL}/{workspace_uuid}/pipelines-config/runners'
        data = {'name': name, 'labels': labels}
        runner, _ = self.make_http_request(url, method='post', json=data, headers={'Content-Type': 'application/json'})
        return runner

    def delete_runner(self, workspace_uuid, runner_uuid):
        url = f'{self.BASE_URL}/{workspace_uuid}/pipelines-config/runners/{runner_uuid}'
        runner, _ = self.make_http_request(url, method='delete', headers={'Content-Type': 'application/json'})
        return runner


class BitbucketRepositoryRunner(BitbucketAPIService):
    MAX_REQUEST_TIMEOUT = 10
    BASE_URL = f'{BITBUCKET_BASE_URL}/internal/repositories'
    INTERVAL_BEFORE_REQUESTS = 5

    def get_runner(self, workspace_uuid, repo_uuid, runner_uuid):
        url = f'{self.BASE_URL}/{workspace_uuid}/{repo_uuid}/pipelines-config/runners/{runner_uuid}'
        runner, _ = self.make_http_request(url)
        return runner

    def get_runners(self, workspace_uuid, repo_uuid):
        runners = []
        url = f'{self.BASE_URL}/{workspace_uuid}/{repo_uuid}/pipelines-config/runners?pagelen={ITEMS_PER_PAGE}'

        while url:
            runners_part, _ = self.make_http_request(url)
            runners.extend(runners_part['values'])
            url = runners_part.get('next')

        return runners

    def create_runner(self, workspace_uuid, repo_uuid, name, labels):
        url = f'{self.BASE_URL}/{workspace_uuid}/{repo_uuid}/pipelines-config/runners'
        data = {'name': name, 'labels': labels}
        runner, _ = self.make_http_request(url, method='post', json=data, headers={'Content-Type': 'application/json'})
        return runner

    def delete_runner(self, workspace_uuid, repo_uuid, runner_uuid):
        url = f'{self.BASE_URL}/{workspace_uuid}/{repo_uuid}/pipelines-config/runners/{runner_uuid}'
        runner, _ = self.make_http_request(url, method='delete', headers={'Content-Type': 'application/json'})
        return runner
