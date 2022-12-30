import logging
import os
from unittest import TestCase, mock

import pytest

from autoscaler.services.kubernetes import KubernetesService
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

        runner_data = {
            'runner_namespace': 'test-namespace',
            'uuid': '{test-uuid}',
            'name': 'good',
            'labels': ['self.hosted', 'asd', 'linux'],
            'state': {
                'status': 'UNREGISTERED',
                'version': {'version': '1.252'},
                'updated_on': '2021-12-03T18:20:22.561088Z'
            },
            'created_on': '2021-12-03T18:20:22.561005Z',
            'updated_on': '2021-12-03T18:20:22.561005Z',
            'oauth_client': {
                'id': 'testid',
                'secret': 'testsecret',
                'token_endpoint': 'https://fake-api.auth0.com/oauth/token',
                'audience': 'api.fake-api.com'
            }
        }
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
