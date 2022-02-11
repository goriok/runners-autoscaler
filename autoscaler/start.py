import os
from time import sleep
from concurrent.futures import ThreadPoolExecutor, wait

import autoscaler.core.constants as constants
from autoscaler.core.helpers import read_yaml_file, required, enable_debug, fail
from autoscaler.core.help_classes import Constants, Strategies, RunnerData, NameUUIDData
from autoscaler.core.logger import logger
from autoscaler.services.kubernetes import KubernetesService
from autoscaler.services.bitbucket import BitbucketService
from autoscaler.strategy.pct_runners_idle import PctRunnersIdleScaler


DEFAULT_LABELS = frozenset({'self.hosted', 'linux'})
MIN_RUNNERS_COUNT = 0
MAX_RUNNERS_COUNT = 100
MAX_GROUPS_COUNT = 10


class StartPoller:
    def __init__(self, config_file_path: str, poll: bool = True):
        self.config_file_path = config_file_path
        self.poll = poll

    def start(self):
        enable_debug()
        # required environment variables BITBUCKET_USERNAME and BITBUCKET_APP_PASSWORD
        required('BITBUCKET_USERNAME')
        required('BITBUCKET_APP_PASSWORD')

        # read runners parameter from the config file
        config_file_path = self.config_file_path

        logger.info(f"Config file provided {config_file_path}.")

        if not os.path.exists(config_file_path):
            fail(f'Passed runners configuration file {config_file_path} does not exist.')

        runners_data = read_yaml_file(config_file_path)

        logger.info(f"Autoscaler config: {runners_data}")

        if 'constants' in runners_data:
            runner_constants = Constants(
                runners_data['constants'].get('default_sleep_time_runner_setup', constants.DEFAULT_SLEEP_TIME_RUNNER_DELETE),
                runners_data['constants'].get('default_sleep_time_runner_delete', constants.DEFAULT_SLEEP_TIME_RUNNER_SETUP),
                runners_data['constants'].get('runner_api_polling_interval', constants.BITBUCKET_RUNNER_API_POLLING_INTERVAL),
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
        with ThreadPoolExecutor(max_workers=MAX_GROUPS_COUNT) as executor:
            while True:
                futures = []
                for runner_data in autoscaler_runners:
                    runner_data: RunnerData
                    if runner_data.strategy == Strategies.PCT_RUNNER_IDLE.value:
                        kubernetes_service = KubernetesService(runner_data.name)

                        runner_service = BitbucketService(runner_data.name)

                        pctRunnersIdleScaler = PctRunnersIdleScaler(runner_data, runner_constants, kubernetes_service, runner_service)

                        futures.append(executor.submit(pctRunnersIdleScaler.process))

                wait(futures)
                for fut in futures:
                    fut.result()

                logger.info(
                    f"Autoscaler next attempt in {runner_constants.runner_api_polling_interval} seconds...\n")

                sleep(runner_constants.runner_api_polling_interval)

                # Added for testing.
                if not self.poll:
                    break


def validate(runner_data):
    # TODO validate args. Refactor conditional blocks with validator usage.
    # TODO optimize this logic
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

    if runner_data.get('parameters') is None:
        fail('Parameters required for runner.')

    if runner_data.get('strategy') is None:
        fail('Strategy required for runner.')


def update(runner_data):
    labels = set(DEFAULT_LABELS)
    labels.update(runner_data.get('labels'))
    runner_data['labels'] = labels

    workspace_data, repository_data = BitbucketService.get_bitbucket_workspace_repository_uuids(
        workspace_name=runner_data['workspace'],
        repository_name=runner_data['repository']
    )

    runner_data['workspace'] = NameUUIDData(
        name=workspace_data['name'],
        uuid=workspace_data['uuid'],
    )

    runner_data['repository'] = NameUUIDData(
        name=repository_data['name'],
        uuid=repository_data['uuid'],
    )

    # Update parameters for different strategies
    if runner_data['strategy'] == Strategies.PCT_RUNNER_IDLE.value:
        try:
            runner_data['parameters'] = PctRunnersIdleScaler.update_parameters(runner_data)
        except KeyError as e:
            fail(f"{runner_data['name']}: parameter is missing {e}")
    else:
        fail(f'{runner_data["name"]}: strategy {runner_data["strategy"]} not supported.')

    return RunnerData(
        workspace=runner_data['workspace'],
        repository=runner_data['repository'],
        name=runner_data['name'],
        labels=runner_data['labels'],
        namespace=runner_data['namespace'],
        strategy=runner_data['strategy'],
        parameters=runner_data['parameters']
    )


def main():
    poller = StartPoller(config_file_path='/opt/conf/config/runners_config.yaml')
    poller.start()


if __name__ == '__main__':
    main()
