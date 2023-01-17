import os
from unittest import TestCase, mock

import pytest

from autoscaler.core.validators import NameUUIDData
from autoscaler.services.bitbucket import BitbucketService, BitbucketServiceData


@mock.patch.dict(os.environ, {'BITBUCKET_USERNAME': 'test', 'BITBUCKET_APP_PASSWORD': 'test', 'DEBUG': 'true'})
class BitbucketServiceTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self.caplog = caplog

    @mock.patch('autoscaler.clients.bitbucket.base.BitbucketRepositoryRunner.get_runners')
    def test_get_bitbucket_runners(self, get_runners_request):
        get_runners_request.return_value = [
            {
                'created_on': '2021-09-29T23:28:04.683210Z',
                'labels': ['abc', 'fff', 'self.hosted', 'linux'],
                'name': 'good',
                'oauth_client': {
                    'audience': 'api.fake-api.com',
                    'id': 'YgTQgBOdLVu0Ag9P4nYtM5miFgXopgVi',
                    'token_endpoint': 'https://fake-api.auth0.com/oauth/token'},
                'state': {
                    'status': 'ONLINE',
                    'updated_on': '2021-09-29T23:55:14.857790Z',
                    'version': {'current': '1.184'}
                },
                'updated_on': '2021-09-29T23:55:14.857791Z',
                'uuid': '{670ea89c-e64d-5923-8ccc-06d67fae8039}'}
        ]

        workspace = NameUUIDData(
            name='workspace-test',
            uuid='{workspace-test-uuid}'
        )

        repository = NameUUIDData(
            name='repository-test',
            uuid='{repository-test-uuid}'
        )

        service: BitbucketService = BitbucketService('test')

        result = service.get_bitbucket_runners(workspace, repository)

        self.assertEqual(
            result,
            [
                {
                    'created_on': '2021-09-29T23:28:04.683210Z',
                    'labels': ['abc', 'fff', 'self.hosted', 'linux'],
                    'name': 'good',
                    'oauth_client': {
                        'audience': 'api.fake-api.com',
                        'id': 'YgTQgBOdLVu0Ag9P4nYtM5miFgXopgVi',
                        'token_endpoint': 'https://fake-api.auth0.com/oauth/token'},
                    'state': {
                        'status': 'ONLINE',
                        'updated_on': '2021-09-29T23:55:14.857790Z',
                        'version': {'current': '1.184'}
                    },
                    'updated_on': '2021-09-29T23:55:14.857791Z',
                    'uuid': '{670ea89c-e64d-5923-8ccc-06d67fae8039}'}
            ]
        )

    @mock.patch('autoscaler.clients.bitbucket.base.BitbucketWorkspaceRunner.get_runners')
    def test_get_bitbucket_runners_no_repo(self, get_runners_request):
        get_runners_request.return_value = [
            {
                'created_on': '2021-09-29T23:28:04.683210Z',
                'labels': ['abc', 'fff', 'self.hosted', 'linux'],
                'name': 'good',
                'oauth_client': {
                    'audience': 'api.fake-api.com',
                    'id': 'YgTQgBOdLVu0Ag9P4nYtM5miFgXopgVi',
                    'token_endpoint': 'https://fake-api.auth0.com/oauth/token'},
                'state': {
                    'status': 'ONLINE',
                    'updated_on': '2021-09-29T23:55:14.857790Z',
                    'version': {'current': '1.184'}
                },
                'updated_on': '2021-09-29T23:55:14.857791Z',
                'uuid': '{670ea89c-e64d-5923-8ccc-06d67fae8039}'}
        ]

        workspace = NameUUIDData(
            name='workspace-test',
            uuid='{workspace-test-uuid}'
        )

        repository = None

        service: BitbucketService = BitbucketService('test')

        result = service.get_bitbucket_runners(workspace, repository)

        self.assertEqual(
            result,
            [
                {
                    'created_on': '2021-09-29T23:28:04.683210Z',
                    'labels': ['abc', 'fff', 'self.hosted', 'linux'],
                    'name': 'good',
                    'oauth_client': {
                        'audience': 'api.fake-api.com',
                        'id': 'YgTQgBOdLVu0Ag9P4nYtM5miFgXopgVi',
                        'token_endpoint': 'https://fake-api.auth0.com/oauth/token'},
                    'state': {
                        'status': 'ONLINE',
                        'updated_on': '2021-09-29T23:55:14.857790Z',
                        'version': {'current': '1.184'}
                    },
                    'updated_on': '2021-09-29T23:55:14.857791Z',
                    'uuid': '{670ea89c-e64d-5923-8ccc-06d67fae8039}'}
            ]
        )

    @mock.patch('autoscaler.clients.bitbucket.base.BitbucketRepositoryRunner.create_runner')
    def test_create_bitbucket_runner(self, mock_create_runner):
        mock_create_runner.return_value = {
            'uuid': '{test-uuid}',
            'name': 'good',
            'labels': ['self.hosted', 'asd', 'linux'],
            'state': {
                'status': 'UNREGISTERED',
                'version': {'version': '1.252'},
                'updated_on': '2021-12-03T18:20:22.561088Z'
            },
            'created_on': '2021-12-03T18:20:22.561005Z',
            'updated_on': '2021-12-03T18:20:22.561005Z',
            'oauth_client': {
                'id': 'testid',
                'secret': 'testsecret',
                'token_endpoint': 'https://fake-api.auth0.com/oauth/token',
                'audience': 'api.fake-api.com'
            }
        }

        workspace = NameUUIDData(
            name='workspace-test',
            uuid='{workspace-test-uuid}'
        )

        repository = NameUUIDData(
            name='repository-test',
            uuid='{repository-test-uuid}'
        )

        service: BitbucketService = BitbucketService('test')

        result = service.create_bitbucket_runner(
            workspace=workspace,
            name='test',
            labels=['self.hosted', 'asd', 'linux'],
            repository=repository
        )

        self.assertEqual(
            result,
            BitbucketServiceData(
                account_uuid='{workspace-test-uuid}',
                repository_uuid='{repository-test-uuid}',
                runner_uuid='{test-uuid}',
                oauth_client_id_base64='dGVzdGlk',
                oauth_client_secret_base64='dGVzdHNlY3JldA==',
            )
        )

    @mock.patch('autoscaler.clients.bitbucket.base.BitbucketWorkspaceRunner.create_runner')
    def test_create_bitbucket_runner_no_repo(self, mock_create_runner):
        mock_create_runner.return_value = {
            'uuid': '{test-uuid}',
            'name': 'good',
            'labels': ['self.hosted', 'asd', 'linux'],
            'state': {
                'status': 'UNREGISTERED',
                'version': {'version': '1.252'},
                'updated_on': '2021-12-03T18:20:22.561088Z'
            },
            'created_on': '2021-12-03T18:20:22.561005Z',
            'updated_on': '2021-12-03T18:20:22.561005Z',
            'oauth_client': {
                'id': 'testid',
                'secret': 'testsecret',
                'token_endpoint': 'https://fake-api.auth0.com/oauth/token',
                'audience': 'api.fake-api.com'
            }
        }

        workspace = NameUUIDData(
            name='workspace-test',
            uuid='{workspace-test-uuid}'
        )

        repository = None

        service: BitbucketService = BitbucketService('test')

        result = service.create_bitbucket_runner(
            workspace=workspace,
            name='test',
            labels=['self.hosted', 'asd', 'linux'],
            repository=repository
        )

        self.assertEqual(
            result,
            BitbucketServiceData(
                account_uuid='{workspace-test-uuid}',
                repository_uuid=None,
                runner_uuid='{test-uuid}',
                oauth_client_id_base64='dGVzdGlk',
                oauth_client_secret_base64='dGVzdHNlY3JldA==',
            )
        )

    @mock.patch('autoscaler.clients.bitbucket.base.BitbucketRepositoryRunner.delete_runner')
    def test_delete_bitbucket_runner(self, mock_delete_runner):
        mock_delete_runner.return_value = None

        workspace = NameUUIDData(
            name='workspace-test',
            uuid='{workspace-test-uuid}'
        )

        repository = NameUUIDData(
            name='repository-test',
            uuid='{repository-test-uuid}'
        )

        runner_uuid = 'test-uuid'

        service: BitbucketService = BitbucketService('test')
        service.delete_bitbucket_runner(
            workspace,
            runner_uuid,
            repository=repository
        )

        mock_delete_runner.assert_called_once_with(
            workspace.uuid,
            repository.uuid,
            runner_uuid
        )

    @mock.patch('autoscaler.clients.bitbucket.base.BitbucketWorkspaceRunner.delete_runner')
    def test_delete_bitbucket_runner_no_repo(self, mock_delete_runner):
        mock_delete_runner.return_value = None

        workspace = NameUUIDData(
            name='workspace-test',
            uuid='{workspace-test-uuid}'
        )

        runner_uuid = 'test-uuid'

        service: BitbucketService = BitbucketService('test')
        service.delete_bitbucket_runner(workspace, runner_uuid)

        mock_delete_runner.assert_called_once_with(workspace.uuid, 'test-uuid')

    @mock.patch('autoscaler.clients.bitbucket.base.BitbucketWorkspace.get_workspace')
    @mock.patch('autoscaler.clients.bitbucket.base.BitbucketRepository.get_repository')
    def test_get_bitbucket_workspace_repository_uuids(self, mock_get_repo, mock_get_workspace):
        mock_get_repo.return_value = {'uuid': '{test-repo-uuid}', 'slug': 'test-repo'}
        mock_get_workspace.return_value = {'uuid': '{test-workspace-uuid}', 'slug': 'test-workspace'}

        service: BitbucketService = BitbucketService('test')
        result = service.get_bitbucket_workspace_repository_uuids(workspace_name='test-workspace', repository_name='test-repo')

        self.assertEqual(
            result,
            ({'uuid': '{test-workspace-uuid}', 'name': 'test-workspace'}, {'uuid': '{test-repo-uuid}', 'name': 'test-repo'})
        )
