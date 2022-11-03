import os
from unittest import TestCase, mock

import pytest
from autoscaler.start import StartPoller
from autoscaler.core.constants import DEFAULT_RUNNER_KUBERNETES_NAMESPACE

from tests.helpers import capture_output


@mock.patch.dict(os.environ, {'BITBUCKET_USERNAME': 'test', 'BITBUCKET_APP_PASSWORD': 'test'})
class ScaleTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self.caplog = caplog

    def test_config_not_found(self):

        poller = StartPoller(
            config_file_path='fail_config_path',
            template_file_path='fail_config_path',
            poll=False
        )

        with capture_output() as out:
            with pytest.raises(SystemExit) as pytest_wrapped_e:
                poller.start()

        self.assertEqual(pytest_wrapped_e.type, SystemExit)
        self.assertIn('Passed runners configuration file fail_config_path does not exist.', out.getvalue())

    @mock.patch('autoscaler.services.bitbucket.BitbucketService.get_bitbucket_workspace_repository_uuids')
    @mock.patch('autoscaler.strategy.pct_runners_idle.PctRunnersIdleScaler.process')
    @mock.patch('autoscaler.services.kubernetes.KubernetesService.init')
    def test_main(
            self,
            mock_kubernetes_service,
            mock_process,
            mock_get_uuids
    ):
        mock_get_uuids.return_value = (
            {'name': 'test-workspace-name', 'uuid': 'test-workspace-uuid'},
            {'name': 'test-repo-name', 'uuid': 'test-repo-uuid'},
        )
        mock_process.return_value = None
        mock_kubernetes_service.return_value = None

        poller = StartPoller(
            config_file_path='tests/resources/test_config.yaml',
            template_file_path='tests/resources/job-default.yaml',
            poll=False
        )

        poller.start()

        self.assertEqual(mock_process.call_count, 2)

    @mock.patch('autoscaler.services.bitbucket.BitbucketService.get_bitbucket_workspace_repository_uuids')
    def test_main_namespace_required(self, mock_skip_update):
        mock_skip_update.return_value = {'name': 'test', 'uuid': 'test'}, {'name': 'test', 'uuid': 'test'}

        poller = StartPoller(
            config_file_path='tests/resources/test_config_no_namespace.yaml',
            template_file_path='tests/resources/job-default.yaml',
            poll=False
        )

        with capture_output() as out:
            with pytest.raises(SystemExit) as pytest_wrapped_e:
                poller.start()

        self.assertEqual(pytest_wrapped_e.type, SystemExit)
        self.assertIn('namespace\n  field required', out.getvalue())

    @mock.patch('autoscaler.services.bitbucket.BitbucketService.get_bitbucket_workspace_repository_uuids')
    def test_main_namespace_reserved(self, mock_skip_update):
        mock_skip_update.return_value = {'name': 'test', 'uuid': 'test'}, {'name': 'test', 'uuid': 'test'}

        poller = StartPoller(
            config_file_path='tests/resources/test_config_reserved_namespace.yaml',
            template_file_path='tests/resources/job-default.yaml',
            poll=False
        )

        with capture_output() as out:
            with pytest.raises(SystemExit) as pytest_wrapped_e:
                poller.start()

        self.assertEqual(pytest_wrapped_e.type, SystemExit)
        self.assertIn(
            f'namespace name `{DEFAULT_RUNNER_KUBERNETES_NAMESPACE}` is reserved and not available.',
            out.getvalue()
        )

    @mock.patch('autoscaler.services.bitbucket.BitbucketService.get_bitbucket_workspace_repository_uuids')
    def test_main_workspace_required(self, mock_skip_update):
        mock_skip_update.return_value = {'name': 'test', 'uuid': 'test'}, {'name': 'test', 'uuid': 'test'}

        poller = StartPoller(
            config_file_path='tests/resources/test_config_no_workspace.yaml',
            template_file_path='tests/resources/job-default.yaml',
            poll=False
        )

        with capture_output() as out:
            with pytest.raises(SystemExit) as pytest_wrapped_e:
                poller.start()

        self.assertEqual(pytest_wrapped_e.type, SystemExit)
        self.assertIn('workspace\n  field required', out.getvalue())
