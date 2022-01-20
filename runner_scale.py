import os
import json
import argparse

import runner
from apis.kubernetes.base import KubernetesSpecFileAPIService, KubernetesBaseAPIService
from logger import logger
from manual.count_scaler import BitbucketRunnerCountScaler
from helpers import required, enable_debug, fail, string_to_base64string
from constants import (DEFAULT_RUNNER_KUBERNETES_NAMESPACE, DEFAULT_SLEEP_TIME_RUNNER_SETUP,
                       DEFAULT_SLEEP_TIME_RUNNER_DELETE, BITBUCKET_RUNNER_API_POLLING_INTERVAL, RUNNER_COOL_DOWN_PERIOD,
                       CONSTANTS_CONFIG_MAP_NAME, AUTOSCALER_CONFIG_MAP_NAME)

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
            fail('Namespace required for runner.')
        elif runner_data['namespace'] == DEFAULT_RUNNER_KUBERNETES_NAMESPACE:
            fail(f'Namespace name `{DEFAULT_RUNNER_KUBERNETES_NAMESPACE}` is reserved and not available.')

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
        # TODO add validator for autoscaler parameters. Should namespaces be unique for each group despite of the
        #  strategy?

        # get a namespace or create a new one.
        # variable is_namespace_created is True if namespace created and False if namespace already present.
        is_namespace_created = runner.check_kubernetes_namespace(namespace=DEFAULT_RUNNER_KUBERNETES_NAMESPACE)
        # feed controller spec file with BITBUCKET_USERNAME and BITBUCKET_APP_PASSWORD and other environment variables.
        controller_data = {
            'bitbucket_client_username': bitbucket_username,
            'constants_config_map_name': CONSTANTS_CONFIG_MAP_NAME,
            'autoscaler_config_map_name': AUTOSCALER_CONFIG_MAP_NAME,
            'bitbucket_client_secret_base64': string_to_base64string(bitbucket_app_password)
        }

        kube_api = KubernetesBaseAPIService()

        autoscaler_data = {
            'autoscaler.config': json.dumps(runners_data['config'],
                                            default=lambda x: list(x) if isinstance(x, set) else str(x))
        }
        kube_api.create_config_map(
            AUTOSCALER_CONFIG_MAP_NAME,
            autoscaler_data,
            namespace=DEFAULT_RUNNER_KUBERNETES_NAMESPACE
        )

        if 'constants' in runners_data:
            # Simple validation. TODO refactor this.
            constants_data = {
                'constants.default_sleep_time_runner_setup': str(runners_data['constants'].get(
                    'default_sleep_time_runner_setup', DEFAULT_SLEEP_TIME_RUNNER_SETUP
                )),
                'constants.default_sleep_time_runner_delete': str(runners_data['constants'].get(
                    'default_sleep_time_runner_delete', DEFAULT_SLEEP_TIME_RUNNER_DELETE
                )),
                'constants.runner_api_polling_interval': str(runners_data['constants'].get(
                    'runner_api_polling_interval', BITBUCKET_RUNNER_API_POLLING_INTERVAL
                )),
                'constants.runner_cool_down_period': str(runners_data['constants'].get(
                    'runner_cool_down_period', RUNNER_COOL_DOWN_PERIOD
                ))
            }

            kube_api.create_config_map(
                CONSTANTS_CONFIG_MAP_NAME,
                constants_data,
                namespace=DEFAULT_RUNNER_KUBERNETES_NAMESPACE
            )

        # TODO Implement deployment reload if namespace already exists.
        # create controller only when a new namespace created
        if is_namespace_created:
            kube_spec_file_api = KubernetesSpecFileAPIService()
            controller_template_filename = "controller-spec.yml.template"
            template = kube_spec_file_api.generate_kube_spec_file(controller_data, controller_template_filename)
            with open("controller-spec.yml", "w") as f:
                f.write(template)

            result = kube_spec_file_api.apply_kubernetes_spec_file(
                "controller-spec.yml",
                namespace=DEFAULT_RUNNER_KUBERNETES_NAMESPACE
            )
            logger.info(result)


if __name__ == '__main__':
    main()
