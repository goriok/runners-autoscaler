import os
import json
import argparse

import runner
from apis.kubernetes.base import KubernetesSpecFileAPIService
from logger import logger
from manual.count_scaler import BitbucketRunnerCountScaler
from helpers import required, enable_debug, fail, string_to_base64string
from constants import DEFAULT_RUNNER_KUBERNETES_NAMESPACE

DEFAULT_LABELS = {'self.hosted', 'linux'}
MIN_RUNNERS_COUNT = 0
MAX_RUNNERS_COUNT = 100


def main():
    enable_debug()
    # required environment variables BITBUCKET_USERNAME and BITBUCKET_APP_PASSWORD
    bitbucket_username = required('BITBUCKET_USERNAME')
    bitbucket_app_password = required('BITBUCKET_APP_PASSWORD')
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
        logger.info(f"Working on runners data: {runner_data}")

        runner.check_kubernetes_namespace(runner_data['namespace'])

        count_scaler = BitbucketRunnerCountScaler(runner_data)
        count_scaler.run()

    # handle autoscaling workflow
    # TODO allow multiple. Now autoscaling limit 1
    if autoscale_runners:
        # TODO build Docker and pass config
        # TODO add validator for autoscaler parameters

        runner.check_kubernetes_namespace()
        # feed controller spec file with BITBUCKET_USERNAME and BITBUCKET_APP_PASSWORD
        controller_data = {
            'bitbucketClientUsername': bitbucket_username,
            'bitbucketClientSecret_base64': string_to_base64string(bitbucket_app_password),
            'autoscalerConfig': json.dumps(runners_data, default=lambda x: list(x) if isinstance(x, set) else str(x))
        }
        controller_template_filename = "controller-spec.yml.template"

        kube_spec_file_api = KubernetesSpecFileAPIService()
        template = kube_spec_file_api.generate_kube_spec_file(controller_data, controller_template_filename)
        with open("controller-spec.yml", "w") as f:
            f.write(template)

        # TODO Think about how to get rid of Can't update Jobs, field is immutable
        result = kube_spec_file_api.apply_kubernetes_spec_file(
            "controller-spec.yml",
            namespace=DEFAULT_RUNNER_KUBERNETES_NAMESPACE
        )
        logger.info(result)


if __name__ == '__main__':
    main()
