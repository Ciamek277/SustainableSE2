from greenlint.rules.eco1 import ECO1Rule
from greenlint.rules.eco2 import ECO2Rule
from greenlint.rules.eco3 import ECO3Rule
from greenlint.rules.eco4 import ECO4Rule

ALL_RULES = [
    ECO1Rule(),
    ECO2Rule(),
    ECO3Rule(),
    ECO4Rule(),
]

__all__ = ["ALL_RULES", "ECO1Rule", "ECO2Rule", "ECO3Rule", "ECO4Rule"]
