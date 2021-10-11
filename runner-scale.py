import os
import argparse
from pprint import pprint
from time import sleep

from runner import create_runner, setup_job, create_kube_spec_file, validate_kubernetes, get_runners, delete_runner, \
    delete_job, delete_kube_spec_file
from constants import DEFAULT_SLEEP_TIME_RUNNER_SETUP
from helpers import success, required, enable_debug
from logger import logger


DEFAULT_LABELS = ['self.hosted', 'linux']


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
    parser.add_argument("--runners-count", type=int, default=1, help="Count of runners to setup")
    args = parser.parse_args()

    logger.info(args)

    validate_kubernetes()

    labels = []
    labels.extend(DEFAULT_LABELS)
    labels.extend(args.labels)
    labels = list(set(labels))

    # TODO add repository runners
    runners = get_runners(args.workspace, args.repository)

    msg = f"Found {len(runners)} runners on workspace {args.workspace}."
    if args.repository:
        msg = f"{msg} repository {args.repository}"
    logger.info(msg)

    if os.getenv('DEBUG') == 'true':
        pprint(runners)

    online_runners = [r for r in runners if set(r['labels']) == set(labels) and r['state']['status'] == 'ONLINE']

    logger.info(f"Found ONLINE runners with labels {labels}: {len(online_runners)}")
    logger.debug(online_runners)

    runners_idle = [r for r in online_runners if r['state'].get('step') is None]

    logger.warning(f"Found IDLE runners with labels {labels}: {len(runners_idle)}")
    logger.debug(runners_idle)

    if args.runners_count > len(online_runners):
        # create new runners
        logger.warning(f"Starting setup {args.runners_count - len(online_runners)} new runners...")

        count_runners_to_create = args.runners_count - len(online_runners)

        for i in range(count_runners_to_create):
            logger.warning(f"Runner #{i+1} setup...")
            runner_data = create_runner(
                workspace=args.workspace,
                repository=None,
                name=args.name,
                labels=list(labels),
            )

            runner_spec_filename = create_kube_spec_file(runner_data)
            setup_job(runner_spec_filename)

            success(
                f"Successfully setup runner UUID {runner_data['runnerUuid']} on workspace {args.workspace}",
                do_exit=False
            )

            sleep(DEFAULT_SLEEP_TIME_RUNNER_SETUP)

    elif args.runners_count < len(online_runners):
        # delete only idle runners
        # TODO
        count_runners_to_delete = len(runners_idle) - args.runners_count
        runners_to_delete = [r['uuid'] for r in runners_idle][:count_runners_to_delete]

        logger.warning(f"Runners count {len(runners_to_delete)} with the next UUID will be deleted: {runners_to_delete}")

        for runner_uuid in runners_to_delete:
            delete_runner(args.workspace, runner_uuid=runner_uuid)
            delete_job(runner_uuid.strip('{}'))
            delete_kube_spec_file(runner_uuid.strip('{}'))

            success(
                f"Successfully deleted runner UUID {runner_uuid} on workspace {args.workspace}",
                do_exit=False
            )
    else:
        # show message to user that ok
        logger.warning("Nothing to do...")


if __name__ == '__main__':
    main()
