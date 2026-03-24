from __future__ import annotations

import ast
from abc import ABC, abstractmethod

from greenlint.diagnostics import Diagnostic


class BaseRule(ABC):
    code: str = ""

    @abstractmethod
    def check(self, tree: ast.AST) -> list[Diagnostic]:
        raise NotImplementedError
