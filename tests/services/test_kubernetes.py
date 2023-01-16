import logging
import os
from unittest import TestCase, mock

import pytest

from autoscaler.services.kubernetes import KubernetesService, KubernetesServiceData
from autoscaler.core.exceptions import NamespaceNotFoundError


@mock.patch.dict(os.environ, {'BITBUCKET_USERNAME': 'test', 'BITBUCKET_APP_PASSWORD': 'test', 'DEBUG': 'true'})
class KubernetesServiceTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self.caplog = caplog

    @mock.patch('autoscaler.clients.kubernetes.base.KubernetesPythonAPIService.get_kubernetes_namespace')
    @mock.patch('autoscaler.clients.kubernetes.base.KubernetesPythonAPIService.load_config')
    def test_init_namespace_found(self, mock_config, mock_get):
        mock_config.return_value = None
        mock_get.return_value = None

        runner_data = {'namespace': 'test'}

        service: KubernetesService = KubernetesService('test')
        service.init(**runner_data)

        mock_get.assert_called_once_with(**runner_data)

    @mock.patch('autoscaler.clients.kubernetes.base.KubernetesPythonAPIService.get_kubernetes_namespace')
    @mock.patch('autoscaler.clients.kubernetes.base.KubernetesPythonAPIService.create_kubernetes_namespace')
    @mock.patch('autoscaler.clients.kubernetes.base.KubernetesPythonAPIService.load_config')
    def test_init_namespace_not_found_created(self, mock_config, mock_create, mock_get):
        mock_config.return_value = None
        mock_get.side_effect = NamespaceNotFoundError
        mock_create.return_value = None

        runner_data = {'namespace': 'test'}

        service: KubernetesService = KubernetesService('test')
        service.init(**runner_data)

        mock_get.assert_called_once_with(**runner_data)
        mock_create.assert_called_once_with(**runner_data)

    @mock.patch('autoscaler.clients.kubernetes.base.KubernetesPythonAPIService.create_secret')
    @mock.patch('autoscaler.clients.kubernetes.base.KubernetesPythonAPIService.create_job')
    @mock.patch('autoscaler.clients.kubernetes.base.KubernetesPythonAPIService.load_config')
    def test_setup_job(self, mock_config, mock_create, mock_secret):
        mock_config.return_value = None
        mock_create.return_value.metadata.name = None
        mock_secret.return_value.metadata.name = None

        runner_data = KubernetesServiceData(
            account_uuid='test-workspace-uuid',
            runner_uuid='test-uuid',
            oauth_client_id_base64='test-oauth',
            oauth_client_secret_base64='test-secret',
            runner_namespace='test-namespace',
            repository_uuid='test-repository-uuid'
        )

        service: KubernetesService = KubernetesService('test')

        with self.caplog.at_level(logging.INFO):
            service.setup_job(runner_data)

        mock_create.assert_called_once()
        mock_config.assert_called_once()
        mock_secret.assert_called_once()

    @mock.patch('autoscaler.clients.kubernetes.base.KubernetesPythonAPIService.delete_secret')
    @mock.patch('autoscaler.clients.kubernetes.base.KubernetesPythonAPIService.delete_job')
    @mock.patch('autoscaler.clients.kubernetes.base.KubernetesPythonAPIService.load_config')
    def test_delete_job(self, mock_config, mock_delete_job, mock_delete_secret):
        mock_delete_secret.return_value = None
        mock_delete_job.return_value = None
        mock_config.return_value = None

        runner_data = {'namespace': 'test-namespace', 'runner_uuid': 'test-uuid'}

        service: KubernetesService = KubernetesService('test')
        service.delete_job(**runner_data)

        mock_delete_job.assert_called_once_with('test-uuid', 'test-namespace')
