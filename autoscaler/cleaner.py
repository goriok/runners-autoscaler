import os
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, wait
from datetime import datetime, timedelta, timezone
from dateutil import parser as du_parser
from time import sleep

import autoscaler.core.constants as constants
from autoscaler.core.help_classes import Constants, RunnerMeta, NameUUIDData, BitbucketRunnerStatuses, Strategies
from autoscaler.core.helpers import success, fail, read_yaml_file, enable_debug, required
from autoscaler.core.logger import logger, GroupNamePrefixAdapter
from autoscaler.services.bitbucket import BitbucketService
from autoscaler.services.kubernetes import KubernetesService


MAX_GROUPS_COUNT = 10


class StartCleaner:
    def __init__(self, config_file_path: str, poll: bool = True):
        self.config_file_path = config_file_path
        self.poll = poll

    def run(self):
        logger.info("Runners cleaner started...")
        enable_debug()
        # required environment variables BITBUCKET_USERNAME and BITBUCKET_APP_PASSWORD
        required('BITBUCKET_USERNAME')
        required('BITBUCKET_APP_PASSWORD')

        with ThreadPoolExecutor(max_workers=MAX_GROUPS_COUNT) as executor:
            while True:
                autoscaler_runners, runner_constants = self.read_config()

                futures = []
                for runner_data in autoscaler_runners:
                    runner_data: RunnerMeta
                    if runner_data.strategy == Strategies.PCT_RUNNER_IDLE.value:
                        kubernetes_service = KubernetesService(runner_data.name)

                        runner_service = BitbucketService(runner_data.name)

                        cleaner = Cleaner(runner_data, runner_constants, kubernetes_service, runner_service)

                        futures.append(executor.submit(cleaner.run))

                wait(futures)
                for fut in futures:
                    fut.result()

                logger.info(
                    f"Cleaner next attempt in {runner_constants.runner_api_polling_interval} seconds...\n")

                sleep(runner_constants.runner_api_polling_interval)

                # Added for testing.
                if not self.poll:
                    break

    def read_config(self):
        # read runners parameter from the config file

        logger.info(f"Config file provided {self.config_file_path}.")

        if not os.path.exists(self.config_file_path):
            fail(f'Passed runners configuration file {self.config_file_path} does not exist.')

        runners_data = read_yaml_file(self.config_file_path)

        if 'constants' in runners_data:
            runner_constants = Constants(
                runners_data['constants'].get('default_sleep_time_runner_setup',
                                              constants.DEFAULT_SLEEP_TIME_RUNNER_DELETE),
                runners_data['constants'].get('default_sleep_time_runner_delete',
                                              constants.DEFAULT_SLEEP_TIME_RUNNER_SETUP),
                runners_data['constants'].get('runner_api_polling_interval',
                                              constants.BITBUCKET_RUNNER_API_POLLING_INTERVAL),
                runners_data['constants'].get('runner_cool_down_period', constants.RUNNER_COOL_DOWN_PERIOD)
            )
        else:
            runner_constants = Constants()

        autoscaler_runners = [r for r in runners_data['groups']]

        if len(autoscaler_runners) > MAX_GROUPS_COUNT:
            fail(f'Your groups count {len(autoscaler_runners)} exceeds maximum allowed count of {MAX_GROUPS_COUNT}')

        for i, data in enumerate(autoscaler_runners):
            validate(data)

            autoscaler_runners[i] = update(data)

        logger.info(f"Autoscaler runners: {autoscaler_runners}")

        return autoscaler_runners, runner_constants


class Cleaner:
    def __init__(self, runner_data: RunnerMeta, runner_constants: Constants, kubernetes_service=None, runner_service=None):
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
        runners_uuid_to_delete = [
            r['uuid'].strip('{}') for r in runners_to_delete if du_parser.isoparse(r['created_on']) + timedelta(
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

            self.kubernetes_service.delete_job(runner_uuid, self.runner_data.namespace)

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

        if os.getenv('DEBUG') == 'true':
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


def validate(runner_data):
    if runner_data.get('namespace') is None:
        fail('Namespace required for runner.')
    elif runner_data['namespace'] == constants.DEFAULT_RUNNER_KUBERNETES_NAMESPACE:
        fail(f'Namespace name `{constants.DEFAULT_RUNNER_KUBERNETES_NAMESPACE}` is reserved and not available.')

    if runner_data.get('name') is None:
        fail('Group name required for runner.')

    if runner_data.get('workspace') is None:
        fail('Workspace required for runner.')

    if runner_data.get('repository') is None:
        runner_data['repository'] = None


def update(runner_data):
    workspace_data, repository_data = BitbucketService.get_bitbucket_workspace_repository_uuids(
        workspace_name=runner_data['workspace'],
        repository_name=runner_data['repository']
    )

    runner_data['workspace'] = NameUUIDData(
        name=workspace_data['name'],
        uuid=workspace_data['uuid'],
    )

    if repository_data:
        runner_data['repository'] = NameUUIDData(
            name=repository_data['name'],
            uuid=repository_data['uuid'],
        )

    return RunnerMeta(
        workspace=runner_data['workspace'],
        repository=runner_data['repository'],
        name=runner_data['name'],
        namespace=runner_data['namespace'],
        strategy=runner_data['strategy']
    )


def main():
    cleaner = StartCleaner(config_file_path='/opt/conf/config/runners_config.yaml')
    cleaner.run()


if __name__ == '__main__':
    main()
