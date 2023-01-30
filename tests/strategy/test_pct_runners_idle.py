import logging
import os
from unittest import TestCase, mock

import pytest

from autoscaler.core.validators import Constants, NameUUIDData, PctRunnersIdleParameters, PctRunnersIdleStrategyData
from autoscaler.services.kubernetes import KubernetesInMemoryService
from autoscaler.services.bitbucket import BitbucketServiceData
from autoscaler.strategy.pct_runners_idle import PctRunnersIdleScaler, PctRunnersIdleData
from tests.helpers import capture_output


@mock.patch.dict(os.environ, {'BITBUCKET_USERNAME': 'test', 'BITBUCKET_APP_PASSWORD': 'test', 'DEBUG': 'true'})
class BitbucketRunnerAutoscalerTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self.caplog = caplog

    @mock.patch('autoscaler.services.bitbucket.BitbucketService.get_bitbucket_runners')
    def test_get_runners(self, get_runners_request):
        get_runners_request.return_value = ([{
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
                'uuid': '{670ea89c-e64d-5923-8ccc-06d67fae8039}'
            }]
        )
        runner_data = PctRunnersIdleData(
            workspace=NameUUIDData(
                name='workspace-test',
                uuid='{workspace-test-uuid}'
            ),
            repository=NameUUIDData(
                name='repository-test',
                uuid='{repository-test-uuid}'
            ),
            name='good',
            namespace='test',
            strategy='custom',
            labels={'asd'},
            strategy_data=PctRunnersIdleStrategyData(
                parameters=PctRunnersIdleParameters(
                    min=1,
                    max=10,
                    scale_up_threshold=0.5,
                    scale_down_threshold=0.2,
                    scale_up_multiplier=1.5,
                    scale_down_multiplier=0.5
                )
            )
        )

        runner_count_scaler = PctRunnersIdleScaler(
            runner_data=runner_data,
            runner_constants=Constants(),
            kubernetes_service=KubernetesInMemoryService()
        )

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

    @mock.patch('autoscaler.strategy.pct_runners_idle.PctRunnersIdleScaler.get_runners')
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

        runner_data = PctRunnersIdleData(
            workspace=NameUUIDData(
                name='workspace-test',
                uuid='{workspace-test-uuid}'
            ),
            repository=NameUUIDData(
                name='repository-test',
                uuid='{repository-test-uuid}'
            ),
            name='good',
            namespace='test',
            labels={'self.hosted', 'test', 'linux'},
            strategy='percentageRunnersIdle',
            strategy_data=PctRunnersIdleStrategyData(
                parameters=PctRunnersIdleParameters(
                    min=1,
                    max=10,
                    scale_up_threshold=0.5,
                    scale_down_threshold=0.2,
                    scale_up_multiplier=1.5,
                    scale_down_multiplier=0.5
                )
            )
        )

        service = PctRunnersIdleScaler(
            runner_data=runner_data,
            runner_constants=Constants(),
            kubernetes_service=KubernetesInMemoryService()
        )

        with self.caplog.at_level(logging.INFO):
            service.run()

        self.assertIn('Nothing to do...\n', self.caplog.text)

    @mock.patch('autoscaler.strategy.pct_runners_idle.PctRunnersIdleScaler.get_runners')
    @mock.patch('autoscaler.services.bitbucket.BitbucketService.create_bitbucket_runner')
    def test_create_first_runners(self, mock_create_runner, mock_get_runners):
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

        runner_data = PctRunnersIdleData(
            workspace=NameUUIDData(
                name='workspace-test',
                uuid='{workspace-test-uuid}'
            ),
            repository=NameUUIDData(
                name='repository-test',
                uuid='{repository-test-uuid}'
            ),
            name='good',
            namespace='test',
            labels={'self.hosted', 'test', 'linux'},
            strategy='percentageRunnersIdle',
            strategy_data=PctRunnersIdleStrategyData(
                parameters=PctRunnersIdleParameters(
                    min=1,
                    max=10,
                    scale_up_threshold=0.5,
                    scale_down_threshold=0.2,
                    scale_up_multiplier=1.5,
                    scale_down_multiplier=0.5
                )
            )
        )

        service = PctRunnersIdleScaler(
            runner_data=runner_data,
            runner_constants=Constants(default_sleep_time_runner_setup=1),
            kubernetes_service=KubernetesInMemoryService()
        )

        create_runner_data = BitbucketServiceData(
            account_uuid='{workspace-test-uuid}',
            repository_uuid='{repository-test-uuid}',
            runner_uuid='test-runner-uuid',
            oauth_client_id_base64='testbase64=',
            oauth_client_secret_base64='testsecret=='
        )

        mock_create_runner.return_value = create_runner_data

        with capture_output() as out:
            with self.caplog.at_level(logging.DEBUG):
                service.run()

        self.assertIn("{'OFFLINE': 1}", self.caplog.text)
        self.assertIn('Successfully setup runner UUID test-runner-uuid on workspace workspace-test\n',
                      out.getvalue())

    @mock.patch('autoscaler.strategy.pct_runners_idle.PctRunnersIdleScaler.get_runners')
    @mock.patch('autoscaler.services.bitbucket.BitbucketService.delete_bitbucket_runner')
    def test_delete_runners_reach_min(self, mock_delete_runner, mock_get_runners):
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

        runner_data = PctRunnersIdleData(
            workspace=NameUUIDData(
                name='workspace-test',
                uuid='{workspace-test-uuid}'
            ),
            repository=NameUUIDData(
                name='repository-test',
                uuid='{repository-test-uuid}'
            ),
            name='good',
            namespace='test',
            labels={'self.hosted', 'test', 'linux'},
            strategy='percentageRunnersIdle',
            strategy_data=PctRunnersIdleStrategyData(
                parameters=PctRunnersIdleParameters(
                    min=1,
                    max=10,
                    scale_up_threshold=0.5,
                    scale_down_threshold=0.2,
                    scale_up_multiplier=1.5,
                    scale_down_multiplier=0.5
                )
            )
        )

        service = PctRunnersIdleScaler(
            runner_data=runner_data,
            runner_constants=Constants(default_sleep_time_runner_delete=1),
            kubernetes_service=KubernetesInMemoryService()
        )

        mock_delete_runner.return_value = None

        with capture_output() as out:
            service.run()

        self.assertIn('Successfully deleted runner UUID {670ea89c-e64d-5923-8ccc-06d67fae8039}'
                      ' on workspace workspace-test\n',
                      out.getvalue())

    @mock.patch('autoscaler.strategy.pct_runners_idle.PctRunnersIdleScaler.get_runners')
    @mock.patch('autoscaler.services.bitbucket.BitbucketService.delete_bitbucket_runner')
    def test_delete_runners(self, mock_delete_runner, mock_get_runners):
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

        runner_data = PctRunnersIdleData(
            workspace=NameUUIDData(
                name='workspace-test',
                uuid='{workspace-test-uuid}'
            ),
            repository=NameUUIDData(
                name='repository-test',
                uuid='{repository-test-uuid}'
            ),
            name='good',
            namespace='test',
            labels={'self.hosted', 'test', 'linux'},
            strategy='percentageRunnersIdle',
            strategy_data=PctRunnersIdleStrategyData(
                parameters=PctRunnersIdleParameters(
                    min=1,
                    max=10,
                    scale_up_threshold=0.5,
                    scale_down_threshold=0.2,
                    scale_up_multiplier=1.5,
                    scale_down_multiplier=0.5
                )
            )
        )

        service = PctRunnersIdleScaler(
            runner_data=runner_data,
            runner_constants=Constants(default_sleep_time_runner_delete=1),
            kubernetes_service=KubernetesInMemoryService()
        )

        mock_delete_runner.return_value = None

        with capture_output() as out:
            service.run()

        self.assertIn('Successfully deleted runner UUID {670ea89c-e64d-5923-8ccc-06d67fae8039}'
                      ' on workspace workspace-test\n',
                      out.getvalue())

    @mock.patch('autoscaler.strategy.pct_runners_idle.PctRunnersIdleScaler.get_runners')
    @mock.patch('autoscaler.services.bitbucket.BitbucketService.create_bitbucket_runner')
    def test_create_additional_runners(self, mock_create_runner, mock_get_runners):
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
                    'step': 'busy'
                },
                'updated_on': '2021-09-29T23:55:14.857791Z',
                'uuid': '{670ea89c-e64d-5923-8ccc-06d67fae8039}'}
        ]
        mock_get_runners.return_value = get_runners

        runner_data = PctRunnersIdleData(
            workspace=NameUUIDData(
                name='workspace-test',
                uuid='{workspace-test-uuid}'
            ),
            repository=NameUUIDData(
                name='repository-test',
                uuid='{repository-test-uuid}'
            ),
            name='good',
            namespace='test',
            labels={'self.hosted', 'test', 'linux'},
            strategy='percentageRunnersIdle',
            strategy_data=PctRunnersIdleStrategyData(
                parameters=PctRunnersIdleParameters(
                    min=1,
                    max=10,
                    scale_up_threshold=0.5,
                    scale_down_threshold=0.2,
                    scale_up_multiplier=1.5,
                    scale_down_multiplier=0.5
                )
            )
        )

        kubernetes_service = KubernetesInMemoryService()
        service = PctRunnersIdleScaler(
            runner_data=runner_data,
            runner_constants=Constants(default_sleep_time_runner_setup=1),
            kubernetes_service=kubernetes_service
        )

        create_runner_data = BitbucketServiceData(
            account_uuid='{workspace-test-uuid}',
            repository_uuid='{repository-test-uuid}',
            runner_uuid='test-runner-uuid',
            oauth_client_id_base64='testbase64=',
            oauth_client_secret_base64='testsecret=='
        )

        mock_create_runner.return_value = create_runner_data

        with capture_output() as out:
            with self.caplog.at_level(logging.DEBUG):
                service.run()

        self.assertEqual(len(kubernetes_service.list_jobs()), 1)
        self.assertIsNotNone(kubernetes_service.list_jobs()['test-runner-uuid'])
        self.assertIn("{'ONLINE': 1}", self.caplog.text)
        self.assertIn('Successfully setup runner UUID test-runner-uuid on workspace workspace-test\n',
                      out.getvalue())

    @mock.patch('autoscaler.strategy.pct_runners_idle.PctRunnersIdleScaler.get_runners')
    @mock.patch('autoscaler.services.bitbucket.BitbucketService.create_bitbucket_runner')
    def test_create_additional_runners_exceeds_max_config(self, mock_create_runner, mock_get_runners):
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
                    'step': 'busy'
                },
                'updated_on': '2021-09-29T23:55:14.857791Z',
                'uuid': '{670ea89c-e64d-5923-8ccc-06d67fae8039}'}
        ]
        mock_get_runners.return_value = get_runners

        runner_data = PctRunnersIdleData(
            workspace=NameUUIDData(
                name='workspace-test',
                uuid='{workspace-test-uuid}'
            ),
            repository=NameUUIDData(
                name='repository-test',
                uuid='{repository-test-uuid}'
            ),
            name='good',
            namespace='test',
            labels={'self.hosted', 'test', 'linux'},
            strategy='percentageRunnersIdle',
            strategy_data=PctRunnersIdleStrategyData(
                parameters=PctRunnersIdleParameters(
                    min=1,
                    max=1,
                    scale_up_threshold=0.5,
                    scale_down_threshold=0.2,
                    scale_up_multiplier=1.5,
                    scale_down_multiplier=0.5
                )
            )
        )

        service = PctRunnersIdleScaler(
            runner_data=runner_data,
            runner_constants=Constants(default_sleep_time_runner_setup=1),
            kubernetes_service=KubernetesInMemoryService()
        )

        create_runner_data = {
            'account_uuid': '{workspace-test-uuid}',
            'repository_uuid': '{repository-test-uuid}',
            'runner_uuid': 'test-runner-uuid',
            'oauth_client_id_base64': 'testbase64=',
            'oauth_client_secret_base64': 'testsecret=='
        }

        mock_create_runner.return_value = create_runner_data

        with self.caplog.at_level(logging.DEBUG):
            service.run()

        self.assertIn("{'ONLINE': 1}", self.caplog.text)
        self.assertIn('Max runners count: 1 reached.', self.caplog.text)

    @mock.patch('autoscaler.strategy.pct_runners_idle.MAX_RUNNERS_COUNT', 1)
    @mock.patch('autoscaler.strategy.pct_runners_idle.PctRunnersIdleScaler.get_runners')
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
                    'step': 'busy'
                },
                'updated_on': '2021-09-29T23:55:14.857791Z',
                'uuid': '{670ea89c-e64d-5923-8ccc-06d67fae8039}'}
        ]
        mock_get_runners.return_value = get_runners

        runner_data = PctRunnersIdleData(
            workspace=NameUUIDData(
                name='workspace-test',
                uuid='{workspace-test-uuid}'
            ),
            repository=NameUUIDData(
                name='repository-test',
                uuid='{repository-test-uuid}'
            ),
            name='good',
            namespace='test',
            labels={'self.hosted', 'test', 'linux'},
            strategy='percentageRunnersIdle',
            strategy_data=PctRunnersIdleStrategyData(
                parameters=PctRunnersIdleParameters(
                    min=1,
                    max=2,
                    scale_up_threshold=0.5,
                    scale_down_threshold=0.2,
                    scale_up_multiplier=1.5,
                    scale_down_multiplier=0.5
                )
            )
        )

        service = PctRunnersIdleScaler(
            runner_data=runner_data,
            runner_constants=Constants(default_sleep_time_runner_setup=1),
            kubernetes_service=KubernetesInMemoryService()
        )

        with self.caplog.at_level(logging.WARNING):
            service.create_runner(2)

        self.assertIn('Max Runners count limit reached 1 per workspace workspace-test repository: repository-test', self.caplog.text)
