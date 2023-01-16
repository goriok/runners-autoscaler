from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from dateutil import parser as du_parser
from time import sleep

from autoscaler.core.help_classes import BitbucketRunnerStatuses
from autoscaler.core.helpers import success
from autoscaler.core.logger import logger, GroupNamePrefixAdapter
from autoscaler.core.validators import Constants, NameUUIDData
from autoscaler.services.bitbucket import BitbucketService
from autoscaler.services.kubernetes import KubernetesService


@dataclass
class PctRunnersIdleCleanerData:
    workspace: NameUUIDData
    repository: NameUUIDData | None
    name: str
    namespace: str
    strategy: str


class Cleaner:
    def __init__(self, runner_data: PctRunnersIdleCleanerData, runner_constants: Constants, kubernetes_service=None, runner_service=None):
        self.runner_data = runner_data
        self.runner_constants = runner_constants
        self.kubernetes_service = kubernetes_service if kubernetes_service else KubernetesService(runner_data.name)
        self.runner_service = runner_service if runner_service else BitbucketService(runner_data.name)
        self.logger_adapter = GroupNamePrefixAdapter(logger, {'name': runner_data.name})

    def get_runners(self):
        # TODO optimize GET requests with filters by labels
        return self.runner_service.get_bitbucket_runners(self.runner_data.workspace, self.runner_data.repository)

    def delete_runners(self, runners_to_delete):
        # delete only old runners
        # TODO: consider to change case from created_on to updated_on to not delete old runners what recently changed
        #  their status to not ONLINE.
        runners_uuid_to_delete = [
            r['uuid'] for r in runners_to_delete if du_parser.isoparse(r['created_on']) + timedelta(
                seconds=self.runner_constants.runner_cool_down_period) < datetime.now(timezone.utc)
        ]

        if runners_uuid_to_delete:
            self.logger_adapter.warning(
                f"Runners count {len(runners_uuid_to_delete)} with the next UUID will be deleted:"
                f" {runners_uuid_to_delete}"
            )
        else:
            self.logger_adapter.warning(
                f"Nothing to delete... "
                f"All runners are created less than coolDownPeriod: "
                f"{self.runner_constants.runner_cool_down_period} sec ago."
            )

        for runner_uuid in runners_uuid_to_delete:
            self.runner_service.delete_bitbucket_runner(
                workspace=self.runner_data.workspace,
                runner_uuid=runner_uuid,
                repository=self.runner_data.repository
            )

            # Remove curly brackets, because for kubernetes service runners names are without them
            self.kubernetes_service.delete_job(runner_uuid.strip('{}'), self.runner_data.namespace)

            success(
                f"[{self.runner_data.name}] Successfully deleted runner UUID {runner_uuid} "
                f"on workspace {self.runner_data.workspace.name}\n",
                do_exit=False
            )

            sleep(self.runner_constants.default_sleep_time_runner_delete)

    def run(self):
        runners = self.get_runners()

        msg = f"Found {len(runners)} runners on workspace {self.runner_data.workspace.name}"
        if self.runner_data.repository:
            msg = f"{msg} repository: {self.runner_data.repository.name}"

        self.logger_adapter.info(msg)

        if runners:
            runners_stats = dict(Counter([r['state'].get('status') for r in runners]))
            self.logger_adapter.info(runners_stats)

        self.logger_adapter.debug(runners)

        not_online_runners = [
            r for r in runners if
            r['state']['status'] != BitbucketRunnerStatuses.ONLINE
        ]

        self.logger_adapter.info(f"Found NOT ONLINE runners: {len(not_online_runners)}")
        self.logger_adapter.debug(not_online_runners)

        if not_online_runners:
            self.delete_runners(not_online_runners)
        else:
            self.logger_adapter.warning("Nothing to do...\n")
