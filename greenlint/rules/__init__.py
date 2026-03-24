from greenlint.rules.eco1_range_len import ECO1Rule
from greenlint.rules.eco2_append_loop import ECO2Rule
from greenlint.rules.eco3_string_concat import ECO3Rule
from greenlint.rules.eco4_membership_list import ECO4Rule
from greenlint.rules.eco5_unused_heavy_import import ECO5Rule
from greenlint.rules.eco6_iterrows import ECO6Rule
from greenlint.rules.eco7_apply_simple_expr import ECO7Rule

ALL_RULES = [
    ECO1Rule(),
    ECO2Rule(),
    ECO3Rule(),
    ECO4Rule(),
    ECO5Rule(),
    ECO6Rule(),
    ECO7Rule(),
]

__all__ = [
    "ALL_RULES",
    "ECO1Rule",
    "ECO2Rule",
    "ECO3Rule",
    "ECO4Rule",
    "ECO5Rule",
    "ECO6Rule",
    "ECO7Rule",
]
