from dataclasses import dataclass

from autoscaler.clients.bitbucket.base import BitbucketRepository, BitbucketRepositoryRunner, BitbucketWorkspace, BitbucketWorkspaceRunner
from autoscaler.core.logger import logger, GroupNamePrefixAdapter
from autoscaler.core.helpers import string_to_base64string


@dataclass
class BitbucketByProjectServiceData:
    account_uuid: str
    project: str | None
    runner_uuid: str
    oauth_client_id_base64: str
    oauth_client_secret_base64: str


class BitbucketByProjectService:
    def __init__(self, group_name):
        self.logger_adapter = GroupNamePrefixAdapter(logger, {'name': group_name})

    def get_bitbucket_runners(self, workspace, project, **kwargs):
        msg = f"Getting runners on Bitbucket workspace: {workspace.name} and project {project.uuid}"

        self.logger_adapter.info(f"{msg} ...")

        workspace_runner_api = BitbucketWorkspaceRunner()
        runners = workspace_runner_api.get_runners(workspace.uuid)

        return runners

    def create_bitbucket_runner(self, workspace, name, labels, repository=None):
        start_msg = f"Starting to setup runner on Bitbucket workspace: {workspace.name}"
        create_complete_msg = f"Runner created on Bitbucket workspace: {workspace.name}"

        if repository:
            self.logger_adapter.info(f"{start_msg} repository: {repository.name} ...")

            repository_runner_api = BitbucketRepositoryRunner()
            data = repository_runner_api.create_runner(workspace.uuid, repository.uuid, name, tuple(labels))

            self.logger_adapter.info(f"{create_complete_msg} repository: {repository.name}")
        else:
            self.logger_adapter.info(f"{start_msg} ...")

            workspace_runner_api = BitbucketWorkspaceRunner()
            data = workspace_runner_api.create_runner(workspace.uuid, name, tuple(labels))

            self.logger_adapter.info(f"{create_complete_msg}")

        self.logger_adapter.debug(data)

        runner_data = BitbucketByProjectServiceData(
            account_uuid=workspace.uuid,
            project=repository.uuid if repository else None,
            runner_uuid=data["uuid"],
            oauth_client_id_base64=string_to_base64string(data["oauth_client"]["id"]),
            oauth_client_secret_base64=string_to_base64string(data["oauth_client"]["secret"])
        )

        self.logger_adapter.debug(runner_data)

        return runner_data

    def delete_bitbucket_runner(self, workspace, runner_uuid, repository=None):
        msg = f"Starting to delete runner {runner_uuid} from Bitbucket workspace: {workspace.name}"

        if repository:
            self.logger_adapter.info(f"{msg} repository: {repository.name} ...")

            repository_runner_api = BitbucketRepositoryRunner()
            repository_runner_api.delete_runner(workspace.uuid, repository.uuid, runner_uuid)
        else:
            self.logger_adapter.info(f"{msg} ...")

            workspace_runner_api = BitbucketWorkspaceRunner()
            workspace_runner_api.delete_runner(workspace.uuid, runner_uuid)

    def disable_bitbucket_runner(self, workspace, runner_uuid, repository=None):
        msg = f"Starting to disable runner {runner_uuid} from Bitbucket workspace: {workspace.name}"

        if repository:
            self.logger_adapter.info(f"{msg} repository: {repository.name} ...")

            repository_runner_api = BitbucketRepositoryRunner()
            repository_runner_api.disable_runner(workspace.uuid, repository.uuid, runner_uuid)
        else:
            self.logger_adapter.info(f"{msg} ...")

            workspace_runner_api = BitbucketWorkspaceRunner()
            workspace_runner_api.disable_runner(workspace.uuid, runner_uuid)

    @staticmethod
    def get_bitbucket_workspace_repository_uuids(workspace_name, project_uuid):
        workspace_api = BitbucketWorkspace()
        workspace_response = workspace_api.get_workspace(workspace_name)
        workspace_data = {
            'uuid': workspace_response['uuid'],
            'name': workspace_response['slug']
        }

        repository_data = None
        if project_uuid:
            repository_api = BitbucketRepository()
            query = "q=project.uuid=\"" + project_uuid + "\""
            repository_response = repository_api.get_repository_by_workspace(workspace_name, query)
            repository_data = {
                'uuid': repository_response['uuid'],
                'name': repository_response['slug']
            }

        return workspace_data, repository_data
