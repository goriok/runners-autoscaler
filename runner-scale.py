import os
import argparse
from time import sleep

import runner
from logger import logger
from count_scaler import BitbucketRunnerCountScaler
from autoscaler import BitbucketRunnerAutoscaler
from helpers import required, enable_debug, fail
from constants import DEFAULT_RUNNER_KUBERNETES_NAMESPACE, BITBUCKET_RUNNER_API_POLLING_INTERVAL

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
    parser.add_argument("--config", default="runner-config.yaml", help="Path to config file with Runners strategies")
    args = parser.parse_args()

    runners_data = []  # list of runners to handle

    # read runners parameter from the config file
    config_file_path = args.config

    logger.info(f"Config file provided {config_file_path}.")

    if not os.path.exists(config_file_path):
        fail(f'Passed runners configuration file {config_file_path} does not exist.')

    runners_data = runner.read_from_config(config_file_path)

    # update runners data with default params
    for runner_data in runners_data['config']:
        # TODO validate args
        # TODO optimize this logic
        if runner_data.get('namespace') is None:
            namespace = runner_data.get('namespace', DEFAULT_RUNNER_KUBERNETES_NAMESPACE)
            runner_data['namespace'] = namespace

        labels = set()
        labels.update(DEFAULT_LABELS)
        labels.update(set(runner_data.get('labels')))
        runner_data['labels'] = labels

    manual_runners = [r for r in runners_data['config'] if r['type'] == 'manual']
    autoscale_runners = [r for r in runners_data['config'] if r['type'] == 'autoscaling']

    # handle manual workflow
    for runner_data in manual_runners:
        logger.info(f"Working on runners: {runner_data}")

        runner.check_kubernetes_namespace(runner_data['namespace'])

        count_scaler = BitbucketRunnerCountScaler(runner_data)
        count_scaler.run()

    # handle autoscaling workflow
    # TODO allow multiple. Now autoscaling limit 1
    for runner_data in autoscale_runners[:1]:
        logger.info(f"Working on runners: {runner_data}")

        runner.check_kubernetes_namespace(runner_data['namespace'])

        # TODO add validator for autoscaler parameters
        # TODO move to k8s pod
        autoscaler = BitbucketRunnerAutoscaler(runner_data)
        while True:
            autoscaler.run()
            logger.warning(f"AUTOSCALER next attempt in {BITBUCKET_RUNNER_API_POLLING_INTERVAL} seconds...\n")
            sleep(BITBUCKET_RUNNER_API_POLLING_INTERVAL)


if __name__ == '__main__':
    main()
