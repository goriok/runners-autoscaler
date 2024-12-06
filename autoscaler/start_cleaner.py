from concurrent.futures import ThreadPoolExecutor, wait
from time import sleep

from autoscaler.services.bitbucket_by_project import BitbucketByProjectService
from autoscaler.cleaner.pct_runner_idle_cleaner_by_project import CleanerByProject
from autoscaler.cleaner.pct_runner_idle_cleaner import Cleaner
from pydantic import ValidationError

import autoscaler.core.constants as constants
import autoscaler.core.validators as validators
from autoscaler.cleaner.pct_runner_idle_cleaner import Cleaner
from autoscaler.core.exceptions import AutoscalerHTTPError
from autoscaler.core.help_classes import Strategies
from autoscaler.core.helpers import fail, enable_debug
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
        # validate Authorization
        validators.validate_auth()

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

                    if runner_data.strategy == Strategies.PCT_RUNNER_IDLE_BY_PROJECT.value:
                        kubernetes_service = KubernetesService(runner_data.name)

                        runner_service = BitbucketByProjectService(runner_data.name)

                        cleaner = CleanerByProject(runner_data, runner_constants, kubernetes_service, runner_service)

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

        try:
            runners_data = validators.RunnerCleanerData.parse_file(self.config_file_path)
        except ValidationError as e:
            fail(e)
        except AutoscalerHTTPError as e:
            fail(f'Unauthorized. Check your bitbucket credentials. {e}')
        else:
            logger.info(f"Autoscaler runners: {runners_data.groups}")

            return runners_data.groups, runners_data.constants


def main():
    cleaner = StartCleaner(config_file_path='/opt/conf/config/runners_config.yaml')

    cleaner.run()


if __name__ == '__main__':
    main()
