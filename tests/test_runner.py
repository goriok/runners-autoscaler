import os
import logging
from unittest import TestCase, mock

import yaml
import pytest


import runner
from tests.helpers import capture_output


@mock.patch.dict(os.environ, {'BITBUCKET_USERNAME': 'test', 'BITBUCKET_APP_PASSWORD': 'test', 'DEBUG': 'true'})
class RunnerTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self.caplog = caplog

    @mock.patch('apis.bitbucket.base.BitbucketRepositoryRunner.get_runners')
    def test_get_bitbucket_runners(self, get_runners_request):
        get_runners_request.return_value = {
            'values': [
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
        }

        runner_data = {
            "workspace": {
                "name": "workspace-test",
                "uuid": "workspace-test_uuid"
            },
            "repository": {
                "name": "repository-test",
                "uuid": "repository-test_uuid"
            }
        }

        result = runner.get_bitbucket_runners(**runner_data)
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

    @mock.patch('apis.bitbucket.base.BitbucketWorkspaceRunner.get_runners')
    def test_get_bitbucket_runners_no_repo(self, get_runners_request):
        get_runners_request.return_value = {
            'values': [
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
        }

        runner_data = {
            "workspace": {
                "name": "workspace-test",
                "uuid": "workspace-test_uuid"
            }
        }

        result = runner.get_bitbucket_runners(**runner_data)
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

    @mock.patch('apis.bitbucket.base.BitbucketRepositoryRunner.create_runner')
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

        runner_data = {
            "workspace": {
                "name": "workspace-test",
                "uuid": "workspace-test_uuid"
            },
            "repository": {
                "name": "repository-test",
                "uuid": "repository-test_uuid"
            },
            'name': 'good',
            'labels': ('asd',)
        }

        result = runner.create_bitbucket_runner(**runner_data)

        self.assertEqual(
            result,
            {
                'accountUuid': 'workspace-test_uuid',
                'repositoryUuid': 'repository-test_uuid',
                'runnerUuid': 'test-uuid',
                'oauthClientId_base64': 'dGVzdGlk',
                'oauthClientSecret_base64': 'dGVzdHNlY3JldA==',
            }
        )

    @mock.patch('apis.bitbucket.base.BitbucketWorkspaceRunner.create_runner')
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

        runner_data = {
            "workspace": {
                "name": "workspace-test",
                "uuid": "workspace-test_uuid"
            },
            'name': 'good',
            'labels': ('asd',)
        }

        result = runner.create_bitbucket_runner(**runner_data)

        self.assertEqual(
            result,
            {
                'accountUuid': 'workspace-test_uuid',
                'repositoryUuid': None,
                'runnerUuid': 'test-uuid',
                'oauthClientId_base64': 'dGVzdGlk',
                'oauthClientSecret_base64': 'dGVzdHNlY3JldA==',
            }
        )

    @mock.patch('apis.bitbucket.base.BitbucketRepositoryRunner.delete_runner')
    def test_delete_bitbucket_runner(self, mock_delete_runner):
        mock_delete_runner.return_value = None

        runner_data = {
            "workspace": {
                "name": "workspace-test",
                "uuid": "workspace-test_uuid"
            },
            "repository": {
                "name": "repository-test",
                "uuid": "repository-test_uuid"
            },
            'runner_uuid': 'test-uuid'
        }

        runner.delete_bitbucket_runner(**runner_data)

        mock_delete_runner.assert_called_once_with(
            runner_data['workspace']['uuid'],
            runner_data['repository']['uuid'],
            'test-uuid'
        )

    @mock.patch('apis.bitbucket.base.BitbucketWorkspaceRunner.delete_runner')
    def test_delete_bitbucket_runner_no_repo(self, mock_delete_runner):
        mock_delete_runner.return_value = None

        runner_data = {
            "workspace": {
                "name": "workspace-test",
                "uuid": "workspace-test_uuid"
            },
            'runner_uuid': 'test-uuid'
        }

        runner.delete_bitbucket_runner(**runner_data)

        mock_delete_runner.assert_called_once_with(runner_data['workspace']['uuid'], 'test-uuid')

    @mock.patch('apis.kubernetes.base.KubernetesBaseAPIService.get_or_create_kubernetes_namespace')
    def test_check_kubernetes_namespace(self, mock_check_namespace):
        mock_check_namespace.return_value = None

        runner_data = {'namespace': 'test'}

        runner.check_kubernetes_namespace(**runner_data)

        mock_check_namespace.assert_called_once_with(**runner_data)

    @mock.patch('apis.kubernetes.base.KubernetesSpecFileAPIService.create_kube_spec_file')
    @mock.patch('apis.kubernetes.base.KubernetesSpecFileAPIService.apply_kubernetes_spec_file')
    def test_setup_job(self, mock_apply, mock_create):
        mock_create.return_value = 'test-k8-dir/test-runner.yaml'
        apply_result = (
            'secret/runner-oauth-credentials configured\njob.batch/runner-test-uuid created\n',
            0)
        mock_apply.return_value = apply_result

        runner_data = {
            'runnerNamespace': 'test-namespace',
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

        with self.caplog.at_level(logging.INFO):
            runner.setup_job(runner_data)

        self.assertIn(str(apply_result), self.caplog.text)

    @mock.patch('apis.kubernetes.base.KubernetesBaseAPIService.delete_job')
    @mock.patch('apis.kubernetes.base.KubernetesSpecFileAPIService.delete_kube_spec_file')
    def test_delete_job(self, mock_delete_file, mock_delete_job):
        mock_delete_job.return_value = None

        mock_delete_file.return_value = None

        runner_data = {'namespace': 'test-namespace', 'runner_uuid': 'test-uuid'}

        runner.delete_job(**runner_data)

        mock_delete_job.assert_called_once_with('test-uuid', namespace='test-namespace')
        mock_delete_file.assert_called_once_with('test-uuid')

    @mock.patch('yaml.safe_load')
    def test_read_from_config(self, mock_config):
        mock_config.side_effect = yaml.YAMLError

        with capture_output() as out:
            with pytest.raises(SystemExit) as pytest_wrapped_e:
                runner.read_from_config('tests/test_config_manual.yaml')

        self.assertTrue(mock_config.called)
        self.assertEqual(pytest_wrapped_e.type, SystemExit)
        self.assertIn('Error in configuration file: tests/test_config_manual.yaml', out.getvalue())

    @mock.patch('apis.bitbucket.base.BitbucketWorkspace.get_workspace')
    @mock.patch('apis.bitbucket.base.BitbucketRepository.get_repository')
    def test_get_bitbucket_workspace_repository_uuids(self, mock_get_repo, mock_get_workspace):
        mock_get_repo.return_value = {'uuid': '{test-repo-uuid}', 'slug': 'test-repo'}
        mock_get_workspace.return_value = {'uuid': '{test-workspace-uuid}', 'slug': 'test-workspace'}

        runner_data = {'workspace_name': 'test-workspace', 'repository_name': 'test-repo'}
        result = runner.get_bitbucket_workspace_repository_uuids(**runner_data)
        self.assertEqual(
            result,
            ({'uuid': 'test-workspace-uuid', 'name': 'test-workspace'}, {'uuid': 'test-repo-uuid', 'name': 'test-repo'})
        )
