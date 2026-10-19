"""Replaceable JSON and in-memory storage implementations."""

import json
from abc import ABC, abstractmethod
from copy import deepcopy
from pathlib import Path
from typing import Any


class FestivalStorage(ABC):
    """Persistence interface consumed by the festival domain."""

    @abstractmethod
    def load(self) -> dict[str, Any]:
        """Load the source document."""

    @abstractmethod
    def save(self, data: dict[str, Any]) -> None:
        """Persist the source document."""


class JsonStorage(FestivalStorage):
    """Read and write festival documents as UTF-8 JSON."""

    def __init__(self, path: Path, initial_path: Path | None = None) -> None:
        self.path = path
        self.initial_path = initial_path

    def load(self) -> dict[str, Any]:
        source = self.path
        if not source.exists() and self.initial_path is not None:
            source = self.initial_path
        try:
            with source.open(encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError:
            raise ValueError(f"Data file '{source.name}' was not found.") from None
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Data file '{source.name}' is damaged (line {error.lineno})."
            ) from None
        if not isinstance(data, dict):
            raise ValueError(f"Data file '{source.name}' must contain a JSON object.")
        return data

    def save(self, data: dict[str, Any]) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
                file.write("\n")
        except OSError as error:
            raise ValueError(
                f"Could not save '{self.path.name}': {error.strerror}."
            ) from None


class MemoryStorage(FestivalStorage):
    """Deep-copying in-memory storage for isolated tests."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = deepcopy(data)

    def load(self) -> dict[str, Any]:
        return deepcopy(self._data)

    def save(self, data: dict[str, Any]) -> None:
        self._data = deepcopy(data)
