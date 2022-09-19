from typing import Final

AGENT_TYPE_STRM: Final = "strm"
AGENT_TYPE_BONSAI: Final = "bonsai"
AGENT_TYPE_RANDOM: Final = "random"
AGENT_TYPE_BASESTOCK: Final = "basestock"

DEMAND_DISTRIBUTION_UNIFORM: Final = "uniform"
DEMAND_DISTRIBUTION_NORMAL: Final = "normal"
DEMAND_DISTRIBUTION_PATTERN: Final = (
    "pattern"  # TODO: implement, means 4 rounds of 4 demand, then up to 8.
)
