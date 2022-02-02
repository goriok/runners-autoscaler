import math
import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from dateutil import parser as du_parser
from pprint import pprint
from time import sleep

from autoscaler import runner
from autoscaler.clients.bitbucket.base import BitbucketRunnerStatuses
from autoscaler.core.helpers import success
from autoscaler.core.logger import logger


MAX_RUNNERS_COUNT_PER_REPOSITORY = 100
MAX_RUNNERS_COUNT_PER_WORKSPACE = 100
SCALE_UP_MULTIPLIER = 1.5
SCALE_DOWN_MULTIPLIER = 0.5


class PctRunnersIdleScaler:

    def __init__(self, runner_data, runner_constants, kubernetes_service):
        self.runner_data = runner_data
        self.runner_consants = runner_constants
        self.kubernetes_service = kubernetes_service

    def validate(self):
        return self.kubernetes_service.check_kubernetes_namespace(self.runner_data['namespace'])

    def get_runners(self):
        # TODO optimize GET requests with filters by labels
        return runner.get_bitbucket_runners(self.runner_data['workspace'], self.runner_data['repository'])

    def create_runner(self, count_number):
        runners = self.get_runners()

        if runners:
            runners_stats = dict(Counter([r['state'].get('status') for r in runners]))
            logger.debug(runners_stats)

        # check runners count before add new runner
        if len(runners) >= MAX_RUNNERS_COUNT_PER_REPOSITORY:
            msg = f"Max Runners count limit reached {len(runners)} per workspace {self.runner_data['workspace']['name']}"
            if self.runner_data['repository']:
                msg = f"{msg} repository: {self.runner_data['repository']['name']}"

            logger.warning(msg)
            logger.warning(
                "No new runners will be created! Check your runners. Check you runner's config file.")

            return

        logger.info(f"Runner #{count_number + 1} for namespace: {self.runner_data['namespace']} setup...")

        data = runner.create_bitbucket_runner(
            workspace=self.runner_data['workspace'],
            repository=self.runner_data['repository'],
            name=self.runner_data.get('name'),
            labels=self.runner_data['labels'],
        )

        data['runnerNamespace'] = self.runner_data['namespace']
        self.kubernetes_service.setup_job(data)

        success(
            f"Successfully setup runner UUID {data['runnerUuid']} "
            f"on workspace {self.runner_data['workspace']['name']}\n",
            do_exit=False
        )

        sleep(self.runner_consants.default_sleep_time_runner_setup)

    def delete_runners(self, runners_idle):
        # delete only idle runners
        if len(runners_idle) < 1:
            logger.warning("Nothing to delete... All runners are BUSY (running jobs).")
            return

        # delete only old runners
        runners_uuid_to_delete = [
            r['uuid'].strip('{}') for r in runners_idle if du_parser.isoparse(r['created_on']) + timedelta(
                seconds=self.runner_consants.runner_cool_down_period) < datetime.now(timezone.utc)
        ]

        if runners_uuid_to_delete:
            logger.warning(
                f"Runners count {len(runners_uuid_to_delete)} with the next UUID will be deleted:"
                f" {runners_uuid_to_delete}"
            )
        else:
            logger.warning(
                f"Nothing to delete... "
                f"All runners are created less than coolDownPeriod: "
                f"{self.runner_consants.runner_cool_down_period} sec ago."
            )

        for runner_uuid in runners_uuid_to_delete:
            runner.delete_bitbucket_runner(
                workspace=self.runner_data['workspace'],
                repository=self.runner_data['repository'],
                runner_uuid=runner_uuid
            )

            self.kubernetes_service.delete_job(runner_uuid, self.runner_data['namespace'])

            success(
                f"Successfully deleted runner UUID {runner_uuid} "
                f"on workspace {self.runner_data['workspace']['name']}\n",
                do_exit=False
            )

            sleep(self.runner_consants.default_sleep_time_runner_delete)

    def run(self):
        runners = self.get_runners()

        msg = f"Found {len(runners)} runners on workspace {self.runner_data['workspace']['name']}"
        if self.runner_data['repository']:
            msg = f"{msg} repository: {self.runner_data['repository']['name']}"

        logger.info(msg)

        if runners:
            runners_stats = dict(Counter([r['state'].get('status') for r in runners]))
            logger.info(runners_stats)

        if os.getenv('DEBUG') == 'true':
            pprint(runners)

        online_runners = [
            r for r in runners if
            set(r['labels']) == self.runner_data['labels'] and r['state']['status'] == BitbucketRunnerStatuses.online.value
        ]

        logger.info(f"Found ONLINE runners with labels {self.runner_data['labels']}: {len(online_runners)}")
        logger.debug(online_runners)

        runners_idle = [r for r in online_runners if r['state'].get('step') is None]
        runners_busy = [r for r in online_runners if 'step' in r['state']]

        logger.info(f"Found IDLE runners with labels {self.runner_data['labels']}: {len(runners_idle)}")
        if os.getenv('DEBUG') == 'true':
            pprint(runners_idle)

        runners_scale_treshold = len(runners_busy) / len(online_runners) if online_runners else 0
        logger.info(f'Current runners threshold: {round(runners_scale_treshold, 2)}')

        msg_autoscaler = (
            f"Runners Autoscaler. "
            f"min: {self.runner_data['parameters']['min']}, "
            f"max: {self.runner_data['parameters']['max']}, "
            f"current: {len(online_runners)}"
        )

        if not online_runners and self.runner_data['parameters']['min'] > 0:
            # create new runners from 0
            count_runners_to_create = self.runner_data['parameters']['min']

            msg_autoscaler = (
                f"{msg_autoscaler}, "
                f"desired: {count_runners_to_create}. "
                f"Changing the desired capacity "
                f"from {len(online_runners)} to {count_runners_to_create}.\n"
            )
            logger.info(msg_autoscaler)

            for i in range(count_runners_to_create):
                self.create_runner(i)

        # TODO add max_runners per repo or max_runners per workspace
        elif (runners_scale_treshold > float(self.runner_data['parameters']['scaleUpThreshold']) or len(online_runners) < self.runner_data['parameters']['min']) \
                and len(online_runners) <= self.runner_data['parameters']['max'] \
                and len(runners) <= MAX_RUNNERS_COUNT_PER_REPOSITORY:

            # TODO validate scaleDownFactor > 1
            desired_runners_count = math.ceil(
                len(online_runners) * self.runner_data['parameters'].get('scaleUpMultiplier', SCALE_UP_MULTIPLIER)
            )
            if desired_runners_count <= self.runner_data['parameters']['max']:
                count_runners_to_create = desired_runners_count - len(online_runners)
            else:
                count_runners_to_create = self.runner_data['parameters']['max'] - len(online_runners)
                desired_runners_count = self.runner_data['parameters']['max']

            if count_runners_to_create == 0:
                logger.info(f"Max runners count: {self.runner_data['parameters']['max']} reached.")
                return

            msg_autoscaler = (
                f"{msg_autoscaler}, "
                f"desired: {desired_runners_count}. "
                f"Changing the desired capacity "
                f"from {len(online_runners)} to {desired_runners_count}.\n"
            )
            logger.info(msg_autoscaler)

            for i in range(count_runners_to_create):
                self.create_runner(i)

        elif runners_scale_treshold < float(self.runner_data['parameters']['scaleDownThreshold']) and \
                len(runners_idle) > self.runner_data['parameters']['min']:

            # TODO validate 0 < scaleDownFactor < 1
            desired_runners_count = math.floor(
                len(runners_idle) * self.runner_data['parameters'].get('scaleDownMultiplier', SCALE_DOWN_MULTIPLIER)
            )

            if desired_runners_count > self.runner_data['parameters']['min']:
                count_runners_to_delete = len(runners_idle) - desired_runners_count
            else:
                count_runners_to_delete = len(runners_idle) - self.runner_data['parameters']['min']
                desired_runners_count = self.runner_data['parameters']['min']

            runners_idle_to_delete = runners_idle[:count_runners_to_delete]

            msg_autoscaler = (
                f"{msg_autoscaler}, "
                f"idle: {len(runners_idle)}, "
                f"desired: {desired_runners_count}. "
                f"Changing the desired capacity "
                f"from {len(runners_idle)} to {desired_runners_count}.\n"
            )
            logger.info(msg_autoscaler)

            self.delete_runners(runners_idle_to_delete)

        else:
            # show message to user that ok
            logger.info(msg_autoscaler)
            logger.warning("Nothing to do...\n")
