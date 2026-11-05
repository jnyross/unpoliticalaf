"""Build-time feature flags for optional enhancements to the static site.

Local builds accept JSON boolean overrides in UNPOLITICAL_FEATURE_FLAGS.
Production builds use only the reviewed config/feature-flags.production.json.
Visitors cannot override flags. New local features default off.
"""
import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType

ENV_VAR = "UNPOLITICAL_FEATURE_FLAGS"
PRODUCTION_CONFIG = Path(__file__).resolve().parents[1] / "config/feature-flags.production.json"


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


def _parse(raw):
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
    return overrides


@lru_cache(maxsize=32)
def _resolve(raw):
    overrides = _parse(raw)
    return MappingProxyType({name: overrides.get(name, flag.default) for name, flag in FLAGS.items()})


def resolve(environ=None):
    """Return immutable effective flags, rejecting invalid config rather than shipping it.

    The cache is keyed by configuration, not process lifetime, so successive builds
    with different environments do not accidentally reuse a previous rollout.
    """
    environ = os.environ if environ is None else environ
    return _resolve(environ.get(ENV_VAR, "{}"))


def production(environ=None):
    """Read the complete, explicit production configuration, never remote state.

    Reject local overrides, including empty ones, so Vercel-only settings cannot
    silently diverge from the rebuild used by make live and live.yml.
    """
    environ = os.environ if environ is None else environ
    if ENV_VAR in environ:
        raise ValueError(f"Production builds require unsetting {ENV_VAR}; use {PRODUCTION_CONFIG.name}")
    settings = _parse(PRODUCTION_CONFIG.read_text(encoding="utf-8"))
    if settings.keys() != FLAGS.keys():
        raise ValueError(f"{PRODUCTION_CONFIG.name} must explicitly configure every registered feature flag")
    return MappingProxyType(settings)
