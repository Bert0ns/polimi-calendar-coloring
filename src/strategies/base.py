import os
import json
from abc import ABC, abstractmethod
from colors import Colors


class EventColoringStrategy(ABC):
    """Abstract base class defining the contract for coloring strategies."""

    @abstractmethod
    def determine_color(self, event):
        """
        Returns the color ID for the event, or None if no change is needed.
        """
        pass


class CompositeColoringStrategy(EventColoringStrategy):
    """
    Evaluates multiple coloring strategies in order.
    Returns the first color determined by a strategy.
    """

    def __init__(self, strategies):
        self.strategies = strategies

    def determine_color(self, event):
        for strategy in self.strategies:
            color = strategy.determine_color(event)
            if color is not None:
                return color
        return None


class PersistentColoringStrategy(EventColoringStrategy):
    """Base class for strategies that persist state to JSON files."""

    def __init__(self, state_file, interactive=False):
        self.state_file = state_file
        self.interactive = interactive

        if self.interactive:
            self.state = {}
        else:
            self.state = self._load_state()

    def _load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(
                    f"{Colors.WARNING}⚠ Warning: '{self.state_file}' is corrupted. Starting fresh.{Colors.ENDC}"
                )
                return {}
        return {}

    def _save_state(self):
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=4)
