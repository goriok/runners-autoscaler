"""Module for configuring constants for runner controller."""
from dataclasses import dataclass
from enum import Enum, auto

import autoscaler.core.constants as constants


class SEnum(Enum):
    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other

        return super().__eq__(other)


@dataclass
class Constants:
    default_sleep_time_runner_setup: int = constants.DEFAULT_SLEEP_TIME_RUNNER_SETUP
    default_sleep_time_runner_delete: int = constants.DEFAULT_SLEEP_TIME_RUNNER_DELETE
    runner_api_polling_interval: int = constants.BITBUCKET_RUNNER_API_POLLING_INTERVAL
    runner_cool_down_period: int = constants.RUNNER_COOL_DOWN_PERIOD


class Strategies(Enum):
    PCT_RUNNER_IDLE = 'percentageRunnersIdle'


class BitbucketRunnerStatuses(SEnum):
    UNREGISTERED = auto()
    ONLINE = auto()
    OFFLINE = auto()
    DISABLED = auto()
    ENABLED = auto()
