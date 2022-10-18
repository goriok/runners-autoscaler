from concurrent.futures import ThreadPoolExecutor, wait
from time import sleep

import autoscaler.core.constants as constants
import autoscaler.core.validators as validators
from autoscaler.cleaner.pct_runner_idle_cleaner import Cleaner
from autoscaler.core.help_classes import Strategies
from autoscaler.core.helpers import read_yaml_file, enable_debug, required
from autoscaler.core.logger import logger
from autoscaler.services.bitbucket import BitbucketService
from autoscaler.services.kubernetes import KubernetesService


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

        with ThreadPoolExecutor(max_workers=constants.MAX_GROUPS_COUNT) as executor:
            while True:
                autoscaler_runners, runner_constants = self.read_config()

                futures = []
                for runner_data in autoscaler_runners:
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
        logger.info(f"Config file provided {self.config_file_path}.")

        # read runners parameter from the config file
        validators.validate_config(self.config_file_path)

        runners_data = read_yaml_file(self.config_file_path)

        runner_constants = validators.init_constants(runners_data)

        autoscaler_runner_groups = [r for r in runners_data['groups']]

        validators.validate_group_count(len(autoscaler_runner_groups))

        for i, data in enumerate(autoscaler_runner_groups):
            validators.validate_runner_data(data, only_cleaner=True)

            autoscaler_runner_groups[i] = validators.update_runner_data(data, only_cleaner=True)

        logger.info(f"Autoscaler runners: {autoscaler_runner_groups}")

        return autoscaler_runner_groups, runner_constants


def main():
    cleaner = StartCleaner(config_file_path='/opt/conf/config/runners_config.yaml')
    cleaner.run()


if __name__ == '__main__':
    main()
