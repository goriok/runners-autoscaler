"""Module for configuring help classes for runner controller."""
from enum import Enum, auto


class SEnum(Enum):
    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other

        return super().__eq__(other)


class Strategies(Enum):
    PCT_RUNNER_IDLE = 'percentageRunnersIdle'
    PCT_RUNNER_IDLE_BY_PROJECT = 'percentageRunnersIdleByProject'


class BitbucketRunnerStatuses(SEnum):
    UNREGISTERED = auto()
    ONLINE = auto()
    OFFLINE = auto()
    DISABLED = auto()
    ENABLED = auto()
