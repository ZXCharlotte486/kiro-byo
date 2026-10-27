"""Dyna Mode plug-in placeholder: discoverable but never executable in 0.2.3."""
from .contracts import BuiltinMode

MODE = BuiltinMode(
    id="dyna", policy_filename="dyna.json",
    type_ids=("flash", "strong", "miracle"),
    default_type="flash", enabled=False,
)
