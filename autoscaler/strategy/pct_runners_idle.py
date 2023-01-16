import math
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from dateutil import parser as du_parser
from time import sleep
from typing import Set

from autoscaler.core.exceptions import KubernetesNamespaceError, CannotCreateNamespaceError
from autoscaler.core.help_classes import BitbucketRunnerStatuses
from autoscaler.core.helpers import success, fail
from autoscaler.core.interfaces import Strategy
from autoscaler.core.logger import logger, GroupNamePrefixAdapter
from autoscaler.core.validators import Constants, NameUUIDData, PctRunnersIdleParameters
from autoscaler.services.kubernetes import KubernetesService, KubernetesServiceData
from autoscaler.services.bitbucket import BitbucketService, BitbucketServiceData


MAX_RUNNERS_COUNT = 100
SCALE_UP_MULTIPLIER = 1.5
SCALE_DOWN_MULTIPLIER = 0.5


@dataclass
class PctRunnersIdleData:
    workspace: NameUUIDData
    repository: NameUUIDData | None
    name: str
    namespace: str
    strategy: str
    labels: Set[str]
    parameters: PctRunnersIdleParameters


class PctRunnersIdleScaler(Strategy):
    def __init__(self, runner_data: PctRunnersIdleData, runner_constants: Constants, kubernetes_service=None, runner_service=None):
        self.runner_data = runner_data
        self.runner_constants = runner_constants
        self.kubernetes_service = kubernetes_service if kubernetes_service else KubernetesService(runner_data.name)
        self.runner_service = runner_service if runner_service else BitbucketService(runner_data.name)
        self.logger_adapter = GroupNamePrefixAdapter(logger, {'name': runner_data.name})

    @staticmethod
    def convert_bitbucket_data_to_k8s_data(bitbucket_data: BitbucketServiceData, namespace) -> KubernetesServiceData:
        """
        Bitbucket workspace, repository and runners uuids have curly brackets i.e {some-uuid} format.
        Kubernetes labels does not allow to use curly brackets for values so this method reformat
        bitbucket data to kubernetes data without curly brackets and also add data for namespace.
        """
        return KubernetesServiceData(
            account_uuid=bitbucket_data.account_uuid.strip('{}'),
            repository_uuid=bitbucket_data.repository_uuid.strip('{}') if bitbucket_data.repository_uuid else None,
            runner_uuid=bitbucket_data.runner_uuid.strip('{}'),
            oauth_client_id_base64=bitbucket_data.oauth_client_id_base64,
            oauth_client_secret_base64=bitbucket_data.oauth_client_secret_base64,
            runner_namespace=namespace
        )

    def validate(self):
        try:
            self.kubernetes_service.init(self.runner_data.namespace)
        except CannotCreateNamespaceError as e:
            fail(f"Couldn't create namespace: {self.runner_data.namespace}. Error {e}")
        except KubernetesNamespaceError as e:
            fail(f"Couldn't get namespace: {self.runner_data.namespace}. Error {e}")

    def process(self):
        self.logger_adapter.info(f"Working on runner group: {self.runner_data}")

        # TODO move to k8s pod
        self.validate()

        self.run()

    def get_runners(self):
        # TODO optimize GET requests with filters by labels
        return self.runner_service.get_bitbucket_runners(self.runner_data.workspace, self.runner_data.repository)

    def create_runner(self, count_number):
        runners = self.get_runners()

        if runners:
            runners_stats = dict(Counter([r['state'].get('status') for r in runners]))
            self.logger_adapter.debug(runners_stats)

        # check runners count before add new runner
        if len(runners) >= MAX_RUNNERS_COUNT:
            msg = f"Max Runners count limit reached {len(runners)} per workspace {self.runner_data.workspace.name}"
            if self.runner_data.repository:
                msg = f"{msg} repository: {self.runner_data.repository.name}"

            self.logger_adapter.warning(msg)
            self.logger_adapter.warning(
                "No new runners will be created! Check your runners. Check you runner's config file.")

            return

        self.logger_adapter.info(f"Runner #{count_number + 1} for namespace: {self.runner_data.namespace} setup...")

        bitbucket_data = self.runner_service.create_bitbucket_runner(
            workspace=self.runner_data.workspace,
            name=self.runner_data.name,
            labels=self.runner_data.labels,
            repository=self.runner_data.repository
        )

        kubernetes_data = self.convert_bitbucket_data_to_k8s_data(bitbucket_data, self.runner_data.namespace)

        self.kubernetes_service.setup_job(kubernetes_data)

        success(
            f"[{self.runner_data.name}] Successfully setup runner UUID {bitbucket_data.runner_uuid} "
            f"on workspace {self.runner_data.workspace.name}\n",
            do_exit=False
        )

        sleep(self.runner_constants.default_sleep_time_runner_setup)

    def delete_runners(self, runners_idle):
        # delete only idle runners
        if len(runners_idle) < 1:
            self.logger_adapter.warning("Nothing to delete... All runners are BUSY (running jobs).")
            return

        # delete only old runners
        runners_uuid_to_delete = [
            r['uuid'] for r in runners_idle if du_parser.isoparse(r['created_on']) + timedelta(
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

        online_runners = [
            r for r in runners if
            set(r['labels']) == self.runner_data.labels and r['state']['status'] == BitbucketRunnerStatuses.ONLINE
        ]

        self.logger_adapter.info(f"Found ONLINE runners with labels {self.runner_data.labels}: {len(online_runners)}")
        self.logger_adapter.debug(online_runners)

        runners_idle = [r for r in online_runners if r['state'].get('step') is None]
        runners_busy = [r for r in online_runners if 'step' in r['state']]

        self.logger_adapter.info(f"Found IDLE runners with labels {self.runner_data.labels}: {len(runners_idle)}")
        self.logger_adapter.debug(runners_idle)

        runners_scale_threshold = len(runners_busy) / len(online_runners) if online_runners else 0
        self.logger_adapter.info(f'Current runners threshold: {round(runners_scale_threshold, 2)}')

        msg_autoscaler = (
            f"Runners Autoscaler. "
            f"min: {self.runner_data.parameters.min}, "
            f"max: {self.runner_data.parameters.max}, "
            f"current: {len(online_runners)}"
        )

        if not online_runners and self.runner_data.parameters.min > 0:
            # create new runners from 0
            count_runners_to_create = self.runner_data.parameters.min

            msg_autoscaler = (
                f"{msg_autoscaler}, "
                f"desired: {count_runners_to_create}. "
                f"Changing the desired capacity "
                f"from {len(online_runners)} to {count_runners_to_create}.\n"
            )
            self.logger_adapter.info(msg_autoscaler)

            for i in range(count_runners_to_create):
                # Do not try to create new runners when total number of runners
                # reached max allowed by API. Still show the message warning
                # when total number of runners is equal the MAX_RUNNERS_COUNT.
                if len(runners) + i > MAX_RUNNERS_COUNT:
                    break

                self.create_runner(i)

        # TODO add max_runners per repo or max_runners per workspace
        elif (runners_scale_threshold > float(self.runner_data.parameters.scale_up_threshold) or len(online_runners) < self.runner_data.parameters.min) \
                and len(online_runners) <= self.runner_data.parameters.max \
                and len(runners) <= MAX_RUNNERS_COUNT:

            # TODO validate scaleDownFactor > 1
            desired_runners_count = math.ceil(
                len(online_runners) * self.runner_data.parameters.scale_up_multiplier
            )
            if desired_runners_count <= self.runner_data.parameters.max:
                count_runners_to_create = desired_runners_count - len(online_runners)
            else:
                count_runners_to_create = self.runner_data.parameters.max - len(online_runners)
                desired_runners_count = self.runner_data.parameters.max

            if count_runners_to_create == 0:
                self.logger_adapter.info(f"Max runners count: {self.runner_data.parameters.max} reached.")
                return

            msg_autoscaler = (
                f"{msg_autoscaler}, "
                f"desired: {desired_runners_count}. "
                f"Changing the desired capacity "
                f"from {len(online_runners)} to {desired_runners_count}.\n"
            )
            self.logger_adapter.info(msg_autoscaler)

            for i in range(count_runners_to_create):
                # Do not try to create new runners when total number of runners
                # reached max allowed by API. Still show the message warning
                # when total number of runners is equal the MAX_RUNNERS_COUNT.
                if len(runners) + i > MAX_RUNNERS_COUNT:
                    break

                self.create_runner(i)

        elif runners_scale_threshold < float(self.runner_data.parameters.scale_down_threshold) and \
                len(runners_idle) > self.runner_data.parameters.min:

            # TODO validate 0 < scaleDownFactor < 1
            desired_runners_count = math.floor(
                len(runners_idle) * self.runner_data.parameters.scale_down_multiplier
            )

            if desired_runners_count > self.runner_data.parameters.min:
                count_runners_to_delete = len(runners_idle) - desired_runners_count
            else:
                count_runners_to_delete = len(runners_idle) - self.runner_data.parameters.min
                desired_runners_count = self.runner_data.parameters.min

            runners_idle_to_delete = runners_idle[:count_runners_to_delete]

            msg_autoscaler = (
                f"{msg_autoscaler}, "
                f"idle: {len(runners_idle)}, "
                f"desired: {desired_runners_count}. "
                f"Changing the desired capacity "
                f"from {len(runners_idle)} to {desired_runners_count}.\n"
            )
            self.logger_adapter.info(msg_autoscaler)

            self.delete_runners(runners_idle_to_delete)

        else:
            # show message to user that ok
            self.logger_adapter.info(msg_autoscaler)
            self.logger_adapter.warning("Nothing to do...\n")
