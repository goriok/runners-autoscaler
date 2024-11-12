from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from dateutil import parser as du_parser
from time import sleep

from autoscaler.core.constants import AUTOSCALER_RUNNER
from autoscaler.core.help_classes import BitbucketRunnerStatuses
from autoscaler.core.helpers import success
from autoscaler.core.logger import logger, GroupNamePrefixAdapter
from autoscaler.core.validators import Constants, NameUUIDData
from autoscaler.services.bitbucket_by_project import BitbucketByProjectService
from autoscaler.services.kubernetes import KubernetesService


@dataclass
class PctRunnersIdleCleanerByProjectData:
    workspace: NameUUIDData
    project: NameUUIDData | None
    name: str
    namespace: str
    strategy: str


class Cleaner:
    def __init__(self, runner_data: PctRunnersIdleCleanerByProjectData, runner_constants: Constants, kubernetes_service=None, runner_service=None):
        self.runner_data = runner_data
        self.runner_constants = runner_constants
        self.kubernetes_service = kubernetes_service if kubernetes_service else KubernetesService(runner_data.name)
        self.runner_service = runner_service if runner_service else BitbucketByProjectService(runner_data.name)
        self.logger_adapter = GroupNamePrefixAdapter(logger, {'name': runner_data.name})

    def get_repositories(self):
        return self.runner_service.get_bitbucket_workspace_repository_uuids(self.runner_data.workspace.name, self.runner_data.project.uuid)

    def get_runners(self, repository):
        return self.runner_service.get_bitbucket_runners(self.runner_data.workspace, repository)

    def delete_runners(self, runners_to_delete, repository):
        runners_uuid_to_delete = [r['uuid'] for r in runners_to_delete]

        for runner_uuid in runners_uuid_to_delete:
            self.runner_service.delete_bitbucket_runner(
                workspace=self.runner_data.workspace,
                runner_uuid=runner_uuid,
                repository=repository,
            )

            # Remove curly brackets, because for kubernetes service runners names are without them.
            self.kubernetes_service.delete_job(runner_uuid.strip('{}'), self.runner_data.namespace)

            success(
                f"[{self.runner_data.name}] Successfully deleted runner UUID {runner_uuid} "
                f"on workspace {self.runner_data.workspace.name}\n",
                do_exit=False
            )

            sleep(self.runner_constants.default_sleep_time_runner_delete)

    def run(self):
        workflow, repositories = self.get_repositories()
        for repository in repositories:
            runners = self.get_runners(repository)

            msg = f"Found {len(runners)} runners on workspace {self.runner_data.workspace.name}"
            if repository:
                msg = f"{msg} repository: {repository.name}"

            self.logger_adapter.info(msg)

            if runners:
                runners_stats = dict(Counter([r['state'].get('status') for r in runners]))
                self.logger_adapter.info(runners_stats)

            self.logger_adapter.debug(runners)

            # Delete runners that are not online, created by autoscaler tool, and created more than configured time ago.
            runners_to_delete_not_online_or_disabled = [
                r for r in runners if
                r['state']['status'] != BitbucketRunnerStatuses.ONLINE and
                r['state']['status'] != BitbucketRunnerStatuses.DISABLED and
                AUTOSCALER_RUNNER in r['labels'] and
                du_parser.isoparse(r['state']['updated_on']) + timedelta(
                    seconds=self.runner_constants.runner_cool_down_period) < datetime.now(timezone.utc)
            ]
            runners_to_delete_disabled = [
                r for r in runners if
                r['state']['status'] == BitbucketRunnerStatuses.DISABLED and
                r['state'].get('step') is None and
                AUTOSCALER_RUNNER in r['labels'] and
                du_parser.isoparse(r['state']['updated_on']) + timedelta(
                    seconds=self.runner_constants.runner_cool_down_period) < datetime.now(timezone.utc)
            ]
            runners_to_delete = runners_to_delete_not_online_or_disabled + runners_to_delete_disabled

            self.logger_adapter.info(f"Number of runners to delete found: {len(runners_to_delete)}.")

            self.logger_adapter.debug(runners_to_delete)

            if runners_to_delete:
                self.delete_runners(runners_to_delete, repository)
            else:
                self.logger_adapter.warning("Nothing to do...\n")
