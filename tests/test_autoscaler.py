import os
import logging
from unittest import TestCase, mock

import pytest

import runner
from automatic import autoscaler
from tests.helpers import capture_output


@mock.patch.dict(os.environ, {'BITBUCKET_USERNAME': 'test', 'BITBUCKET_APP_PASSWORD': 'test', 'DEBUG': 'true'})
class BitbucketRunnerAutoscalerTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self.caplog = caplog

    @mock.patch.object(runner.BitbucketWorkspaceRunner, 'make_http_request')
    def test_get_runners(self, get_runners_request):
        get_runners_request.return_value = ({
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
            ]},
            200
        )
        runner_data = {
            "workspace": {
                "name": "workspace-test",
                "uuid": "workspace-test_uuid"
            },
            "repository": None
        }
        runner_count_scaler = autoscaler.BitbucketRunnerAutoscaler(runner_data=runner_data)
        result = runner_count_scaler.get_runners()
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

    @mock.patch('automatic.autoscaler.BitbucketRunnerAutoscaler.get_runners')
    def test_run_nothing_to_do(self, mock_get_runners):
        get_runners = [
            {
                'created_on': '2021-09-29T23:28:04.683210Z',
                'labels': ['test', 'self.hosted', 'linux'],
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
        mock_get_runners.return_value = get_runners

        runner_data = {
            "name": "Runner repository group",
            "workspace": {
                "name": "workspace-test",
                "uuid": "workspace-test_uuid"
            },
            "repository": {
                "name": "repository-test",
                "uuid": "repository-test_uuid"
            },
            "labels": {"self.hosted", "test", "linux"},
            "namespace": "rg-1",
            "type": "autoscaling",
            "parameters": {
                "min": 1,
                "max": 10,
                "scaleUpThreshold": 0.5,
                "scaleDownThreshold": 0.2,
                "scaleUpMultiplier": 1.5,
                "scaleDownMultiplier": 0.5
            }
        }

        service = autoscaler.BitbucketRunnerAutoscaler(runner_data=runner_data)

        with self.caplog.at_level(logging.INFO):
            service.run()

        self.assertIn('Nothing to do...\n', self.caplog.text)

    @mock.patch('automatic.autoscaler.DEFAULT_SLEEP_TIME_RUNNER_SETUP', 0.1)
    @mock.patch('automatic.autoscaler.BitbucketRunnerAutoscaler.get_runners')
    @mock.patch('runner.create_bitbucket_runner')
    @mock.patch('runner.setup_job')
    def test_create_first_runners(self, mock_setup_job, mock_create_runner, mock_get_runners):
        get_runners = [
            {
                'created_on': '2021-09-29T23:28:04.683210Z',
                'labels': ['test', 'self.hosted', 'linux'],
                'name': 'good',
                'oauth_client': {
                    'audience': 'api.fake-api.com',
                    'id': 'YgTQgBOdLVu0Ag9P4nYtM5miFgXopgVi',
                    'token_endpoint': 'https://fake-api.auth0.com/oauth/token'},
                'state': {
                    'status': 'OFFLINE',
                    'updated_on': '2021-09-29T23:55:14.857790Z',
                    'version': {'current': '1.184'}
                },
                'updated_on': '2021-09-29T23:55:14.857791Z',
                'uuid': '{670ea89c-e64d-5923-8ccc-06d67fae8039}'}
        ]
        mock_get_runners.return_value = get_runners

        runner_data = {
            "name": "Runner repository group",
            "workspace": {
                "name": "workspace-test",
                "uuid": "workspace-test_uuid"
            },
            "repository": {
                "name": "repository-test",
                "uuid": "repository-test_uuid"
            },
            "labels": {"self.hosted", "test", "linux"},
            "namespace": "rg-1",
            "type": "autoscaling",
            "parameters": {
                "min": 1,
                "max": 10,
                "scaleUpThreshold": 0.5,
                "scaleDownThreshold": 0.2,
                "scaleUpMultiplier": 1.5,
                "scaleDownMultiplier": 0.5
            }
        }

        service = autoscaler.BitbucketRunnerAutoscaler(runner_data=runner_data)

        create_runner_data = {
            'accountUuid': 'workspace-test_uuid',
            'repositoryUuid': 'repository-test_uuid',
            'runnerUuid': 'test-runner-uuid',
            'oauthClientId_base64': 'testbase64=',
            'oauthClientSecret_base64': 'testsecret=='
        }

        mock_create_runner.return_value = create_runner_data
        mock_setup_job.return_value = None

        with capture_output() as out:
            with self.caplog.at_level(logging.DEBUG):
                service.run()

        self.assertIn("{'OFFLINE': 1}", self.caplog.text)
        self.assertIn('Successfully setup runner UUID test-runner-uuid on workspace workspace-test\n',
                      out.getvalue())

    @mock.patch('automatic.autoscaler.DEFAULT_SLEEP_TIME_RUNNER_DELETE', 0.1)
    @mock.patch('automatic.autoscaler.BitbucketRunnerAutoscaler.get_runners')
    @mock.patch('runner.delete_bitbucket_runner')
    @mock.patch('runner.delete_job')
    def test_delete_runners_reach_min(self, mock_delete_job, mock_delete_runner, mock_get_runners):
        get_runners = [
            {
                'created_on': '2021-09-29T23:28:04.683210Z',
                'labels': ['test', 'self.hosted', 'linux'],
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
                'uuid': '{670ea89c-e64d-5923-8ccc-06d67fae8039}'
            },
            {
                'created_on': '2021-09-29T23:28:04.683210Z',
                'labels': ['test', 'self.hosted', 'linux'],
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
                'uuid': '{670ea89c-e64d-5923-8ccc-06d67fae8038}'
            }
        ]
        mock_get_runners.return_value = get_runners

        runner_data = {
            "name": "Runner repository group",
            "workspace": {
                "name": "workspace-test",
                "uuid": "workspace-test_uuid"
            },
            "repository": {
                "name": "repository-test",
                "uuid": "repository-test_uuid"
            },
            "labels": {"self.hosted", "test", "linux"},
            "namespace": "rg-1",
            "type": "autoscaling",
            "parameters": {
                "min": 1,
                "max": 10,
                "scaleUpThreshold": 0.5,
                "scaleDownThreshold": 0.2,
                "scaleUpMultiplier": 1.5,
                "scaleDownMultiplier": 0.5
            }
        }

        service = autoscaler.BitbucketRunnerAutoscaler(runner_data=runner_data)

        mock_delete_runner.return_value = None
        mock_delete_job.return_value = None

        with capture_output() as out:
            service.run()

        self.assertIn('Successfully deleted runner UUID 670ea89c-e64d-5923-8ccc-06d67fae8039'
                      ' on workspace workspace-test\n',
                      out.getvalue())

    @mock.patch('automatic.autoscaler.DEFAULT_SLEEP_TIME_RUNNER_DELETE', 0.1)
    @mock.patch('automatic.autoscaler.BitbucketRunnerAutoscaler.get_runners')
    @mock.patch('runner.delete_bitbucket_runner')
    @mock.patch('runner.delete_job')
    def test_delete_runners(self, mock_delete_job, mock_delete_runner, mock_get_runners):
        get_runners = [
            {
                'created_on': '2021-09-29T23:28:04.683210Z',
                'labels': ['test', 'self.hosted', 'linux'],
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
                'uuid': '{670ea89c-e64d-5923-8ccc-06d67fae8039}'
            },
            {
                'created_on': '2021-09-29T23:28:04.683210Z',
                'labels': ['test', 'self.hosted', 'linux'],
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
                'uuid': '{670ea89c-e64d-5923-8ccc-06d67fae8038}'
            },
            {
                'created_on': '2021-09-29T23:28:04.683210Z',
                'labels': ['test', 'self.hosted', 'linux'],
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
                'uuid': '{670ea89c-e64d-5923-8ccc-06d67fae8037}'
            }
        ]
        mock_get_runners.return_value = get_runners

        runner_data = {
            "name": "Runner repository group",
            "workspace": {
                "name": "workspace-test",
                "uuid": "workspace-test_uuid"
            },
            "repository": {
                "name": "repository-test",
                "uuid": "repository-test_uuid"
            },
            "labels": {"self.hosted", "test", "linux"},
            "namespace": "rg-1",
            "type": "autoscaling",
            "parameters": {
                "min": 1,
                "max": 10,
                "scaleUpThreshold": 0.5,
                "scaleDownThreshold": 0.8,
                "scaleUpMultiplier": 1.5,
                "scaleDownMultiplier": 0.8
            }
        }

        service = autoscaler.BitbucketRunnerAutoscaler(runner_data=runner_data)

        mock_delete_runner.return_value = None
        mock_delete_job.return_value = None

        with capture_output() as out:
            service.run()

        self.assertIn('Successfully deleted runner UUID 670ea89c-e64d-5923-8ccc-06d67fae8039'
                      ' on workspace workspace-test\n',
                      out.getvalue())

    @mock.patch('automatic.autoscaler.DEFAULT_SLEEP_TIME_RUNNER_SETUP', 0.1)
    @mock.patch('automatic.autoscaler.BitbucketRunnerAutoscaler.get_runners')
    @mock.patch('runner.create_bitbucket_runner')
    @mock.patch('runner.setup_job')
    def test_create_additional_runners(self, mock_setup_job, mock_create_runner, mock_get_runners):
        get_runners = [
            {
                'created_on': '2021-09-29T23:28:04.683210Z',
                'labels': ['test', 'self.hosted', 'linux'],
                'name': 'good',
                'oauth_client': {
                    'audience': 'api.fake-api.com',
                    'id': 'YgTQgBOdLVu0Ag9P4nYtM5miFgXopgVi',
                    'token_endpoint': 'https://fake-api.auth0.com/oauth/token'},
                'state': {
                    'status': 'ONLINE',
                    'updated_on': '2021-09-29T23:55:14.857790Z',
                    'version': {'current': '1.184'},
                    'step': "busy"
                },
                'updated_on': '2021-09-29T23:55:14.857791Z',
                'uuid': '{670ea89c-e64d-5923-8ccc-06d67fae8039}'}
        ]
        mock_get_runners.return_value = get_runners

        runner_data = {
            "name": "Runner repository group",
            "workspace": {
                "name": "workspace-test",
                "uuid": "workspace-test_uuid"
            },
            "repository": {
                "name": "repository-test",
                "uuid": "repository-test_uuid"
            },
            "labels": {"self.hosted", "test", "linux"},
            "namespace": "rg-1",
            "type": "autoscaling",
            "parameters": {
                "min": 1,
                "max": 10,
                "scaleUpThreshold": 0.5,
                "scaleDownThreshold": 0.2,
                "scaleUpMultiplier": 1.5,
                "scaleDownMultiplier": 0.5
            }
        }

        service = autoscaler.BitbucketRunnerAutoscaler(runner_data=runner_data)

        create_runner_data = {
            'accountUuid': 'workspace-test_uuid',
            'repositoryUuid': 'repository-test_uuid',
            'runnerUuid': 'test-runner-uuid',
            'oauthClientId_base64': 'testbase64=',
            'oauthClientSecret_base64': 'testsecret=='
        }

        mock_create_runner.return_value = create_runner_data
        mock_setup_job.return_value = None

        with capture_output() as out:
            with self.caplog.at_level(logging.DEBUG):
                service.run()

        self.assertIn("{'ONLINE': 1}", self.caplog.text)
        self.assertIn('Successfully setup runner UUID test-runner-uuid on workspace workspace-test\n',
                      out.getvalue())

    @mock.patch('automatic.autoscaler.DEFAULT_SLEEP_TIME_RUNNER_SETUP', 0.1)
    @mock.patch('automatic.autoscaler.BitbucketRunnerAutoscaler.get_runners')
    @mock.patch('runner.create_bitbucket_runner')
    @mock.patch('runner.setup_job')
    def test_create_additional_runners_exceeds_max_config(self, mock_setup_job, mock_create_runner, mock_get_runners):
        get_runners = [
            {
                'created_on': '2021-09-29T23:28:04.683210Z',
                'labels': ['test', 'self.hosted', 'linux'],
                'name': 'good',
                'oauth_client': {
                    'audience': 'api.fake-api.com',
                    'id': 'YgTQgBOdLVu0Ag9P4nYtM5miFgXopgVi',
                    'token_endpoint': 'https://fake-api.auth0.com/oauth/token'},
                'state': {
                    'status': 'ONLINE',
                    'updated_on': '2021-09-29T23:55:14.857790Z',
                    'version': {'current': '1.184'},
                    'step': "busy"
                },
                'updated_on': '2021-09-29T23:55:14.857791Z',
                'uuid': '{670ea89c-e64d-5923-8ccc-06d67fae8039}'}
        ]
        mock_get_runners.return_value = get_runners

        runner_data = {
            "name": "Runner repository group",
            "workspace": {
                "name": "workspace-test",
                "uuid": "workspace-test_uuid"
            },
            "repository": {
                "name": "repository-test",
                "uuid": "repository-test_uuid"
            },
            "labels": {"self.hosted", "test", "linux"},
            "namespace": "rg-1",
            "type": "autoscaling",
            "parameters": {
                "min": 1,
                "max": 1,
                "scaleUpThreshold": 0.5,
                "scaleDownThreshold": 0.2,
                "scaleUpMultiplier": 1.5,
                "scaleDownMultiplier": 0.5
            }
        }

        service = autoscaler.BitbucketRunnerAutoscaler(runner_data=runner_data)

        create_runner_data = {
            'accountUuid': 'workspace-test_uuid',
            'repositoryUuid': 'repository-test_uuid',
            'runnerUuid': 'test-runner-uuid',
            'oauthClientId_base64': 'testbase64=',
            'oauthClientSecret_base64': 'testsecret=='
        }

        mock_create_runner.return_value = create_runner_data
        mock_setup_job.return_value = None

        with self.caplog.at_level(logging.DEBUG):
            service.run()

        self.assertIn("{'ONLINE': 1}", self.caplog.text)
        self.assertIn('Max runners count: 1 reached.', self.caplog.text)

    @mock.patch('automatic.autoscaler.DEFAULT_SLEEP_TIME_RUNNER_SETUP', 0.1)
    @mock.patch('automatic.autoscaler.MAX_RUNNERS_COUNT_PER_REPOSITORY', 1)
    @mock.patch('automatic.autoscaler.BitbucketRunnerAutoscaler.get_runners')
    def test_create_additional_runners_exceeds_max_constant(self, mock_get_runners):
        get_runners = [
            {
                'created_on': '2021-09-29T23:28:04.683210Z',
                'labels': ['test', 'self.hosted', 'linux'],
                'name': 'good',
                'oauth_client': {
                    'audience': 'api.fake-api.com',
                    'id': 'YgTQgBOdLVu0Ag9P4nYtM5miFgXopgVi',
                    'token_endpoint': 'https://fake-api.auth0.com/oauth/token'},
                'state': {
                    'status': 'ONLINE',
                    'updated_on': '2021-09-29T23:55:14.857790Z',
                    'version': {'current': '1.184'},
                    'step': "busy"
                },
                'updated_on': '2021-09-29T23:55:14.857791Z',
                'uuid': '{670ea89c-e64d-5923-8ccc-06d67fae8039}'}
        ]
        mock_get_runners.return_value = get_runners

        runner_data = {
            "name": "Runner repository group",
            "workspace": {
                "name": "workspace-test",
                "uuid": "workspace-test_uuid"
            },
            "repository": {
                "name": "repository-test",
                "uuid": "repository-test_uuid"
            },
            "labels": {"self.hosted", "test", "linux"},
            "namespace": "rg-1",
            "type": "autoscaling",
            "parameters": {
                "min": 1,
                "max": 2,
                "scaleUpThreshold": 0.5,
                "scaleDownThreshold": 0.2,
                "scaleUpMultiplier": 1.5,
                "scaleDownMultiplier": 0.5
            }
        }

        service = autoscaler.BitbucketRunnerAutoscaler(runner_data=runner_data)

        with self.caplog.at_level(logging.WARNING):
            service.create_runner(2)

        self.assertIn('Max Runners count limit reached 1 per workspace workspace-test repository: repository-test', self.caplog.text)
