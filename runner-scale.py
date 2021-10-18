import os
import argparse
from time import sleep
from pprint import pprint

import runner
from logger import logger
from helpers import success, required, enable_debug, fail
from apis.bitbucket.base import BitbucketRunnerStatuses
from constants import (DEFAULT_SLEEP_TIME_RUNNER_SETUP, DEFAULT_SLEEP_TIME_RUNNER_DELETE,
                       DEFAULT_RUNNER_KUBERNETES_NAMESPACE)

DEFAULT_LABELS = {'self.hosted', 'linux'}
MIN_RUNNERS_COUNT = 0
MAX_RUNNERS_COUNT = 100


def main():
    enable_debug()
    # required environment variables BITBUCKET_USERNAME and BITBUCKET_APP_PASSWORD
    required('BITBUCKET_USERNAME')
    required('BITBUCKET_APP_PASSWORD')
    runner.validate_kubernetes()

    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", help="Workspace of the runner")
    # TODO repository runner
    parser.add_argument("--repository", help="Repository of the runner")
    parser.add_argument("--name", help="Name of the runner")
    parser.add_argument("--labels", nargs="+", help="List of labels used for the runner")
    parser.add_argument("--runners-count", type=int, default=1, choices=range(MIN_RUNNERS_COUNT, MAX_RUNNERS_COUNT + 1),
                        help="Count of runners to setup. ")
    parser.add_argument("--namespace", default=DEFAULT_RUNNER_KUBERNETES_NAMESPACE,
                        help=f"Kubernetes namespace for runners. Default: {DEFAULT_RUNNER_KUBERNETES_NAMESPACE}")
    parser.add_argument("--config", help="Path to config file with Runners strategies")
    args = parser.parse_args()

    runners_data = []  # list of runners to handle

    # TODO read runners parameter from config file
    if args.config:
        config_file_path = args.config

        logger.warning(
            f"Config file provided {config_file_path}. "
            f"Other command line parameters will be ignored. "
            f"Starting setup with parameters from the config file..."
        )

        if not os.path.exists(config_file_path):
            fail(f'Passed runners configuration file {config_file_path} does not exist.')

        runners_data = runner.read_from_config(config_file_path)
    else:
        runners_data = [vars(args)]

    for runner_data in runners_data:
        logger.info(f"Working on runners: {runner_data}")
        # TODO validate args
        namespace = runner_data.get('namespace', DEFAULT_RUNNER_KUBERNETES_NAMESPACE)

        runner.check_kubernetes_namespace(namespace)

        labels = set()
        labels.update(DEFAULT_LABELS)
        labels.update(set(runner_data.get('labels')))

        # TODO add repository runners
        runners = runner.get_bitbucket_runners(runner_data.get('workspace'), runner_data.get('repository'))

        msg = f"Found {len(runners)} runners on workspace {runner_data.get('workspace')}."
        if runner_data.get('repository'):
            msg = f"{msg} repository {runner_data.get('repository')}"
        logger.info(msg)

        if os.getenv('DEBUG') == 'true':
            pprint(runners)

        online_runners = [
            r for r in runners if
            set(r['labels']) == labels and r['state']['status'] == BitbucketRunnerStatuses.online.value
        ]

        logger.info(f"Found ONLINE runners with labels {labels}: {len(online_runners)}")
        logger.debug(online_runners)

        runners_idle = [r for r in online_runners if r['state'].get('step') is None]

        logger.warning(f"Found IDLE runners with labels {labels}: {len(runners_idle)}")
        if os.getenv('DEBUG') == 'true':
            pprint(runners_idle)

        if runner_data.get('runners_count') > len(online_runners):
            # create new runners
            logger.warning(f"Starting to setup {runner_data.get('runners_count') - len(online_runners)} new runners...")

            count_runners_to_create = runner_data.get('runners_count') - len(online_runners)

            for i in range(count_runners_to_create):
                logger.warning(f"Runner #{i + 1} for namespace: {namespace} setup...")
                data = runner.create_bitbucket_runner(
                    workspace=runner_data.get('workspace'),
                    repository=runner_data.get('repository'),
                    name=runner_data.get('name'),
                    labels=labels,
                )

                data['runnerNamespace'] = namespace
                runner.setup_job(data)

                success(
                    f"Successfully setup runner UUID {data['runnerUuid']} "
                    f"on workspace {runner_data.get('workspace')}\n",
                    do_exit=False
                )

                sleep(DEFAULT_SLEEP_TIME_RUNNER_SETUP)

        elif runner_data.get('runners_count') < len(online_runners):
            # delete only idle runners
            if len(runners_idle) < 1:
                logger.warning("Nothing to delete... All runners are BUSY (running jobs).")
                continue

            if len(runners_idle) > runner_data.get('runners_count'):
                count_runners_to_delete = len(runners_idle) - runner_data.get('runners_count')
            else:
                count_runners_to_delete = len(runners_idle)

            runners_uuid_to_delete = [r['uuid'].strip('{}') for r in runners_idle][:count_runners_to_delete]

            logger.warning(f"Runners count {len(runners_uuid_to_delete)} with the next UUID will be deleted:"
                           f" {runners_uuid_to_delete}")

            for runner_uuid in runners_uuid_to_delete:
                runner.delete_bitbucket_runner(runner_data.get('workspace'), runner_uuid=runner_uuid)
                runner.delete_job(runner_uuid)

                success(
                    f"Successfully deleted runner UUID {runner_uuid} "
                    f"on workspace {runner_data.get('workspace')}\n",
                    do_exit=False
                )
                sleep(DEFAULT_SLEEP_TIME_RUNNER_DELETE)
        else:
            # show message to user that ok
            logger.warning("Nothing to do...\n")


if __name__ == '__main__':
    main()
