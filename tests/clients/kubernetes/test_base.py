from unittest import TestCase, mock

from autoscaler.clients.kubernetes.base import (KubernetesBaseAPIService,
                                                KubernetesSpecFileAPIService)
from autoscaler.core.constants import (DEFAULT_RUNNER_KUBERNETES_NAMESPACE,
                                       RUNNER_KUBERNETES_SPECS_DIR)
from tests.helpers import get_file


class KubernetesBaseAPIServiceTestCase(TestCase):

    @mock.patch('subprocess.run')
    def test_delete_job(self, subprocess_mock):
        subprocess_mock.return_value = mock.Mock(returncode=0)

        api = KubernetesBaseAPIService()
        api.delete_job('foo', 'bar')
        subprocess_mock.assert_called_once_with(
            ['kubectl', '-n', 'bar', 'delete', 'job', '-l', 'runnerUuid=foo'],
            capture_output=True,
            text=True,
            timeout=10
        )

    @mock.patch('subprocess.run')
    def test_get_kubernetes_version(self, subprocess_mock):
        subprocess_mock.return_value = mock.Mock(returncode=0)

        api = KubernetesBaseAPIService()
        api.get_kubernetes_version()
        subprocess_mock.assert_called_once_with(['kubectl', 'version'], capture_output=True, text=True, timeout=10)

    @mock.patch('subprocess.run')
    def test_get_kubernetes_config(self, subprocess_mock):
        subprocess_mock.return_value = mock.Mock(returncode=0)

        api = KubernetesBaseAPIService()
        api.get_kubernetes_config()
        subprocess_mock.assert_called_once_with(
            ['kubectl', 'config', 'view'],
            capture_output=True,
            text=True,
            timeout=10
        )

    @mock.patch('subprocess.run')
    def test_get_or_create_kubernetes_namespace_not_created(self, subprocess_mock):
        process_mock = mock.Mock('foo', returncode=0, stdout='bar')

        subprocess_mock.return_value = process_mock
        subprocess_mock.return_value.check_returncode = mock.Mock('foo', returncode=0, stdout='bar')

        api = KubernetesBaseAPIService()
        result = api.get_or_create_kubernetes_namespace(namespace=DEFAULT_RUNNER_KUBERNETES_NAMESPACE)
        self.assertEqual(False, result)

    @mock.patch('subprocess.run')
    @mock.patch.object(KubernetesBaseAPIService.api, 'run_piped_command')
    def test_get_or_create_kubernetes_namespace_created(self, mock_create, subprocess_mock):
        process_mock = mock.Mock('foo', returncode=1, stdout='bar')

        subprocess_mock.return_value = process_mock
        subprocess_mock.return_value.check_returncode = mock.Mock('foo', returncode=1, stdout='bar')
        mock_create.return_value = None

        api = KubernetesBaseAPIService()
        result = api.get_or_create_kubernetes_namespace(namespace=DEFAULT_RUNNER_KUBERNETES_NAMESPACE)
        self.assertEqual(True, result)

    @mock.patch.object(KubernetesBaseAPIService.api, 'run_piped_command')
    def test_create_kubernetes_namespace(self, mock_create):
        mock_create.return_value = 'baz'

        api = KubernetesBaseAPIService()
        result = api.create_kubernetes_namespace(namespace=DEFAULT_RUNNER_KUBERNETES_NAMESPACE)
        self.assertEqual('baz', result)

    @mock.patch.object(KubernetesBaseAPIService.api, 'run_piped_command')
    def test_create_apply_spec(self, mock_create):
        mock_create.return_value = 'baz'

        api = KubernetesBaseAPIService()
        result = api.create_apply_spec('foo')
        self.assertEqual('baz', result)


class KubernetesSpecFileAPIServiceTestCase(TestCase):

    def test_generate_kube_spec_file(self):
        runner_data = {
            'accountUuid': 'account',
            'repositoryUuid': 'repo',
            'runnerUuid': 'runner',
            'oauthClientId_base64': 'testID',
            'oauthClientSecret_base64': 'testSecret',
            'runnerNamespace': 'namespace'
        }
        api = KubernetesSpecFileAPIService()
        output = api.generate_kube_spec_file(runner_data=runner_data)

        assert output == get_file('job-default.yaml')

    @mock.patch('subprocess.run')
    def test_apply_kubernetes_spec_file(self, subprocess_mock):
        subprocess_mock.return_value = mock.Mock(returncode=0)

        api = KubernetesSpecFileAPIService()
        api.apply_kubernetes_spec_file('foo', 'bar')
        subprocess_mock.assert_called_once_with(
            ['kubectl', '-n', 'bar', 'apply', '-f', 'foo'],
            capture_output=True,
            text=True,
            timeout=10
        )

    @mock.patch('autoscaler.clients.kubernetes.base.open')
    def test_create_kube_spec_file(self, mocked_create):
        runner_data = {
            'accountUuid': 'account',
            'repositoryUuid': 'repo',
            'runnerUuid': 'runner',
            'oauthClientId_base64': 'testID',
            'oauthClientSecret_base64': 'testSecret',
            'runnerNamespace': 'namespace'
        }
        api = KubernetesSpecFileAPIService()

        api.create_kube_spec_file(runner_data)

        mocked_create.assert_called_once_with(f'{RUNNER_KUBERNETES_SPECS_DIR}/runner-runner.yaml', 'w')

    @mock.patch('pathlib.Path.unlink')
    def test_delete_kube_spec_file(self, mocked_delete):
        api = KubernetesSpecFileAPIService()

        api.delete_kube_spec_file('test')

        mocked_delete.assert_called_once_with(missing_ok=True)
