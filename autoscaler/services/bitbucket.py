from autoscaler.clients.bitbucket.base import BitbucketRepository, BitbucketRepositoryRunner, BitbucketWorkspace, BitbucketWorkspaceRunner
from autoscaler.core.logger import logger, GroupNamePrefixAdapter
from autoscaler.core.helpers import string_to_base64string


class BitbucketService:
    def __init__(self, group_name):
        self.logger_adapter = GroupNamePrefixAdapter(logger, {'name': group_name})

    def get_bitbucket_runners(self, workspace, repository=None):
        msg = f"Getting runners on Bitbucket workspace: {workspace['name']}"

        if repository:
            self.logger_adapter.info(f"{msg} repository: {repository['name']} ...")

            repository_runner_api = BitbucketRepositoryRunner()
            runners_data = repository_runner_api.get_runners(workspace['uuid'], repository['uuid'])
        else:
            self.logger_adapter.info(f"{msg} ...")

            workspace_runner_api = BitbucketWorkspaceRunner()
            runners_data = workspace_runner_api.get_runners(workspace['uuid'])

        return runners_data['values']

    def create_bitbucket_runner(self, workspace, repository=None, name='test', labels=('test',)):
        start_msg = f"Starting to setup runner on Bitbucket workspace: {workspace['name']}"
        create_complete_msg = f"Runner created on Bitbucket workspace: {workspace['name']}"

        if repository:
            self.logger_adapter.info(f"{start_msg} repository: {repository['name']} ...")

            repository_runner_api = BitbucketRepositoryRunner()
            data = repository_runner_api.create_runner(workspace['uuid'], repository['uuid'], name, tuple(labels))

            self.logger_adapter.info(f"{create_complete_msg} repository: {repository['name']}")
        else:
            self.logger_adapter.info(f"{start_msg} ...")

            workspace_runner_api = BitbucketWorkspaceRunner()
            data = workspace_runner_api.create_runner(workspace['uuid'], name, tuple(labels))

            self.logger_adapter.info(f"{create_complete_msg}")

        self.logger_adapter.debug(data)

        runner_data = {
            "accountUuid": workspace['uuid'],
            "repositoryUuid": repository['uuid'] if repository else None,
            "runnerUuid": data["uuid"].strip('{}'),
            "oauthClientId_base64": string_to_base64string(data["oauth_client"]["id"]),
            "oauthClientSecret_base64": string_to_base64string(data["oauth_client"]["secret"]),
        }

        self.logger_adapter.debug(runner_data)

        return runner_data

    def delete_bitbucket_runner(self, workspace, runner_uuid, repository=None):
        msg = f"Starting to delete runner {runner_uuid} from Bitbucket workspace: {workspace['name']}"

        if repository:
            self.logger_adapter.info(f"{msg} repository: {repository['name']} ...")

            repository_runner_api = BitbucketRepositoryRunner()
            repository_runner_api.delete_runner(workspace['uuid'], repository['uuid'], runner_uuid)
        else:
            self.logger_adapter.info(f"{msg} ...")

            workspace_runner_api = BitbucketWorkspaceRunner()
            workspace_runner_api.delete_runner(workspace['uuid'], runner_uuid)

    @staticmethod
    def get_bitbucket_workspace_repository_uuids(workspace_name, repository_name):
        workspace_api = BitbucketWorkspace()
        workspace_response = workspace_api.get_workspace(workspace_name)
        workspace_data = {
            'uuid': workspace_response['uuid'].strip('{}'),
            'name': workspace_response['slug']
        }

        repository_data = None
        if repository_name:
            repository_api = BitbucketRepository()
            repository_response = repository_api.get_repository(workspace_name, repository_name)
            repository_data = {
                'uuid': repository_response['uuid'].strip('{}'),
                'name': repository_response['slug']
            }

        return workspace_data, repository_data
