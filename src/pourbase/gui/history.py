"""Undo and redo for the settings and display options of the element view."""

from __future__ import annotations

import copy
from typing import Any


class History:
    """Snapshots of ``(settings, display)``; ``record`` adds one when the state differs from the current one."""

    def __init__(self, limit: int = 200) -> None:
        self.limit = limit
        self._states: list[Any] = []
        self._index = -1

    def record(self, state: Any) -> bool:
        if self._index >= 0 and self._states[self._index] == state:
            return False
        del self._states[self._index + 1:]
        self._states.append(copy.deepcopy(state))
        if len(self._states) > self.limit:
            del self._states[0]
        self._index = len(self._states) - 1
        return True

    def can_undo(self) -> bool:
        return self._index > 0

    def can_redo(self) -> bool:
        return self._index < len(self._states) - 1

    def undo(self) -> Any:
        self._index -= 1
        return copy.deepcopy(self._states[self._index])

    def redo(self) -> Any:
        self._index += 1
        return copy.deepcopy(self._states[self._index])
