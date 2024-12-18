import os
import shutil
from concurrent.futures import ThreadPoolExecutor, wait
from time import sleep

from pydantic import ValidationError

import autoscaler.core.constants as constants
import autoscaler.core.validators as validators
from autoscaler.core.helpers import enable_debug, fail
from autoscaler.core.help_classes import Strategies
from autoscaler.core.logger import logger
from autoscaler.core.exceptions import AutoscalerHTTPError
from autoscaler.services.kubernetes import KubernetesService
from autoscaler.services.bitbucket import BitbucketService
from autoscaler.services.bitbucket_by_project import BitbucketByProjectService
from autoscaler.strategy.pct_runners_idle import PctRunnersIdleScaler
from autoscaler.strategy.pct_runners_idle_by_project import PctRunnersIdleByProjectScaler


class StartPoller:
    def __init__(self, config_file_path: str, template_file_path: str, poll: bool = True):
        self.config_file_path = config_file_path
        self.template_file_path = template_file_path
        self.poll = poll

    def start(self):
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

                        pctRunnersIdleScaler = PctRunnersIdleScaler(runner_data, runner_constants, kubernetes_service, runner_service)

                        futures.append(executor.submit(pctRunnersIdleScaler.process))
                    if runner_data.strategy == Strategies.PCT_RUNNER_IDLE_BY_PROJECT.value:
                        kubernetes_service = KubernetesService(runner_data.name)

                        runner_service = BitbucketByProjectService(runner_data.name)

                        autoscaler = PctRunnersIdleByProjectScaler(runner_data, runner_constants, kubernetes_service, runner_service)

                        futures.append(executor.submit(autoscaler.process))

                wait(futures)
                for fut in futures:
                    fut.result()

                logger.info(
                    f"Autoscaler next attempt in {runner_constants.runner_api_polling_interval} seconds...\n")

                sleep(runner_constants.runner_api_polling_interval)

                # Added for testing.
                if not self.poll:
                    break

    def read_config(self):
        logger.info(f"Config file provided {self.config_file_path}.")

        # read runners parameter from the config file
        validators.validate_config(self.config_file_path, self.template_file_path)

        destination_path = os.path.join(constants.DEST_TEMPLATE_FILE_PATH, constants.TEMPLATE_FILE_NAME)
        shutil.copy(self.template_file_path, destination_path)
        logger.info(f'File {self.template_file_path} copied to {destination_path}')

        try:
            runners_data = validators.RunnerData.parse_file(self.config_file_path)
            validators.validate_kubernetes_manifest(constants.TEMPLATE_FILE_NAME)
        except ValidationError as e:
            fail(e)
        except AutoscalerHTTPError as e:
            fail(f'Unauthorized. Check your bitbucket credentials. {e}')
        else:
            logger.info(f"Autoscaler config: {runners_data}")

            logger.info(f"Autoscaler runners: {runners_data.groups}")

            return runners_data.groups, runners_data.constants


def main():
    poller = StartPoller(config_file_path='/opt/conf/config/runners_config.yaml',
                         template_file_path='/opt/conf/job_template/job.yaml.template')

    poller.start()


if __name__ == '__main__':
    main()
