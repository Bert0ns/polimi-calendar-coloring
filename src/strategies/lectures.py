import hashlib
from .base import PersistentColoringStrategy
from colors import Colors


class LectureColoringStrategy(PersistentColoringStrategy):
    """
    Strategy specifically for coloring Polimi lectures.
    """

    AVAILABLE_LECTURE_COLORS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"]

    def __init__(self, interactive=False):
        super().__init__("course_colors.json", interactive)

    def _get_deterministic_color(self, course_name):
        used_colors = set(self.state.values())
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

        if course_name not in self.state:
            if self.interactive:
                print(
                    f"\n{Colors.OKCYAN}🎨 New Course Detected: {Colors.BOLD}'{course_name}'{Colors.ENDC}"
                )
                Colors.print_color_palette()

                while True:
                    prompt_msg = f"{Colors.OKCYAN}❓ Pick a color ID for ALL lectures of this course (1-11): {Colors.ENDC}"
                    ans = input(prompt_msg).strip()
                    if ans in self.AVAILABLE_LECTURE_COLORS:
                        self.state[course_name] = ans
                        self._save_state()
                        break
                    else:
                        print(
                            f"{Colors.WARNING} ↳ Invalid choice. Please pick from {self.AVAILABLE_LECTURE_COLORS}.{Colors.ENDC}"
                        )
            else:
                self.state[course_name] = self._get_deterministic_color(course_name)
                self._save_state()

        return self.state[course_name]
