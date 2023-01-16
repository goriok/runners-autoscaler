import logging
import os
from unittest import TestCase, mock

import pytest

from autoscaler.cleaner.pct_runner_idle_cleaner import Cleaner
from autoscaler.core.constants import DEFAULT_RUNNER_KUBERNETES_NAMESPACE
from autoscaler.core.validators import Constants, GroupMeta, NameUUIDData
from autoscaler.services.kubernetes import KubernetesInMemoryService
from autoscaler.start_cleaner import StartCleaner
from tests.helpers import capture_output


@mock.patch.dict(os.environ, {'BITBUCKET_USERNAME': 'test', 'BITBUCKET_APP_PASSWORD': 'test'})
class StartCleanerTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self.caplog = caplog

    def test_config_not_found(self):

        cleaner = StartCleaner(
            config_file_path='fail_config_path',
            poll=False
        )

        with capture_output() as out:
            with pytest.raises(SystemExit) as pytest_wrapped_e:
                cleaner.run()

        self.assertEqual(pytest_wrapped_e.type, SystemExit)
        self.assertIn('Passed runners configuration file fail_config_path does not exist.', out.getvalue())

    @mock.patch('autoscaler.services.bitbucket.BitbucketService.get_bitbucket_workspace_repository_uuids')
    @mock.patch('autoscaler.cleaner.pct_runner_idle_cleaner.Cleaner.run')
    @mock.patch('autoscaler.services.kubernetes.KubernetesService.init')
    def test_main(
            self,
            mock_kubernetes_service,
            mock_run,
            mock_get_uuids
    ):
        mock_get_uuids.return_value = (
            {'name': 'test-workspace-name', 'uuid': 'test-workspace-uuid'},
            {'name': 'test-repo-name', 'uuid': 'test-repo-uuid'},
        )
        mock_run.return_value = None
        mock_kubernetes_service.return_value = None

        cleaner = StartCleaner(
            config_file_path='tests/resources/test_config.yaml',
            poll=False
        )

        cleaner.run()

        self.assertEqual(mock_run.call_count, 2)

    @mock.patch('autoscaler.services.bitbucket.BitbucketService.get_bitbucket_workspace_repository_uuids')
    def test_main_namespace_required(self, mock_skip_update):
        mock_skip_update.return_value = {'name': 'test', 'uuid': 'test'}, {'name': 'test', 'uuid': 'test'}

        cleaner = StartCleaner(
            config_file_path='tests/resources/test_config_no_namespace.yaml',
            poll=False
        )

        with capture_output() as out:
            with pytest.raises(SystemExit) as pytest_wrapped_e:
                cleaner.run()

        self.assertEqual(pytest_wrapped_e.type, SystemExit)
        self.assertIn('namespace\n  field required', out.getvalue())

    @mock.patch('autoscaler.services.bitbucket.BitbucketService.get_bitbucket_workspace_repository_uuids')
    def test_main_namespace_reserved(self, mock_skip_update):
        mock_skip_update.return_value = {'name': 'test', 'uuid': 'test'}, {'name': 'test', 'uuid': 'test'}

        cleaner = StartCleaner(
            config_file_path='tests/resources/test_config_reserved_namespace.yaml',
            poll=False
        )

        with capture_output() as out:
            with pytest.raises(SystemExit) as pytest_wrapped_e:
                cleaner.run()

        self.assertEqual(pytest_wrapped_e.type, SystemExit)
        self.assertIn(
            f'namespace name `{DEFAULT_RUNNER_KUBERNETES_NAMESPACE}` is reserved and not available.',
            out.getvalue()
        )

    @mock.patch('autoscaler.services.bitbucket.BitbucketService.get_bitbucket_workspace_repository_uuids')
    def test_main_workspace_required(self, mock_skip_update):
        mock_skip_update.return_value = {'name': 'test', 'uuid': 'test'}, {'name': 'test', 'uuid': 'test'}

        cleaner = StartCleaner(
            config_file_path='tests/resources/test_config_no_workspace.yaml',
            poll=False
        )

        with capture_output() as out:
            with pytest.raises(SystemExit) as pytest_wrapped_e:
                cleaner.run()

        self.assertEqual(pytest_wrapped_e.type, SystemExit)
        self.assertIn('workspace\n  field required', out.getvalue())


@mock.patch.dict(os.environ, {'BITBUCKET_USERNAME': 'test', 'BITBUCKET_APP_PASSWORD': 'test', 'DEBUG': 'true'})
class CleanerTestCase(TestCase):

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
                    'status': 'OFFLINE',
                    'updated_on': '2021-09-29T23:55:14.857790Z',
                    'version': {'current': '1.184'}
                },
                'updated_on': '2021-09-29T23:55:14.857791Z',
                'uuid': '{670ea89c-e64d-5923-8ccc-06d67fae8039}'
            }]
        )
        runner_data = GroupMeta.construct(**{
            'workspace': NameUUIDData(**{
                'name': 'workspace-test',
                'uuid': '{workspace-test-uuid}'
            }),
            'repository': NameUUIDData(**{
                'name': 'repository-test',
                'uuid': '{repository-test-uuid}'
            }),
            'name': 'good',
            'namespace': 'test',
            'strategy': 'custom'
        })

        runner_count_scaler = Cleaner(
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
                        'status': 'OFFLINE',
                        'updated_on': '2021-09-29T23:55:14.857790Z',
                        'version': {'current': '1.184'}
                    },
                    'updated_on': '2021-09-29T23:55:14.857791Z',
                    'uuid': '{670ea89c-e64d-5923-8ccc-06d67fae8039}'}
            ]
        )

    @mock.patch('autoscaler.cleaner.pct_runner_idle_cleaner.Cleaner.get_runners')
    @mock.patch('autoscaler.services.bitbucket.BitbucketService.delete_bitbucket_runner')
    def test_delete_runners_delete_part(self, mock_delete_runner, mock_get_runners):
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

        runner_data = GroupMeta.construct(**{
            'workspace': NameUUIDData(**{
                'name': 'workspace-test',
                'uuid': '{workspace-test-uuid}'
            }),
            'repository': NameUUIDData(**{
                'name': 'repository-test',
                'uuid': '{repository-test-uuid}'
            }),
            'name': 'good',
            'namespace': 'test',
            'strategy': 'percentageRunnersIdle'
        })

        service = Cleaner(
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

    @mock.patch('autoscaler.cleaner.pct_runner_idle_cleaner.Cleaner.get_runners')
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
                    'status': 'OFFLINE',
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
                    'status': 'UNREGISTERED',
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
                    'status': 'OFFLINE',
                    'updated_on': '2021-09-29T23:55:14.857790Z',
                    'version': {'current': '1.184'}
                },
                'updated_on': '2021-09-29T23:55:14.857791Z',
                'uuid': '{670ea89c-e64d-5923-8ccc-06d67fae8037}'
            }
        ]
        mock_get_runners.return_value = get_runners

        runner_data = GroupMeta.construct(**{
            'workspace': NameUUIDData(**{
                'name': 'workspace-test',
                'uuid': '{workspace-test-uuid}'
            }),
            'repository': NameUUIDData(**{
                'name': 'repository-test',
                'uuid': '{repository-test-uuid}'
            }),
            'name': 'good',
            'namespace': 'test',
            'strategy': 'percentageRunnersIdle'
        })

        service = Cleaner(
            runner_data=runner_data,
            runner_constants=Constants(default_sleep_time_runner_delete=1),
            kubernetes_service=KubernetesInMemoryService()
        )

        mock_delete_runner.return_value = None

        with capture_output() as out:
            service.run()

        self.assertIn('Successfully deleted runner UUID {670ea89c-e64d-5923-8ccc-06d67fae8037}'
                      ' on workspace workspace-test\n',
                      out.getvalue())

        self.assertIn('Successfully deleted runner UUID {670ea89c-e64d-5923-8ccc-06d67fae8038}'
                      ' on workspace workspace-test\n',
                      out.getvalue())

        self.assertIn('Successfully deleted runner UUID {670ea89c-e64d-5923-8ccc-06d67fae8039}'
                      ' on workspace workspace-test\n',
                      out.getvalue())

    @mock.patch('autoscaler.cleaner.pct_runner_idle_cleaner.Cleaner.get_runners')
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

        runner_data = GroupMeta.construct(**{
            'workspace': NameUUIDData(**{
                'name': 'workspace-test',
                'uuid': '{workspace-test-uuid}'
            }),
            'repository': NameUUIDData(**{
                'name': 'repository-test',
                'uuid': '{repository-test-uuid}'
            }),
            'name': 'good',
            'namespace': 'test',
            'strategy': 'percentageRunnersIdle'
        })

        cleaner = Cleaner(
            runner_data=runner_data,
            runner_constants=Constants(),
            kubernetes_service=KubernetesInMemoryService()
        )

        with self.caplog.at_level(logging.INFO):
            cleaner.run()

        self.assertIn('Nothing to do...\n', self.caplog.text)
