import os
from time import sleep

import autoscaler.core.constants as constants
from autoscaler.core.helpers import read_yaml_file, required, enable_debug, fail
from autoscaler.core.help_classes import Constants
from autoscaler.core.logger import logger
from autoscaler.services.kubernetes import KubernetesService
from autoscaler.services.bitbucket import BitbucketService
from autoscaler.strategy.pct_runners_idle import PctRunnersIdleScaler


DEFAULT_LABELS = {'self.hosted', 'linux'}
MIN_RUNNERS_COUNT = 0
MAX_RUNNERS_COUNT = 100


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

        kubernetes_service: KubernetesService = KubernetesService()
        runner_service: BitbucketService = BitbucketService()

        if 'constants' in runners_data:
            runner_constants = Constants(
                runners_data['constants'].get('default_sleep_time_runner_setup', constants.DEFAULT_SLEEP_TIME_RUNNER_DELETE),
                runners_data['constants'].get('default_sleep_time_runner_delete', constants.DEFAULT_SLEEP_TIME_RUNNER_SETUP),
                runners_data['constants'].get('runner_api_polling_interval', constants.BITBUCKET_RUNNER_API_POLLING_INTERVAL),
                runners_data['constants'].get('runner_cool_down_period', constants.RUNNER_COOL_DOWN_PERIOD)
            )
        else:
            runner_constants = Constants()

        for runner_data in runners_data['config']:
            # TODO validate args. Refactor conditional blocks with validator usage.
            # TODO optimize this logic
            if runner_data.get('namespace') is None:
                fail('Namespace required for runner.')
            elif runner_data['namespace'] == constants.DEFAULT_RUNNER_KUBERNETES_NAMESPACE:
                fail(f'Namespace name `{constants.DEFAULT_RUNNER_KUBERNETES_NAMESPACE}` is reserved and not available.')

            if runner_data.get('workspace') is None:
                fail('Workspace required for runner.')

            if runner_data.get('repository') is None:
                runner_data['repository'] = None

            labels = set()
            labels.update(DEFAULT_LABELS)
            labels.update(set(runner_data.get('labels')))
            runner_data['labels'] = labels

            workspace_data, repository_data = runner_service.get_bitbucket_workspace_repository_uuids(
                workspace_name=runner_data['workspace'],
                repository_name=runner_data['repository']
            )

            runner_data['workspace'] = workspace_data
            runner_data['repository'] = repository_data

        autoscale_runners = [r for r in runners_data['config'] if r['strategy'] == 'percentageRunnersIdle']

        for runner_data in autoscale_runners[:1]:
            logger.info(f"Working on runners: {runner_data}")

            # TODO add validator for autoscaler parameters
            # TODO move to k8s pod
            autoscaler = PctRunnersIdleScaler(runner_data, runner_constants, kubernetes_service, runner_service)
            autoscaler.validate()

            while True:
                autoscaler.run()
                logger.warning(f"AUTOSCALER next attempt in {runner_constants.runner_api_polling_interval} seconds...\n")
                sleep(runner_constants.runner_api_polling_interval)

                # Added for testing.
                if not self.poll:
                    break


def main():
    poller = StartPoller(config_file_path='/opt/conf/config/runners_config.yaml')
    poller.start()


if __name__ == '__main__':
    main()