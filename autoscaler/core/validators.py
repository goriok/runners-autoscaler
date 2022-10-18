import os

import autoscaler.core.constants as constants
from autoscaler.core.helpers import fail
from autoscaler.core.help_classes import Constants, NameUUIDData, Strategies, RunnerMeta, RunnerData
from autoscaler.services.bitbucket import BitbucketService
from autoscaler.strategy.pct_runners_idle import PctRunnersIdleScaler


def validate_config(config_file_path, template_file_path=None):
    if not os.path.exists(config_file_path):
        fail(f'Passed runners configuration file {config_file_path} does not exist.')

    if template_file_path is not None and not os.path.exists(template_file_path):
        fail(f'Passed runners job template file {template_file_path} does not exist.')


def init_constants(runners_data):
    if 'constants' in runners_data:
        return Constants(
            runners_data['constants'].get('default_sleep_time_runner_setup',
                                          constants.DEFAULT_SLEEP_TIME_RUNNER_DELETE),
            runners_data['constants'].get('default_sleep_time_runner_delete',
                                          constants.DEFAULT_SLEEP_TIME_RUNNER_SETUP),
            runners_data['constants'].get('runner_api_polling_interval',
                                          constants.BITBUCKET_RUNNER_API_POLLING_INTERVAL),
            runners_data['constants'].get('runner_cool_down_period', constants.RUNNER_COOL_DOWN_PERIOD)
        )
    else:
        return Constants()


def validate_group_count(group_count):
    if group_count > constants.MAX_GROUPS_COUNT:
        fail(f'Your groups count {group_count} exceeds maximum allowed count of {constants.MAX_GROUPS_COUNT}')


def validate_runner_common_data(runner_data):
    # TODO validate args. Refactor conditional blocks with validator usage.
    # TODO optimize this logic
    if runner_data.get('namespace') is None:
        fail('Namespace required for runner.')
    elif runner_data['namespace'] == constants.DEFAULT_RUNNER_KUBERNETES_NAMESPACE:
        fail(f'Namespace name `{constants.DEFAULT_RUNNER_KUBERNETES_NAMESPACE}` is reserved and not available.')

    if runner_data.get('name') is None:
        fail('Group name required for runner.')

    if runner_data.get('workspace') is None:
        fail('Workspace required for runner.')

    if runner_data.get('repository') is None:
        runner_data['repository'] = None

    if runner_data.get('strategy') is None:
        fail('Strategy required for runner.')


def validate_runner_data(runner_data, only_cleaner=None):
    validate_runner_common_data(runner_data)

    if only_cleaner:
        return

    if runner_data.get('parameters') is None:
        fail('Parameters required for runner.')


def update_runner_data(runner_data, only_cleaner=None):
    workspace_data, repository_data = BitbucketService.get_bitbucket_workspace_repository_uuids(
        workspace_name=runner_data['workspace'],
        repository_name=runner_data['repository']
    )

    workspace = NameUUIDData(
        name=workspace_data['name'],
        uuid=workspace_data['uuid'],
    )

    repository = None
    if repository_data:
        repository = NameUUIDData(
            name=repository_data['name'],
            uuid=repository_data['uuid'],
        )

    if only_cleaner:
        return RunnerMeta(
            workspace=workspace,
            repository=repository,
            name=runner_data['name'],
            namespace=runner_data['namespace'],
            strategy=runner_data['strategy']
        )

    labels = set(constants.DEFAULT_LABELS)
    labels.update(runner_data.get('labels'))

    # Update parameters for different strategies
    parameters = None
    if runner_data['strategy'] == Strategies.PCT_RUNNER_IDLE.value:
        try:
            parameters = PctRunnersIdleScaler.update_parameters(runner_data)
        except KeyError as e:
            fail(f"{runner_data['name']}: parameter is missing {e}")
    else:
        fail(f'{runner_data["name"]}: strategy {runner_data["strategy"]} not supported.')

    return RunnerData(
        workspace=workspace,
        repository=repository,
        name=runner_data['name'],
        labels=labels,
        namespace=runner_data['namespace'],
        strategy=runner_data['strategy'],
        parameters=parameters
    )
