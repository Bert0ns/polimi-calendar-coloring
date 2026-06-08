import os
import json
import hashlib
from abc import ABC, abstractmethod


class Colors:
    OKCYAN = "\033[96m"
    WARNING = "\033[93m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


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


class ExamColoringStrategy(EventColoringStrategy):
    """
    Strategy specifically for coloring Polimi exams.
    """

    COLOR_GREY = "8"
    COLOR_RED = "11"

    def __init__(self, interactive=False):
        self.interactive = interactive
        self.exam_decision_cache = {}
        self.subscribed_titles = set()

    def determine_color(self, event):
        title = event.get("summary", "")
        description = event.get("description", "")

        if not title.startswith("Esame: "):
            return None

        if self.interactive:
            start_info = event.get("start", {})
            date_str = start_info.get(
                "dateTime", start_info.get("date", "Unknown Date")
            )
            if "T" in date_str:
                date_str = date_str.split("T")[0]

            cache_key = f"{title} ({date_str})"

            if cache_key in self.exam_decision_cache:
                return self.exam_decision_cache[cache_key]

            if title in self.subscribed_titles:
                print(
                    f"{Colors.WARNING} ↳ Auto-declining '{title}' on {date_str} (already subscribed to another date){Colors.ENDC}"
                )
                self.exam_decision_cache[cache_key] = self.COLOR_GREY
                return self.COLOR_GREY

            suggestion_str = ""
            default_ans = None
            if description.startswith("Non iscritto"):
                suggestion_str = (
                    f" [{Colors.BOLD}y{Colors.ENDC}/{Colors.BOLD}N{Colors.ENDC}]"
                )
                default_ans = "n"
            elif description.startswith("Iscritto"):
                suggestion_str = (
                    f" [{Colors.BOLD}Y{Colors.ENDC}/{Colors.BOLD}n{Colors.ENDC}]"
                )
                default_ans = "y"
            else:
                suggestion_str = (
                    f" [{Colors.BOLD}y{Colors.ENDC}/{Colors.BOLD}n{Colors.ENDC}]"
                )

            while True:
                prompt_msg = f"{Colors.OKCYAN}❓ Subscribed to '{title}' on {date_str}?{Colors.ENDC}{suggestion_str}: "
                ans = input(prompt_msg).strip().lower()

                if ans == "" and default_ans:
                    ans = default_ans

                if ans in ["y", "yes"]:
                    self.exam_decision_cache[cache_key] = self.COLOR_RED
                    self.subscribed_titles.add(title)
                    break
                elif ans in ["n", "no"]:
                    self.exam_decision_cache[cache_key] = self.COLOR_GREY
                    break
                else:
                    print(
                        f"{Colors.WARNING} ↳ Please answer 'y' or 'n' (or press Enter for suggestion).{Colors.ENDC}"
                    )
            return self.exam_decision_cache[cache_key]
        else:
            if description.startswith("Non iscritto"):
                return self.COLOR_GREY
            elif description.startswith("Iscritto"):
                return self.COLOR_RED
        return None


class LectureColoringStrategy(EventColoringStrategy):
    """
    Strategy specifically for coloring Polimi lectures.
    """

    AVAILABLE_LECTURE_COLORS = ["1", "2", "3", "4", "5", "6", "7", "9", "10"]

    def __init__(self, interactive=False):
        self.interactive = interactive
        self.course_colors_file = "course_colors.json"

        # If interactive, we force the user to pick colors from scratch
        if self.interactive:
            self.course_colors = {}
        else:
            self.course_colors = self._load_course_colors()

    def _load_course_colors(self):
        if os.path.exists(self.course_colors_file):
            try:
                with open(self.course_colors_file, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(
                    f"{Colors.WARNING}⚠ Warning: '{self.course_colors_file}' is corrupted. Starting fresh.{Colors.ENDC}"
                )
                return {}
        return {}

    def _save_course_colors(self):
        with open(self.course_colors_file, "w") as f:
            json.dump(self.course_colors, f, indent=4)

    def _get_deterministic_color(self, course_name):
        used_colors = set(self.course_colors.values())
        unused_colors = [
            c for c in self.AVAILABLE_LECTURE_COLORS if c not in used_colors
        ]

        # If we have unused colors, pick deterministically from them to avoid duplicates.
        # If all 9 colors are used, fall back to the full list (duplicates unavoidable).
        pool = unused_colors if unused_colors else self.AVAILABLE_LECTURE_COLORS

        h = int(hashlib.md5(course_name.encode("utf-8")).hexdigest(), 16)
        return pool[h % len(pool)]

    def determine_color(self, event):
        title = event.get("summary", "")

        if not title.startswith("Lezione: Didattica - "):
            return None

        course_name = title.replace("Lezione: Didattica - ", "").strip()

        if course_name not in self.course_colors:
            if self.interactive:
                print(
                    f"\n{Colors.OKCYAN}🎨 New Course Detected: {Colors.BOLD}'{course_name}'{Colors.ENDC}"
                )
                print("Available Google Calendar Colors:")
                print("  1: Lavender     4: Flamingo     7: Peacock     10: Basil")
                print("  2: Sage         5: Banana       9: Blueberry")
                print("  3: Grape        6: Tangerine")

                while True:
                    prompt_msg = f"{Colors.OKCYAN}❓ Pick a color ID for ALL lectures of this course (1-10, except 8): {Colors.ENDC}"
                    ans = input(prompt_msg).strip()
                    if ans in self.AVAILABLE_LECTURE_COLORS:
                        self.course_colors[course_name] = ans
                        self._save_course_colors()
                        break
                    else:
                        print(
                            f"{Colors.WARNING} ↳ Invalid choice. Please pick from {self.AVAILABLE_LECTURE_COLORS}.{Colors.ENDC}"
                        )
            else:
                self.course_colors[course_name] = self._get_deterministic_color(
                    course_name
                )
                self._save_course_colors()

        return self.course_colors[course_name]
