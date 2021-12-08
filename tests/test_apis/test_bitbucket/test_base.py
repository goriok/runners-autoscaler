import os
from unittest import TestCase, mock

import pytest
import requests_oauthlib

from exceptions import NotAuthorized
from apis.bitbucket.base import (Auth, BitbucketAPIService, BitbucketRepository, BitbucketWorkspace,
                                 BitbucketWorkspaceRunner, BitbucketRepositoryRunner)


class BitbucketAPIServiceTestCase(TestCase):

    @mock.patch.dict(os.environ, {'BITBUCKET_USERNAME': 'test', 'BITBUCKET_APP_PASSWORD': 'test'})
    def test_init_bitbucket_service_basic_auth(self):
        api = BitbucketAPIService()
        self.assertEqual(api.auth.username, 'test')
        self.assertEqual(api.auth.password, 'test')

    @mock.patch.object(requests_oauthlib.oauth2_session.OAuth2Session, 'fetch_token')
    @mock.patch.dict(os.environ, {'BITBUCKET_OAUTH_CLIENT_ID': 'test', 'BITBUCKET_OUATH_CLIENT_SECRET': 'test'})
    def test_init_bitbucket_service_token_oauth(self, mock_fetch_token):
        mock_fetch_token.return_value = {'access_token': 'oauthfaketoken.qsadfsf', 'expires_in': 600}
        api = BitbucketAPIService()
        self.assertEqual(api.auth.token, 'oauthfaketoken.qsadfsf')
        mock_fetch_token.assert_called_once_with('https://bitbucket.org/site/oauth2/access_token',
                                                 client_id=os.getenv('BITBUCKET_OAUTH_CLIENT_ID'),
                                                 client_secret=os.getenv('BITBUCKET_OUATH_CLIENT_SECRET'),)

    @mock.patch.dict(os.environ, {'BITBUCKET_USERNAME': 'test', 'BITBUCKET_APP_PASSWORD': ''})
    def test_init_bitbucket_service_unauthorized(self):
        with self.assertRaises(NotAuthorized):
            BitbucketAPIService()


class AuthTestCase(TestCase):

    @mock.patch.dict(os.environ, {'BITBUCKET_USERNAME': 'test', 'BITBUCKET_APP_PASSWORD': ''})
    def test_init_bitbucket_service_unauthorized(self):
        with pytest.raises(NotAuthorized) as pytest_wrapped_e:
            Auth.basic_auth()

        self.assertEqual(pytest_wrapped_e.type, NotAuthorized)
        self.assertIn('Missing BITBUCKET_USERNAME and BITBUCKET_APP_PASSWORD environment variables.',
                      str(pytest_wrapped_e))


@mock.patch.dict(os.environ, {'BITBUCKET_USERNAME': 'test', 'BITBUCKET_APP_PASSWORD': 'test'})
class BitbucketRepositoryTestCase(TestCase):

    @mock.patch.object(BitbucketRepository, 'make_http_request')
    def test_get_repository(self, get_repository_request):
        get_repository_request.return_value = (
            'foo',
            200
        )
        service = BitbucketRepository()
        repo = service.get_repository('foo', 'bar')
        self.assertEqual(
            repo,
            'foo'
        )

    @mock.patch.object(BitbucketRepository, 'make_http_request')
    def test_get_raw_content(self, get_raw_content_request):
        get_raw_content_request.return_value = (
            'foo',
            200
        )
        service = BitbucketRepository()
        result = service.get_raw_content('foo', 'bar', 'baz')
        self.assertEqual(
            result,
            'foo'
        )


@mock.patch.dict(os.environ, {'BITBUCKET_USERNAME': 'test', 'BITBUCKET_APP_PASSWORD': 'test'})
class BitbucketWorkspaceTestCase(TestCase):

    @mock.patch.object(BitbucketWorkspace, 'make_http_request')
    def test_get_workspace(self, get_workspace_request):
        get_workspace_request.return_value = (
            'foo',
            200
        )
        service = BitbucketWorkspace()
        result = service.get_workspace('foo')
        self.assertEqual(
            result,
            'foo'
        )


@mock.patch.dict(os.environ, {'BITBUCKET_USERNAME': 'test', 'BITBUCKET_APP_PASSWORD': 'test'})
class BitbucketWorkspaceRunnerTestCase(TestCase):

    @mock.patch.object(BitbucketWorkspaceRunner, 'make_http_request')
    def test_get_runner(self, get_runner_request):
        get_runner_request.return_value = (
            'foo',
            200
        )
        service = BitbucketWorkspaceRunner()
        result = service.get_runner('foo', 'bar')
        self.assertEqual(
            result,
            'foo'
        )

    @mock.patch.object(BitbucketWorkspaceRunner, 'make_http_request')
    def test_get_runners(self, get_runners_request):
        get_runners_request.return_value = (
            {'values': ['foo', 'bar', 'baz']},
            200
        )
        service = BitbucketWorkspaceRunner()
        result = service.get_runners('foo')
        self.assertEqual(
            result,
            {'values': ['foo', 'bar', 'baz']}
        )

    @mock.patch.object(BitbucketWorkspaceRunner, 'make_http_request')
    def test_create_runner(self, create_runner_request):
        create_runner_request.return_value = (
            'foo',
            200
        )
        service = BitbucketWorkspaceRunner()
        result = service.create_runner('foo', 'bar', ('baz',))
        self.assertEqual(
            result,
            'foo'
        )

    @mock.patch.object(BitbucketWorkspaceRunner, 'make_http_request')
    def test_delete_runner(self, delete_runner_request):
        delete_runner_request.return_value = (
            'foo',
            200
        )
        service = BitbucketWorkspaceRunner()
        result = service.delete_runner('foo', 'bar')
        self.assertEqual(
            result,
            'foo'
        )


@mock.patch.dict(os.environ, {'BITBUCKET_USERNAME': 'test', 'BITBUCKET_APP_PASSWORD': 'test'})
class BitbucketRepositoryRunnerTestCase(TestCase):

    @mock.patch.object(BitbucketRepositoryRunner, 'make_http_request')
    def test_get_runner(self, get_runner_request):
        get_runner_request.return_value = (
            'foo',
            200
        )
        service = BitbucketRepositoryRunner()
        result = service.get_runner('foo', 'bar', 'baz')
        self.assertEqual(
            result,
            'foo'
        )

    @mock.patch.object(BitbucketRepositoryRunner, 'make_http_request')
    def test_get_runners(self, get_runners_request):
        get_runners_request.return_value = (
            {'values': ['foo', 'bar', 'baz']},
            200
        )
        service = BitbucketRepositoryRunner()
        result = service.get_runners('foo', 'bar')
        self.assertEqual(
            result,
            {'values': ['foo', 'bar', 'baz']}
        )

    @mock.patch.object(BitbucketRepositoryRunner, 'make_http_request')
    def test_create_runner(self, create_runner_request):
        create_runner_request.return_value = (
            'foo',
            200
        )
        service = BitbucketRepositoryRunner()
        result = service.create_runner('foo', 'bar', 'baz', ('label1',))
        self.assertEqual(
            result,
            'foo'
        )

    @mock.patch.object(BitbucketRepositoryRunner, 'make_http_request')
    def test_delete_runner(self, delete_runner_request):
        delete_runner_request.return_value = (
            'foo',
            200
        )
        service = BitbucketRepositoryRunner()
        result = service.delete_runner('foo', 'bar', 'baz')
        self.assertEqual(
            result,
            'foo'
        )
