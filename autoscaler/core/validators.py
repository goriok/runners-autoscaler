import os
from abc import ABC
from typing import Any, Optional, List, Dict, Literal

from pydantic import conlist, conset, root_validator, validator, Extra
from pydantic_yaml import YamlModel

import autoscaler.core.constants as constants
from autoscaler.core.helpers import fail
from autoscaler.core.help_classes import Strategies
from autoscaler.services.bitbucket import BitbucketService
from autoscaler.utils.validation import validate_label_key, validate_label_value


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


class GroupMeta(YamlModel):
    workspace: str
    name: str
    namespace: str
    strategy: str
    repository: Optional[str] = None

    class Strategy:
        supported_strategies = (Strategies.PCT_RUNNER_IDLE.value,)

    @validator('strategy')
    @classmethod
    def strategy_supported(cls, strategy, values):
        if strategy not in GroupMeta.Strategy.supported_strategies:
            raise ValueError(f'{values["name"]}: strategy {strategy} not supported.')
        return strategy

    @validator('namespace')
    @classmethod
    def namespace_reserved(cls, namespace, values):
        if namespace == constants.DEFAULT_RUNNER_KUBERNETES_NAMESPACE:
            raise ValueError(f'{values["name"]}: namespace name `{constants.DEFAULT_RUNNER_KUBERNETES_NAMESPACE}` is reserved and not available.')
        return namespace

    @root_validator
    @classmethod
    def update_to_uuid(cls, values):
        workspace_name, repository_name = values.get('workspace'), values.get('repository')

        workspace_data, repository_data = BitbucketService.get_bitbucket_workspace_repository_uuids(
            workspace_name=workspace_name,
            repository_name=repository_name
        )

        # Update workspace data
        values['workspace'] = NameUUIDData.parse_obj(workspace_data)
        if repository_name is not None:
            # Update repository data
            values['repository'] = NameUUIDData.parse_obj(repository_data)

        return values


class GroupData(GroupMeta):
    labels: conset(str, min_items=1)
    parameters: Any

    @validator('labels')
    @classmethod
    def update_labels(cls, labels):
        # Update labels
        labels.update(set(constants.DEFAULT_LABELS))
        return labels

    @root_validator
    @classmethod
    def update_parameters(cls, values):
        strategy, parameters = values.get('strategy'), values.get('parameters')

        # Update parameters for different strategies
        if strategy == Strategies.PCT_RUNNER_IDLE.value:
            values['parameters'] = PctRunnersIdleParameters.parse_obj(parameters)

        return values


class RunnerData(YamlModel):
    constants: Constants = Constants.parse_obj(dict())
    groups: conlist(GroupData, min_items=1)

    @validator("groups")
    def check_groups_labels_unique(cls, values):
        group_labels_set = set()
        for value in values:
            if value.labels in group_labels_set:
                raise ValueError(
                    f"Every group should have unique set of labels."
                    f" Duplicate labels item found: {value.labels}")
            else:
                group_labels_set.add(frozenset(value.labels))

        return values


class RunnerCleanerData(YamlModel):
    constants: Constants = Constants.parse_obj(dict())
    groups: conlist(GroupMeta, min_items=1)


# labels validators
class Item(YamlModel, ABC):
    _types: Dict[str, type] = {}

    # register automatically all the submodels in `_types`.
    def __init_subclass__(cls, type: Optional[str] = None):
        cls._types[type or cls.__name__.lower()] = cls

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value: Dict[str, Any]) -> 'Item':
        item_kind = value['kind']
        # init with right Item submodel
        return cls._types[item_kind](**value)


class SecretMetadataLabels(YamlModel):
    account_uuid: str
    runner_uuid: str
    runner_namespace: str

    class Config:
        extra = Extra.allow

    @root_validator
    @classmethod
    def validate_labels(cls, values):
        errors = []
        for k, v in values.items():
            errors.extend(validate_label_key(k))
            errors.extend(validate_label_value(v))
        if errors:
            raise ValueError(f"Label errors: {cls.__name__} {errors}")
        return values


class SecretMetadata(YamlModel):
    name: str
    labels: SecretMetadataLabels


class SecretData(Item, type="Secret"):
    metadata: SecretMetadata
    kind: Literal["Secret"]


# job
class JobSpecTemplateMetadataLabels(YamlModel):
    account_uuid: str
    runner_uuid: str
    runner_namespace: str

    class Config:
        extra = Extra.allow

    @root_validator
    @classmethod
    def validate_labels(cls, values):
        errors = []
        for k, v in values.items():
            errors.extend(validate_label_key(k))
            errors.extend(validate_label_value(v))
        if errors:
            raise ValueError(f"Label errors: {cls.__name__} {errors}")
        return values


class JobSpecTemplateMetadata(YamlModel):
    labels: JobSpecTemplateMetadataLabels


class JobSpecTemplate(YamlModel):
    metadata: JobSpecTemplateMetadata


class JobSpec(YamlModel):
    template: JobSpecTemplate


class JobData(Item, type="Job"):
    spec: JobSpec
    kind: Literal["Job"]


class JobTemplate(YamlModel):
    items: List[Item]
