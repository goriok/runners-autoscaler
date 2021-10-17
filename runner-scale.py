import os
import argparse
from time import sleep
from pprint import pprint

import runner
from logger import logger
from helpers import success, required, enable_debug
from apis.bitbucket.base import BitbucketRunnerStatuses
from constants import (DEFAULT_SLEEP_TIME_RUNNER_SETUP, DEFAULT_SLEEP_TIME_RUNNER_DELETE,
                       DEFAULT_RUNNER_KUBERNETES_NAMESPACE)


DEFAULT_LABELS = {'self.hosted', 'linux'}


def main():
    enable_debug()
    # required environment variables BITBUCKET_USERNAME and BITBUCKET_APP_PASSWORD
    required('BITBUCKET_USERNAME')
    required('BITBUCKET_APP_PASSWORD')

    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", help="Workspace of the runner")
    # TODO repository runner
    parser.add_argument("--repository", help="Repository of the runner")
    parser.add_argument("--name", help="Name of the runner")
    parser.add_argument("--labels", nargs="+", help="List of labels used for the runner")
    parser.add_argument("--runners-count", type=int, default=1, choices=range(0, 100+1), help="Count of runners to setup. ")
    parser.add_argument("--namespace", default=DEFAULT_RUNNER_KUBERNETES_NAMESPACE,
                        help=f"Kubernetes namespace for runners. Default: {DEFAULT_RUNNER_KUBERNETES_NAMESPACE}")
    args = parser.parse_args()

    logger.info(args)
    # TODO validate args

    runner.validate_kubernetes()

    labels = set()
    labels.update(DEFAULT_LABELS)
    labels.update(set(args.labels))

    # TODO add repository runners
    runners = runner.get_bitbucket_runners(args.workspace, args.repository)

    msg = f"Found {len(runners)} runners on workspace {args.workspace}."
    if args.repository:
        msg = f"{msg} repository {args.repository}"
    logger.info(msg)

    if os.getenv('DEBUG') == 'true':
        pprint(runners)

    online_runners = [r for r in runners if set(r['labels']) == labels and
                      r['state']['status'] == BitbucketRunnerStatuses.online.value]

    logger.info(f"Found ONLINE runners with labels {labels}: {len(online_runners)}")
    logger.debug(online_runners)

    runners_idle = [r for r in online_runners if r['state'].get('step') is None]

    logger.warning(f"Found IDLE runners with labels {labels}: {len(runners_idle)}")
    if os.getenv('DEBUG') == 'true':
        pprint(runners_idle)

    if args.runners_count > len(online_runners):
        # create new runners
        logger.warning(f"Starting to setup {args.runners_count - len(online_runners)} new runners...")

        count_runners_to_create = args.runners_count - len(online_runners)

        for i in range(count_runners_to_create):
            logger.warning(f"Runner #{i+1} setup...")
            runner_data = runner.create_bitbucket_runner(
                workspace=args.workspace,
                repository=args.repository,
                name=args.name,
                labels=labels,
            )

            runner_data['runnerNamespace'] = args.namespace
            runner.setup_job(runner_data)

            success(
                f"Successfully setup runner UUID {runner_data['runnerUuid']} on workspace {args.workspace}",
                do_exit=False
            )

            sleep(DEFAULT_SLEEP_TIME_RUNNER_SETUP)

    elif args.runners_count < len(online_runners):
        # delete only idle runners
        if len(runners_idle) < 1:
            logger.warning("Nothing to delete... All runners are BUSY (running jobs).")
            return

        if len(runners_idle) > args.runners_count:
            count_runners_to_delete = len(runners_idle) - args.runners_count
        else:
            count_runners_to_delete = len(runners_idle)

        runners_uuid_to_delete = [r['uuid'].strip('{}') for r in runners_idle][:count_runners_to_delete]

        logger.warning(f"Runners count {len(runners_uuid_to_delete)} with the next UUID will be deleted:"
                       f" {runners_uuid_to_delete}")

        for runner_uuid in runners_uuid_to_delete:
            runner.delete_bitbucket_runner(args.workspace, runner_uuid=runner_uuid)
            runner.delete_job(runner_uuid)

            success(
                f"Successfully deleted runner UUID {runner_uuid} on workspace {args.workspace}",
                do_exit=False
            )
            sleep(DEFAULT_SLEEP_TIME_RUNNER_DELETE)
    else:
        # show message to user that ok
        logger.warning("Nothing to do...")


if __name__ == '__main__':
    main()
