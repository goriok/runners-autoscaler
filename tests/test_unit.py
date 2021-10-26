import os
from unittest import TestCase, mock

import runner


@mock.patch.dict(os.environ, {'BITBUCKET_USERNAME': 'test', 'BITBUCKET_APP_PASSWORD': 'test'})
class BitbucketGroupTestCase(TestCase):

    @mock.patch.object(runner.BitbucketWorkspaceRunner, 'make_http_request')
    def test_get_runners(self, mock_http_request):
        mock_http_request.return_value = ({
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
                    'uuid': '{670ea89c-e64d-5923-8ccc-06d67fae8039}'},
            ]},
            200
        )
        result = runner.get_bitbucket_runners('fake_workspace')
        self.assertEqual(
            list(result),
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
                    'uuid': '{670ea89c-e64d-5923-8ccc-06d67fae8039}'},
            ]
        )

    @mock.patch.object(runner.BitbucketWorkspaceRunner, 'make_http_request')
    def test_create_runner(self, mock_http_request):
        mock_http_request.return_value = ({
            'values': [
                {
                    'uuid': '{8bae4096-fa58-573c-9b62-1bfdf316a36f}',
                    'name': 'group_1',
                    'labels': ['abc', 'self.hosted', 'linux'],
                    'state': {
                        'status': 'UNREGISTERED',
                        'updated_on': '2021-10-11T06:41:39.064097Z'
                    }, 'created_on': '2021-10-11T06:41:39.064038Z',
                    'updated_on': '2021-10-11T06:41:39.064038Z',
                    'oauth_client': {
                        'id': 'fjtCg06lHzQQCK7HXZ93RM6ulZkxJqC0',
                        'secret': 'super-secret',
                        'token_endpoint': 'https://fake-api.auth0.com/oauth/token',
                        'audience': 'api.fake-api.com'
                    }
                },
            ]},
            200
        )
        result = runner.get_bitbucket_runners('fake_workspace')
        self.assertEqual(
            list(result),
            [
                {
                    'uuid': '{8bae4096-fa58-573c-9b62-1bfdf316a36f}',
                    'name': 'group_1',
                    'labels': ['abc', 'self.hosted', 'linux'],
                    'state': {
                        'status': 'UNREGISTERED',
                        'updated_on': '2021-10-11T06:41:39.064097Z'
                    }, 'created_on': '2021-10-11T06:41:39.064038Z',
                    'updated_on': '2021-10-11T06:41:39.064038Z',
                    'oauth_client': {
                        'id': 'fjtCg06lHzQQCK7HXZ93RM6ulZkxJqC0',
                        'secret': 'super-secret',
                        'token_endpoint': 'https://fake-api.auth0.com/oauth/token',
                        'audience': 'api.fake-api.com'
                    }
                },
            ]
        )


class KubernetesGroupTestCase(TestCase):

    @mock.patch('subprocess.run')
    def test_eks_run_with_role_arn(self, subprocess_mock):
        subprocess_mock.return_value = mock.Mock(returncode=0)

        api = runner.KubernetesBaseAPIService()
        api.get_kubernetes_version()
        subprocess_mock.assert_called_once_with(['kubectl', 'version'], capture_output=True, text=True, timeout=5)
