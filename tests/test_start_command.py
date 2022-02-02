import argparse
import logging
import os
from unittest import TestCase, mock

import pytest

import autoscaler.start_command as scale
from autoscaler.core.constants import DEFAULT_RUNNER_KUBERNETES_NAMESPACE
from tests.helpers import capture_output


test_config_no_namespace = [
    {
        "name": "Runner repository group",
        "workspace": "test",
        "repository": "runner-test",
        "labels": ["self.hosted", "test", "linux"],
        "strategy": "percentageRunnersIdle",
        "parameters": {
            "min": 1,
            "max": 10,
            "scaleUpThreshold": 0.5,
            "scaleDownThreshold": 0.2,
            "scaleUpMultiplier": 1.5,
            "scaleDownMultiplier": 0.5
        }
    }
]


@mock.patch.dict(os.environ, {'BITBUCKET_USERNAME': 'test', 'BITBUCKET_APP_PASSWORD': 'test'})
class ScaleTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self.caplog = caplog

    @mock.patch('argparse.ArgumentParser.parse_args')
    def test_config_not_found(self, mock_args):
        mock_args.return_value = argparse.Namespace(config='fail_config_path')

        with capture_output() as out:
            with pytest.raises(SystemExit) as pytest_wrapped_e:
                scale.main()

        self.assertTrue(mock_args.called)
        self.assertEqual(pytest_wrapped_e.type, SystemExit)
        self.assertIn('Passed runners configuration file fail_config_path does not exist.', out.getvalue())

    @mock.patch('autoscaler.start_command.TESTING_BREAK_LOOP', True)
    @mock.patch('argparse.ArgumentParser.parse_args')
    @mock.patch('autoscaler.runner.get_bitbucket_workspace_repository_uuids')
    @mock.patch('autoscaler.strategy.pct_runners_idle.PctRunnersIdleScaler.run')
    @mock.patch('autoscaler.services.kubernetes.KubernetesService.check_kubernetes_namespace')
    def test_main(
            self,
            mock_kubernetes_service,
            mock_run,
            mock_get_uuids,
            mock_args
    ):
        mock_args.return_value = argparse.Namespace(config='tests/test_config.yaml')
        mock_get_uuids.return_value = ('test-workspace-uuid', 'test-repo-uuid')
        mock_run.return_value = None
        mock_kubernetes_service.return_value = None

        with self.caplog.at_level(logging.INFO):
            scale.main()

        assert mock_args.called
        assert mock_run.called
        self.assertIn('test', self.caplog.text)

    @mock.patch('argparse.ArgumentParser.parse_args')
    @mock.patch('autoscaler.runner.read_from_config')
    def test_main_namespace_required(
            self,
            mock_runner_data,
            mock_args
    ):
        mock_args.return_value = argparse.Namespace(config='tests/test_config.yaml')
        mock_runner_data.return_value = {'config': [{'foo': 'bar'}]}

        with capture_output() as out:
            with pytest.raises(SystemExit) as pytest_wrapped_e:
                scale.main()

        assert mock_args.called
        self.assertEqual(pytest_wrapped_e.type, SystemExit)
        self.assertIn('Namespace required for runner.', out.getvalue())

    @mock.patch('subprocess.run')
    @mock.patch('argparse.ArgumentParser.parse_args')
    @mock.patch('autoscaler.runner.read_from_config')
    def test_main_namespace_reserved(
            self,
            mock_runner_data,
            mock_args,
            mock_validate_kubernetes
    ):
        mock_validate_kubernetes.return_value = mock.Mock(returncode=0)
        mock_validate_kubernetes.return_value.check_returncode = mock.Mock(returncode=0)
        mock_args.return_value = argparse.Namespace(config='tests/test_config.yaml')
        mock_runner_data.return_value = {'config': [{'namespace': DEFAULT_RUNNER_KUBERNETES_NAMESPACE}]}

        with capture_output() as out:
            with pytest.raises(SystemExit) as pytest_wrapped_e:
                scale.main()

        assert mock_args.called
        self.assertEqual(pytest_wrapped_e.type, SystemExit)
        self.assertIn(
            f'Namespace name `{DEFAULT_RUNNER_KUBERNETES_NAMESPACE}` is reserved and not available.',
            out.getvalue()
        )

    @mock.patch('argparse.ArgumentParser.parse_args')
    @mock.patch('autoscaler.runner.read_from_config')
    def test_main_workspace_required(
            self,
            mock_runner_data,
            mock_args
    ):
        mock_args.return_value = argparse.Namespace(config='tests/test_config.yaml')
        mock_runner_data.return_value = {'config': [{'namespace': 'test'}]}

        with capture_output() as out:
            with pytest.raises(SystemExit) as pytest_wrapped_e:
                scale.main()

        assert mock_args.called
        self.assertEqual(pytest_wrapped_e.type, SystemExit)
        self.assertIn('Workspace required for runner.', out.getvalue())
