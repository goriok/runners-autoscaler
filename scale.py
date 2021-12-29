import os
from time import sleep

import runner
from logger import logger
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

    runners_data = []  # list of runners to handle

    # read runners parameter from the config file
    config_file_path = "/runner-config.yaml"

    logger.info(f"Config file provided {config_file_path}.")

    if not os.path.exists(config_file_path):
        fail(f'Passed runners configuration file {config_file_path} does not exist.')

    # TODO feature re-read config file
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

    autoscale_runners = [r for r in runners_data['config'] if r['type'] == 'autoscaling']

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
