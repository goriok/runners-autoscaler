import os
from time import sleep
from pprint import pprint

import autoscaler.runner as runner
from autoscaler.core.logger import logger
from autoscaler.core.helpers import success
from autoscaler.clients.bitbucket.base import BitbucketRunnerStatuses
from autoscaler.core.constants import DEFAULT_SLEEP_TIME_RUNNER_SETUP, DEFAULT_SLEEP_TIME_RUNNER_DELETE


class ManualRunnersScaler:

    def __init__(self, runner_data):
        self.runner_data = runner_data

    def get_runners(self):
        # TODO optimize GET requests with filters by labels
        return runner.get_bitbucket_runners(self.runner_data['workspace'], self.runner_data['repository'])

    def run(self):
        # TODO move to manual worflow
        # TODO optimize GET requests with filters by labels
        runners = self.get_runners()

        msg = f"Found {len(runners)} runners on workspace {self.runner_data['workspace']['name']}"
        if self.runner_data['repository']:
            msg = f"{msg} repository: {self.runner_data['repository']['name']}"
        logger.info(msg)

        if os.getenv('DEBUG') == 'true':
            pprint(runners)

        online_runners = [
            r for r in runners if
            set(r['labels']) == self.runner_data['labels'] and r['state']['status'] == BitbucketRunnerStatuses.online.value
        ]

        logger.info(f"Found ONLINE runners with labels {self.runner_data['labels']}: {len(online_runners)}")
        logger.debug(online_runners)

        runners_idle = [r for r in online_runners if r['state'].get('step') is None]

        logger.info(f"Found IDLE runners with labels {self.runner_data['labels']}: {len(runners_idle)}")
        if os.getenv('DEBUG') == 'true':
            pprint(runners_idle)

        if self.runner_data['parameters'].get('runners_count') > len(online_runners):
            # create new runners
            logger.info(f"Starting to setup {self.runner_data['parameters'].get('runners_count') - len(online_runners)} new runners...")

            count_runners_to_create = self.runner_data['parameters'].get('runners_count') - len(online_runners)

            for i in range(count_runners_to_create):
                logger.info(f"Runner #{i + 1} for namespace: {self.runner_data['namespace']} setup...")

                data = runner.create_bitbucket_runner(
                    workspace=self.runner_data['workspace'],
                    repository=self.runner_data['repository'],
                    name=self.runner_data.get('name'),
                    labels=self.runner_data['labels'],
                )

                data['runnerNamespace'] = self.runner_data['namespace']
                runner.setup_job(data)

                success(
                    f"Successfully setup runner UUID {data['runnerUuid']} "
                    f"on workspace {self.runner_data['workspace']['name']}\n",
                    do_exit=False
                )

                sleep(DEFAULT_SLEEP_TIME_RUNNER_SETUP)

        elif self.runner_data['parameters'].get('runners_count') < len(online_runners):
            # delete only idle runners
            # TODO delete logic
            if len(runners_idle) < 1:
                logger.warning("Nothing to delete... All runners are BUSY (running jobs).")
                return

            if len(runners_idle) > self.runner_data['parameters'].get('runners_count'):
                count_runners_to_delete = len(runners_idle) - self.runner_data['parameters'].get('runners_count')
            else:
                count_runners_to_delete = len(runners_idle)

            runners_uuid_to_delete = [r['uuid'].strip('{}') for r in runners_idle][:count_runners_to_delete]

            logger.warning(f"Runners count {len(runners_uuid_to_delete)} with the next UUID will be deleted:"
                           f" {runners_uuid_to_delete}")

            for runner_uuid in runners_uuid_to_delete:
                runner.delete_bitbucket_runner(
                    workspace=self.runner_data['workspace'],
                    repository=self.runner_data['repository'],
                    runner_uuid=runner_uuid
                )
                runner.delete_job(runner_uuid, self.runner_data['namespace'])

                success(
                    f"Successfully deleted runner UUID {runner_uuid} "
                    f"on workspace {self.runner_data['workspace']['name']}\n",
                    do_exit=False
                )
                sleep(DEFAULT_SLEEP_TIME_RUNNER_DELETE)
        else:
            # show message to user that ok
            logger.warning("Nothing to do...\n")
