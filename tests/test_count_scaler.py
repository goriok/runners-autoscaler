import os
import logging
from unittest import TestCase, mock

import pytest

import runner
from manual import count_scaler
from tests.helpers import capture_output


@mock.patch.dict(os.environ, {'BITBUCKET_USERNAME': 'test', 'BITBUCKET_APP_PASSWORD': 'test', 'DEBUG': 'true'})
class BitbucketRunnerCountScalerTestCase(TestCase):

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
        runner_count_scaler = count_scaler.BitbucketRunnerCountScaler(runner_data=runner_data)
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

    @mock.patch('manual.count_scaler.BitbucketRunnerCountScaler.get_runners')
    def test_run_nothing_to_do(self, mock_get_runners):
        get_runners = [
            {
                'created_on': '2021-09-29T23:28:04.683210Z',
                'labels': ['test-label', 'self.hosted', 'linux'],
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
            'name': 'Runner repository group',
            "workspace": {
                "name": "workspace-test",
                "uuid": "workspace-test_uuid"
            },
            "repository": {
                "name": "repository-test",
                "uuid": "repository-test_uuid"
            },
            'labels': {'self.hosted', 'linux', 'test-label'},
            'namespace': 'bitbucket-runner',
            'strategy': 'manual',
            'parameters': {'runners_count': 1}
        }

        service = count_scaler.BitbucketRunnerCountScaler(runner_data=runner_data)

        with self.caplog.at_level(logging.INFO):
            service.run()

        self.assertIn('Nothing to do...\n', self.caplog.text)

    @mock.patch('manual.count_scaler.DEFAULT_SLEEP_TIME_RUNNER_SETUP', 0.1)
    @mock.patch('manual.count_scaler.BitbucketRunnerCountScaler.get_runners')
    @mock.patch('runner.create_bitbucket_runner')
    @mock.patch('runner.setup_job')
    def test_create_new_runners(self, mock_setup_job, mock_create_runner, mock_get_runners):
        get_runners = []
        mock_get_runners.return_value = get_runners

        runner_data = {
            'name': 'Runner repository group',
            "workspace": {
                "name": "workspace-test",
                "uuid": "workspace-test_uuid"
            },
            "repository": {
                "name": "repository-test",
                "uuid": "repository-test_uuid"
            },
            'labels': {'self.hosted', 'linux', 'test-label'},
            'namespace': 'bitbucket-runner',
            'strategy': 'manual',
            'parameters': {'runners_count': 1}
        }

        service = count_scaler.BitbucketRunnerCountScaler(runner_data=runner_data)

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
            service.run()

        self.assertIn('Successfully setup runner UUID test-runner-uuid on workspace workspace-test\n',
                      out.getvalue())

    @mock.patch('manual.count_scaler.DEFAULT_SLEEP_TIME_RUNNER_DELETE', 0.1)
    @mock.patch('manual.count_scaler.BitbucketRunnerCountScaler.get_runners')
    @mock.patch('runner.delete_bitbucket_runner')
    @mock.patch('runner.delete_job')
    def test_delete_runners(self, mock_delete_job, mock_delete_runner, mock_get_runners):
        get_runners = [
            {
                'created_on': '2021-09-29T23:28:04.683210Z',
                'labels': ['test-label', 'self.hosted', 'linux'],
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
            'name': 'Runner repository group',
            "workspace": {
                "name": "workspace-test",
                "uuid": "workspace-test_uuid"
            },
            "repository": {
                "name": "repository-test",
                "uuid": "repository-test_uuid"
            },
            'labels': {'self.hosted', 'linux', 'test-label'},
            'namespace': 'bitbucket-runner',
            'strategy': 'manual',
            'parameters': {'runners_count': 0}
        }

        service = count_scaler.BitbucketRunnerCountScaler(runner_data=runner_data)

        mock_delete_runner.return_value = None
        mock_delete_job.return_value = None

        with capture_output() as out:
            service.run()

        self.assertIn('Successfully deleted runner UUID 670ea89c-e64d-5923-8ccc-06d67fae8039'
                      ' on workspace workspace-test\n',
                      out.getvalue())

    @mock.patch('manual.count_scaler.DEFAULT_SLEEP_TIME_RUNNER_DELETE', 0.1)
    @mock.patch('manual.count_scaler.BitbucketRunnerCountScaler.get_runners')
    def test_delete_no_idle_runners(self, mock_get_runners):
        get_runners = [
            {
                'created_on': '2021-09-29T23:28:04.683210Z',
                'labels': ['test-label', 'self.hosted', 'linux'],
                'name': 'good',
                'oauth_client': {
                    'audience': 'api.fake-api.com',
                    'id': 'YgTQgBOdLVu0Ag9P4nYtM5miFgXopgVi',
                    'token_endpoint': 'https://fake-api.auth0.com/oauth/token'},
                'state': {
                    'status': 'ONLINE',
                    'updated_on': '2021-09-29T23:55:14.857790Z',
                    'version': {'current': '1.184'},
                    'step': 'test job running'
                },
                'updated_on': '2021-09-29T23:55:14.857791Z',
                'uuid': '{670ea89c-e64d-5923-8ccc-06d67fae8039}'}
        ]
        mock_get_runners.return_value = get_runners

        runner_data = {
            'name': 'Runner repository group',
            "workspace": {
                "name": "workspace-test",
                "uuid": "workspace-test_uuid"
            },
            "repository": {
                "name": "repository-test",
                "uuid": "repository-test_uuid"
            },
            'labels': {'self.hosted', 'linux', 'test-label'},
            'namespace': 'bitbucket-runner',
            'strategy': 'manual',
            'parameters': {'runners_count': 0}
        }

        service = count_scaler.BitbucketRunnerCountScaler(runner_data=runner_data)

        with self.caplog.at_level(logging.WARNING):
            service.run()

        self.assertIn('Nothing to delete... All runners are BUSY (running jobs).',
                      self.caplog.text)
