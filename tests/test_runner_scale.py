import os
import argparse
import logging
from unittest import TestCase, mock

import pytest

import runner_scale
from tests.helpers import capture_output


@mock.patch.dict(os.environ, {'BITBUCKET_USERNAME': 'test', 'BITBUCKET_APP_PASSWORD': 'test'})
class RunnerScaleTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self.caplog = caplog

    @mock.patch('subprocess.run')
    @mock.patch('argparse.ArgumentParser.parse_args')
    def test_wrong_arguments(self, mock_args, mock_validate_kubernetes):
        mock_validate_kubernetes.return_value = mock.Mock(returncode=0)
        mock_validate_kubernetes.return_value.check_returncode = mock.Mock(returncode=0)
        mock_args.return_value = argparse.Namespace(test='foo')

        with pytest.raises(AttributeError) as pytest_wrapped_e:
            runner_scale.main()

        self.assertTrue(mock_args.called)
        self.assertEqual(pytest_wrapped_e.type, AttributeError)
        self.assertIn("AttributeError: 'Namespace' object has no attribute 'config'", str(pytest_wrapped_e))

    @mock.patch('subprocess.run')
    @mock.patch('argparse.ArgumentParser.parse_args')
    def test_config_not_found(self, mock_args, mock_validate_kubernetes):
        mock_validate_kubernetes.return_value = mock.Mock(returncode=0)
        mock_validate_kubernetes.return_value.check_returncode = mock.Mock(returncode=0)
        mock_args.return_value = argparse.Namespace(config='fail_config_path')

        with capture_output() as out:
            with pytest.raises(SystemExit) as pytest_wrapped_e:
                runner_scale.main()

        self.assertTrue(mock_args.called)
        self.assertEqual(pytest_wrapped_e.type, SystemExit)
        self.assertIn('Passed runners configuration file fail_config_path does not exist.', out.getvalue())

    @mock.patch('subprocess.run')
    @mock.patch('argparse.ArgumentParser.parse_args')
    @mock.patch('runner.check_kubernetes_namespace')
    @mock.patch('manual.count_scaler.BitbucketRunnerCountScaler.run')
    def test_main_manual(self, mock_run, mock_namespace, mock_args, mock_validate_kubernetes):
        mock_validate_kubernetes.return_value = mock.Mock(returncode=0)
        mock_validate_kubernetes.return_value.check_returncode = mock.Mock(returncode=0)
        mock_args.return_value = argparse.Namespace(config='tests/test_config_manual.yaml')
        mock_namespace.return_value = None
        mock_run.return_value = None

        with self.caplog.at_level(logging.INFO):
            runner_scale.main()

        self.assertIn('Working on runners data', self.caplog.text)
        assert mock_args.called
        assert mock_namespace.called
        assert mock_run.called

    @mock.patch('subprocess.run')
    @mock.patch('argparse.ArgumentParser.parse_args')
    @mock.patch('runner.check_kubernetes_namespace')
    @mock.patch('apis.kubernetes.base.KubernetesSpecFileAPIService.generate_kube_spec_file')
    @mock.patch('apis.kubernetes.base.KubernetesSpecFileAPIService.apply_kubernetes_spec_file')
    @mock.patch('runner_scale.open')
    def test_main_automatic(
            self,
            mocked_create,
            mock_apply,
            mock_generate_spec,
            mock_namespace,
            mock_args,
            mock_validate_kubernetes
    ):
        mock_validate_kubernetes.return_value = mock.Mock(returncode=0)
        mock_validate_kubernetes.return_value.check_returncode = mock.Mock(returncode=0)
        mock_args.return_value = argparse.Namespace(config='tests/test_config_automatic.yaml')
        mock_namespace.return_value = None
        mock_generate_spec.return_value = None
        mock_apply.return_value = 'test'

        with self.caplog.at_level(logging.INFO):
            runner_scale.main()

        assert mock_args.called
        assert mock_namespace.called
        assert mock_generate_spec.called
        assert mock_apply.called
        mocked_create.assert_called_once_with('controller-spec.yml', 'w')
        self.assertIn('test', self.caplog.text)
