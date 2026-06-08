import os
import json
import hashlib
from abc import ABC, abstractmethod


class Colors:
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"

    # Google Calendar True Colors (RGB)
    C1_LAVENDER = "\033[38;2;121;134;203m"
    C2_SAGE = "\033[38;2;51;182;121m"
    C3_GRAPE = "\033[38;2;142;36;170m"
    C4_FLAMINGO = "\033[38;2;230;124;115m"
    C5_BANANA = "\033[38;2;246;192;38m"
    C6_TANGERINE = "\033[38;2;245;81;29m"
    C7_PEACOCK = "\033[38;2;3;155;229m"
    C8_GRAPHITE = "\033[38;2;97;97;97m"
    C9_BLUEBERRY = "\033[38;2;63;81;181m"
    C10_BASIL = "\033[38;2;11;128;67m"
    C11_TOMATO = "\033[38;2;214;0;0m"


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
        self.exam_states_file = "exam_states.json"

        if self.interactive:
            self.exam_decision_cache = {}
        else:
            self.exam_decision_cache = self._load_exam_states()

        self.subscribed_titles = self._derive_subscribed_titles()

    def _load_exam_states(self):
        if os.path.exists(self.exam_states_file):
            try:
                with open(self.exam_states_file, "r") as f:
                    data = json.load(f)
                    # Backwards compatibility: upgrade string colors to dict format
                    for k, v in data.items():
                        if isinstance(v, str):
                            data[k] = {"color": v, "subscribed": (v == self.COLOR_RED)}
                    return data
            except json.JSONDecodeError:
                print(
                    f"{Colors.WARNING}⚠ Warning: '{self.exam_states_file}' is corrupted. Starting fresh.{Colors.ENDC}"
                )
                return {}
        return {}

    def _save_exam_states(self):
        with open(self.exam_states_file, "w") as f:
            json.dump(self.exam_decision_cache, f, indent=4)

    def _derive_subscribed_titles(self):
        subscribed = set()
        for key, state in self.exam_decision_cache.items():
            if state.get("subscribed", False):
                title = key.rsplit(" (", 1)[0]
                subscribed.add(title)
        return subscribed

    def determine_color(self, event):
        title = event.get("summary", "")
        description = event.get("description", "")

        if not title.startswith("Esame: "):
            return None

        start_info = event.get("start", {})
        date_str = start_info.get("dateTime", start_info.get("date", "Unknown Date"))
        if "T" in date_str:
            date_str = date_str.split("T")[0]

        cache_key = f"{title} ({date_str})"

        if self.interactive:
            if cache_key in self.exam_decision_cache:
                return self.exam_decision_cache[cache_key]["color"]

            if title in self.subscribed_titles:
                print(
                    f"{Colors.WARNING} ↳ Auto-declining '{title}' on {date_str} (already subscribed to another date){Colors.ENDC}"
                )
                self.exam_decision_cache[cache_key] = {
                    "color": self.COLOR_GREY,
                    "subscribed": False,
                }
                self._save_exam_states()
                return self.COLOR_GREY

            # Prompt 1: Subscription Status
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

            is_subscribed = False
            while True:
                prompt_msg = f"{Colors.OKCYAN}❓ Subscribed to '{title}' on {date_str}?{suggestion_str}: {Colors.ENDC}"
                ans = input(prompt_msg).strip().lower()

                if ans == "" and default_ans:
                    ans = default_ans

                if ans in ["y", "yes"]:
                    is_subscribed = True
                    break
                elif ans in ["n", "no"]:
                    is_subscribed = False
                    break
                else:
                    print(
                        f"{Colors.WARNING} ↳ Please answer 'y' or 'n' (or press Enter for suggestion).{Colors.ENDC}"
                    )

            # Prompt 2: Color Choice
            default_color = self.COLOR_RED if is_subscribed else self.COLOR_GREY
            print("Available Google Calendar Colors:")
            print(
                f"{Colors.BOLD}{Colors.C1_LAVENDER}1: Lavender (1){Colors.ENDC}    {Colors.BOLD}{Colors.C2_SAGE}2: Sage (2){Colors.ENDC}       {Colors.BOLD}{Colors.C3_GRAPE}3: Grape (3){Colors.ENDC}     {Colors.BOLD}{Colors.C4_FLAMINGO}4: Flamingo (4){Colors.ENDC}"
            )
            print(
                f"{Colors.BOLD}{Colors.C5_BANANA}5: Banana (5){Colors.ENDC}      {Colors.BOLD}{Colors.C6_TANGERINE}6: Tangerine (6){Colors.ENDC}  {Colors.BOLD}{Colors.C7_PEACOCK}7: Peacock (7){Colors.ENDC}   {Colors.BOLD}{Colors.C8_GRAPHITE}8: Graphite (8){Colors.ENDC}"
            )
            print(
                f"{Colors.BOLD}{Colors.C9_BLUEBERRY}9: Blueberry (9){Colors.ENDC}  {Colors.BOLD}{Colors.C10_BASIL}10: Basil (10){Colors.ENDC}   {Colors.BOLD}{Colors.C11_TOMATO}11: Tomato (11){Colors.ENDC}"
            )

            chosen_color = None
            valid_colors = [str(i) for i in range(1, 12)]
            while True:
                prompt_msg = f"{Colors.OKCYAN}❓ Pick a color ID for this exam (1-11) [Default {default_color}]: {Colors.ENDC}"
                ans = input(prompt_msg).strip()

                if ans == "":
                    chosen_color = default_color
                    break
                elif ans in valid_colors:
                    chosen_color = ans
                    break
                else:
                    print(
                        f"{Colors.WARNING} ↳ Invalid choice. Please pick from 1 to 11.{Colors.ENDC}"
                    )

            self.exam_decision_cache[cache_key] = {
                "color": chosen_color,
                "subscribed": is_subscribed,
            }
            if is_subscribed:
                self.subscribed_titles.add(title)
            self._save_exam_states()
            return chosen_color

        else:
            if cache_key in self.exam_decision_cache:
                return self.exam_decision_cache[cache_key]["color"]

            if title in self.subscribed_titles:
                self.exam_decision_cache[cache_key] = {
                    "color": self.COLOR_GREY,
                    "subscribed": False,
                }
                self._save_exam_states()
                return self.COLOR_GREY

            color = None
            is_sub = False
            if description.startswith("Non iscritto"):
                color = self.COLOR_GREY
                is_sub = False
            elif description.startswith("Iscritto"):
                color = self.COLOR_RED
                is_sub = True

            if color is not None:
                self.exam_decision_cache[cache_key] = {
                    "color": color,
                    "subscribed": is_sub,
                }
                if is_sub:
                    self.subscribed_titles.add(title)
                self._save_exam_states()

            return color


class LectureColoringStrategy(EventColoringStrategy):
    """
    Strategy specifically for coloring Polimi lectures.
    """

    AVAILABLE_LECTURE_COLORS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"]

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
        # If all 11 colors are used, fall back to the full list (duplicates unavoidable).
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
                print(
                    f"{Colors.BOLD}{Colors.C1_LAVENDER}1: Lavender (1){Colors.ENDC}    {Colors.BOLD}{Colors.C2_SAGE}2: Sage (2){Colors.ENDC}       {Colors.BOLD}{Colors.C3_GRAPE}3: Grape (3){Colors.ENDC}     {Colors.BOLD}{Colors.C4_FLAMINGO}4: Flamingo (4){Colors.ENDC}"
                )
                print(
                    f"{Colors.BOLD}{Colors.C5_BANANA}5: Banana (5){Colors.ENDC}      {Colors.BOLD}{Colors.C6_TANGERINE}6: Tangerine (6){Colors.ENDC}  {Colors.BOLD}{Colors.C7_PEACOCK}7: Peacock (7){Colors.ENDC}   {Colors.BOLD}{Colors.C8_GRAPHITE}8: Graphite (8){Colors.ENDC}"
                )
                print(
                    f"{Colors.BOLD}{Colors.C9_BLUEBERRY}9: Blueberry (9){Colors.ENDC}  {Colors.BOLD}{Colors.C10_BASIL}10: Basil (10){Colors.ENDC}   {Colors.BOLD}{Colors.C11_TOMATO}11: Tomato (11){Colors.ENDC}"
                )

                while True:
                    prompt_msg = f"{Colors.OKCYAN}❓ Pick a color ID for ALL lectures of this course (1-11): {Colors.ENDC}"
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
