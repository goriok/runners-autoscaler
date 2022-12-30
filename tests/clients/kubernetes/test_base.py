from kubernetes.client import ApiException
from unittest import TestCase, mock

import autoscaler.core.exceptions as core_exc
from autoscaler.clients.kubernetes.base import KubernetesSpecFileAPIService, KubernetesPythonAPIService
from tests.helpers import get_file


class KubernetesSpecFileAPIServiceTestCase(TestCase):

    def test_generate_kube_spec_file(self):
        runner_data = {
            'account_uuid': 'account',
            'repository_uuid': 'repo',
            'runner_uuid': 'runner',
            'oauth_client_id_base64': 'testID',
            'oauth_client_secret_base64': 'testSecret',
            'runner_namespace': 'namespace'
        }
        api = KubernetesSpecFileAPIService()
        output = api.generate_kube_spec_file(runner_data=runner_data)

        assert output == get_file('job-default.yaml')


class KubernetesPythonAPIServiceTestCase(TestCase):

    @mock.patch('kubernetes.config.load_incluster_config')
    def test_load_config(self, mock_config):
        KubernetesPythonAPIService()

        mock_config.assert_called_once()

    @mock.patch('kubernetes.config.load_incluster_config')
    @mock.patch('kubernetes.client.CoreV1Api.create_namespaced_secret')
    def test_create_secret(self, mock_create, mock_config):
        mock_config.return_value = None
        api = KubernetesPythonAPIService()
        api.create_secret('foo', 'bar')

        mock_create.assert_called_once_with(body='foo', namespace='bar')

    @mock.patch('kubernetes.config.load_incluster_config')
    @mock.patch('kubernetes.client.BatchV1Api.create_namespaced_job')
    def test_create_job(self, mock_create, mock_config):
        mock_config.return_value = None
        api = KubernetesPythonAPIService()
        api.create_job('foo', 'bar')

        mock_create.assert_called_once_with(body='foo', namespace='bar')

    @mock.patch('kubernetes.config.load_incluster_config')
    @mock.patch('kubernetes.client.CoreV1Api.delete_namespaced_secret')
    @mock.patch('kubernetes.client.V1DeleteOptions')
    def test_delete_secret(self, mock_client_delete, mock_delete, mock_config):
        mock_config.return_value = None
        mock_client_delete.return_value = None
        api = KubernetesPythonAPIService()

        api.delete_secret('foo', 'bar')

        mock_delete.assert_called_once_with(name='runner-oauth-credentials-foo', namespace='bar', body=None)

    @mock.patch('kubernetes.config.load_incluster_config')
    @mock.patch('kubernetes.client.CoreV1Api.delete_namespaced_secret')
    @mock.patch('kubernetes.client.V1DeleteOptions')
    def test_delete_secret_error(self, mock_client_delete, mock_delete, mock_config):
        mock_config.return_value = None
        mock_client_delete.return_value = None
        mock_delete.side_effect = ApiException
        api = KubernetesPythonAPIService()
        with self.assertRaises(core_exc.KubernetesSecretError):
            api.delete_secret('foo', 'bar')

        mock_delete.assert_called_once_with(name='runner-oauth-credentials-foo', namespace='bar', body=None)
        self.assertRaises(core_exc.KubernetesSecretError, api.delete_secret, 'foo', 'bar')

    @mock.patch('kubernetes.config.load_incluster_config')
    @mock.patch('kubernetes.client.CoreV1Api.delete_namespaced_secret')
    @mock.patch('kubernetes.client.V1DeleteOptions')
    def test_delete_secret_not_found(self, mock_client_delete, mock_delete, mock_config):
        mock_config.return_value = None
        mock_client_delete.return_value = None
        mock_delete.side_effect = ApiException(status=404)
        api = KubernetesPythonAPIService()
        with self.assertRaises(core_exc.SecretNotFoundError):
            api.delete_secret('foo', 'bar')

        mock_delete.assert_called_once_with(name='runner-oauth-credentials-foo', namespace='bar', body=None)
        self.assertRaises(core_exc.SecretNotFoundError, api.delete_secret, 'foo', 'bar')

    @mock.patch('kubernetes.config.load_incluster_config')
    @mock.patch('kubernetes.client.BatchV1Api.delete_namespaced_job')
    @mock.patch('kubernetes.client.V1DeleteOptions')
    def test_delete_job(self, mock_client_delete, mock_delete, mock_config):
        mock_config.return_value = None
        mock_client_delete.return_value = None
        api = KubernetesPythonAPIService()

        api.delete_job('foo', 'bar')

        mock_delete.assert_called_once_with(name='runner-foo', namespace='bar', body=None)

    @mock.patch('kubernetes.config.load_incluster_config')
    @mock.patch('kubernetes.client.BatchV1Api.delete_namespaced_job')
    @mock.patch('kubernetes.client.V1DeleteOptions')
    def test_delete_job_error(self, mock_client_delete, mock_delete, mock_config):
        mock_config.return_value = None
        mock_client_delete.return_value = None
        mock_delete.side_effect = ApiException
        api = KubernetesPythonAPIService()
        with self.assertRaises(core_exc.KubernetesJobError):
            api.delete_job('foo', 'bar')

        mock_delete.assert_called_once_with(name='runner-foo', namespace='bar', body=None)
        self.assertRaises(core_exc.KubernetesJobError, api.delete_job, 'foo', 'bar')

    @mock.patch('kubernetes.config.load_incluster_config')
    @mock.patch('kubernetes.client.BatchV1Api.delete_namespaced_job')
    @mock.patch('kubernetes.client.V1DeleteOptions')
    def test_delete_job_not_found(self, mock_client_delete, mock_delete, mock_config):
        mock_config.return_value = None
        mock_client_delete.return_value = None
        mock_delete.side_effect = ApiException(status=404)
        api = KubernetesPythonAPIService()
        with self.assertRaises(core_exc.JobNotFoundError):
            api.delete_job('foo', 'bar')

        mock_delete.assert_called_once_with(name='runner-foo', namespace='bar', body=None)
        self.assertRaises(core_exc.JobNotFoundError, api.delete_job, 'foo', 'bar')

    @mock.patch('kubernetes.config.load_incluster_config')
    @mock.patch('kubernetes.client.CoreV1Api.read_namespace')
    def test_get_kubernetes_namespace(self, mock_get, mock_config):
        mock_config.return_value = None
        api = KubernetesPythonAPIService()
        api.get_kubernetes_namespace('foo')

        mock_get.assert_called_once_with(name='foo')

    @mock.patch('kubernetes.config.load_incluster_config')
    @mock.patch('kubernetes.client.CoreV1Api.read_namespace')
    def test_get_kubernetes_namespace_error(self, mock_get, mock_config):
        mock_config.return_value = None
        mock_get.side_effect = ApiException
        api = KubernetesPythonAPIService()
        with self.assertRaises(core_exc.KubernetesNamespaceError):
            api.get_kubernetes_namespace('foo')

        mock_get.assert_called_once_with(name='foo')
        self.assertRaises(core_exc.KubernetesNamespaceError, api.get_kubernetes_namespace, 'foo')

    @mock.patch('kubernetes.config.load_incluster_config')
    @mock.patch('kubernetes.client.CoreV1Api.read_namespace')
    def test_get_kubernetes_namespace_not_found(self, mock_get, mock_config):
        mock_config.return_value = None
        mock_get.side_effect = ApiException(status=404)
        api = KubernetesPythonAPIService()
        with self.assertRaises(core_exc.NamespaceNotFoundError):
            api.get_kubernetes_namespace('foo')

        mock_get.assert_called_once_with(name='foo')
        self.assertRaises(core_exc.NamespaceNotFoundError, api.get_kubernetes_namespace, 'foo')

    @mock.patch('kubernetes.config.load_incluster_config')
    @mock.patch('kubernetes.client.CoreV1Api.create_namespace')
    @mock.patch('kubernetes.client.V1Namespace')
    @mock.patch('kubernetes.client.V1ObjectMeta')
    def test_create_kubernetes_namespace(self, mock_client_create_meta, mock_client_create, mock_create, mock_config):
        mock_config.return_value = None
        mock_client_create.return_value = 'foo'
        mock_client_create_meta.return_value = 'foo'
        api = KubernetesPythonAPIService()
        api.create_kubernetes_namespace('foo')

        mock_create.assert_called_once_with('foo')

    @mock.patch('kubernetes.config.load_incluster_config')
    @mock.patch('kubernetes.client.CoreV1Api.create_namespace')
    @mock.patch('kubernetes.client.V1Namespace')
    @mock.patch('kubernetes.client.V1ObjectMeta')
    def test_create_kubernetes_namespace_error(self, mock_client_create_meta, mock_client_create, mock_create, mock_config):
        mock_config.return_value = None
        mock_client_create.return_value = 'foo'
        mock_client_create_meta.return_value = 'foo'
        mock_create.side_effect = ApiException
        api = KubernetesPythonAPIService()
        with self.assertRaises(core_exc.CannotCreateNamespaceError):
            api.create_kubernetes_namespace('foo')

        mock_create.assert_called_once_with('foo')
        self.assertRaises(core_exc.CannotCreateNamespaceError, api.create_kubernetes_namespace, 'foo')
