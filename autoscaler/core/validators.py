import os
from typing import Any

from pydantic import conlist, root_validator, validator
from pydantic_yaml import YamlModel

import autoscaler.core.constants as constants
from autoscaler.core.helpers import fail
from autoscaler.core.help_classes import Strategies
from autoscaler.services.bitbucket import BitbucketService


# Temporary until we decide which camelCase or snake-case we should use
def to_camel(string):
    words = string.split('_')
    return f"{words[0]}{''.join(word.capitalize() for word in words[1:])}"


def validate_config(config_file_path, template_file_path=None):
    if not os.path.exists(config_file_path):
        fail(f'Passed runners configuration file {config_file_path} does not exist.')

    if template_file_path is not None and not os.path.exists(template_file_path):
        fail(f'Passed runners job template file {template_file_path} does not exist.')


class Constants(YamlModel):
    default_sleep_time_runner_setup: int = constants.DEFAULT_SLEEP_TIME_RUNNER_SETUP
    default_sleep_time_runner_delete: int = constants.DEFAULT_SLEEP_TIME_RUNNER_DELETE
    runner_api_polling_interval: int = constants.BITBUCKET_RUNNER_API_POLLING_INTERVAL
    runner_cool_down_period: int = constants.RUNNER_COOL_DOWN_PERIOD


class NameUUIDData(YamlModel):
    name: str
    uuid: str


class PctRunnersIdleParameters(YamlModel):
    min: int
    max: int
    scale_up_threshold: float
    scale_down_threshold: float
    scale_up_multiplier: float
    scale_down_multiplier: float

    class Config:
        alias_generator = to_camel


class GroupMeta(YamlModel):
    workspace: NameUUIDData
    name: str
    namespace: str
    strategy: str
    repository: NameUUIDData | None = None

    @root_validator(pre=True)
    @classmethod
    def update_to_uuid(cls, values):
        workspace_name, repository_name = values.get('workspace'), values.get('repository')
        assert workspace_name, 'Workspace required for runner.'

        values['workspace'], values['repository'] = BitbucketService.get_bitbucket_workspace_repository_uuids(
            workspace_name=workspace_name,
            repository_name=repository_name
        )
        return values

    @validator('strategy')
    @classmethod
    def strategy_supported(cls, strategy, values):
        assert strategy in GroupData.Strategy.supported_strategies, f'{values["name"]}: strategy {strategy} not supported.'
        return strategy

    @validator('namespace')
    @classmethod
    def namespace_reserved(cls, namespace, values):
        assert namespace != constants.DEFAULT_RUNNER_KUBERNETES_NAMESPACE, f'{values["name"]}: namespace name `{constants.DEFAULT_RUNNER_KUBERNETES_NAMESPACE}` is reserved and not available.'
        return namespace


class GroupData(GroupMeta):
    labels: set[str]
    parameters: Any

    class Strategy:
        supported_strategies = (Strategies.PCT_RUNNER_IDLE.value,)

    @root_validator
    @classmethod
    def update_group_data(cls, values):
        strategy, parameters = values.get('strategy'), values.get('parameters')
        # Update labels
        values['labels'].update(set(constants.DEFAULT_LABELS))

        # Update parameters for different strategies
        if strategy == Strategies.PCT_RUNNER_IDLE.value:
            values['parameters'] = PctRunnersIdleParameters.parse_obj(parameters)

        return values


class RunnerData(YamlModel):
    constants: Constants = Constants.parse_obj(dict())
    groups: conlist(GroupData, min_items=1)


class RunnerCleanerData(YamlModel):
    constants: Constants = Constants.parse_obj(dict())
    groups: conlist(GroupMeta, min_items=1)
