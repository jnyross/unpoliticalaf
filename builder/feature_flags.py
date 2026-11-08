"""Build-time feature flags for optional enhancements to the static site.

Local builds accept JSON boolean overrides in UNPOLITICAL_FEATURE_FLAGS.
Production builds use only the reviewed config/feature-flags.production.json.
Visitors cannot override flags. New local features default off.
"""

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

ENV_VAR = "UNPOLITICAL_FEATURE_FLAGS"
PRODUCTION_CONFIG = Path(__file__).resolve().parents[1] / "config/feature-flags.production.json"


@dataclass(frozen=True)
class FeatureFlag:
    description: str
    default: bool = False


# Already-shipped enhancements retain their current behaviour by default.
FLAGS = MappingProxyType(
    {
        "chart_interactions": FeatureFlag("Tap, hover and keyboard chart readouts", default=True),
        "sticky_navigation": FeatureFlag(
            "Keep the main navigation visible while scrolling", default=True
        ),
    }
)


def _unique_pairs(pairs, source):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"{source} contains a duplicate feature flag")
        result[key] = value
    return result


def _parse(raw, source=ENV_VAR):
    try:
        overrides = json.loads(raw, object_pairs_hook=lambda pairs: _unique_pairs(pairs, source))
    except json.JSONDecodeError:
        raise ValueError(f"{source} must be a JSON object of booleans") from None
    if not isinstance(overrides, dict):
        raise ValueError(f"{source} must be a JSON object of booleans")
    if overrides.keys() - FLAGS.keys():
        raise ValueError(f"{source} contains an unknown feature flag; see builder/feature_flags.py")
    if any(type(value) is not bool for value in overrides.values()):
        raise ValueError(f"{source} values must be JSON true or false, not strings or numbers")
    return overrides


def snapshot(settings):
    """Copy and validate a complete caller-owned mapping, without reading settings."""
    if not isinstance(settings, Mapping):
        raise ValueError("A flag snapshot must be an object")
    settings = dict(settings)
    if settings.keys() != FLAGS.keys():
        raise ValueError("A flag snapshot must explicitly configure every registered feature flag")
    if any(type(value) is not bool for value in settings.values()):
        raise ValueError("Flag snapshot values must be booleans")
    return MappingProxyType({name: settings[name] for name in sorted(FLAGS)})


def resolve(environ=None):
    """Return immutable effective flags, rejecting invalid config rather than shipping it.

    Resolve per build, never per process, so successive builds cannot reuse an
    earlier environment or registry. Only local overrides may be partial.
    """
    environ = os.environ if environ is None else environ
    overrides = _parse(environ.get(ENV_VAR, "{}"))
    return snapshot({name: overrides.get(name, flag.default) for name, flag in FLAGS.items()})


def production(environ=None):
    """Read the complete, explicit production configuration, never remote state.

    Reject local overrides, including empty ones, so Vercel-only settings cannot
    silently diverge from the rebuild used by make live and live.yml.
    """
    environ = os.environ if environ is None else environ
    if ENV_VAR in environ:
        raise ValueError(
            f"Production builds require unsetting {ENV_VAR}; use {PRODUCTION_CONFIG.name}"
        )
    settings = _parse(PRODUCTION_CONFIG.read_text(encoding="utf-8"), PRODUCTION_CONFIG.name)
    if settings.keys() != FLAGS.keys():
        raise ValueError(
            f"{PRODUCTION_CONFIG.name} must explicitly configure every registered feature flag"
        )
    return snapshot(settings)
