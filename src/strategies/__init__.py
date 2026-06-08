from .base import (
    EventColoringStrategy,
    CompositeColoringStrategy,
    PersistentColoringStrategy,
)
from .exams import ExamColoringStrategy
from .lectures import LectureColoringStrategy

__all__ = [
    "EventColoringStrategy",
    "CompositeColoringStrategy",
    "PersistentColoringStrategy",
    "ExamColoringStrategy",
    "LectureColoringStrategy",
]
