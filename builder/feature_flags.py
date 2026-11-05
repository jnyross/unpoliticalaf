"""Build-time feature flags for optional enhancements to the static site.

Set UNPOLITICAL_FEATURE_FLAGS to a JSON object of boolean overrides. Configure
it separately for local builds and each deployment environment; visitors cannot
override flags. New features are off unless explicitly enabled in the registry.
"""
import json
import os
from dataclasses import dataclass
from functools import lru_cache
from types import MappingProxyType

ENV_VAR = "UNPOLITICAL_FEATURE_FLAGS"


@dataclass(frozen=True)
class FeatureFlag:
    description: str
    default: bool = False


# Already-shipped enhancements retain their current behaviour by default.
FLAGS = MappingProxyType({
    "chart_interactions": FeatureFlag("Tap, hover and keyboard chart readouts", default=True),
    "sticky_navigation": FeatureFlag("Keep the main navigation visible while scrolling", default=True),
})


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"{ENV_VAR} contains a duplicate feature flag")
        result[key] = value
    return result


@lru_cache(maxsize=32)
def _resolve(raw):
    try:
        overrides = json.loads(raw, object_pairs_hook=_unique_pairs)
    except json.JSONDecodeError:
        raise ValueError(f"{ENV_VAR} must be a JSON object of booleans") from None
    if not isinstance(overrides, dict):
        raise ValueError(f"{ENV_VAR} must be a JSON object of booleans")
    if overrides.keys() - FLAGS.keys():
        raise ValueError(f"{ENV_VAR} contains an unknown feature flag; see builder/feature_flags.py")
    if any(type(value) is not bool for value in overrides.values()):
        raise ValueError(f"{ENV_VAR} values must be JSON true or false, not strings or numbers")
    return MappingProxyType({name: overrides.get(name, flag.default) for name, flag in FLAGS.items()})


def resolve(environ=None):
    """Return immutable effective flags, rejecting invalid config rather than shipping it.

    The cache is keyed by configuration, not process lifetime, so successive builds
    with different environments do not accidentally reuse a previous rollout.
    """
    environ = os.environ if environ is None else environ
    return _resolve(environ.get(ENV_VAR, "{}"))


def enabled(name):
    """Check a registered flag; misspelled names raise KeyError."""
    return resolve()[name]
