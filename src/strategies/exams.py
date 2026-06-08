from .base import PersistentColoringStrategy
from colors import Colors


class ExamColoringStrategy(PersistentColoringStrategy):
    """
    Strategy specifically for coloring Polimi exams.
    """

    COLOR_GREY = "8"
    COLOR_RED = "11"

    def __init__(self, interactive=False):
        super().__init__("exam_states.json", interactive)
        self.subscribed_titles = self._derive_subscribed_titles()

    def _derive_subscribed_titles(self):
        subscribed = set()
        for key, state_data in self.state.items():
            if state_data.get("subscribed", False):
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
            if cache_key in self.state:
                return self.state[cache_key]["color"]

            if title in self.subscribed_titles:
                print(
                    f"{Colors.WARNING} ↳ Auto-declining '{title}' on {date_str} (already subscribed to another date){Colors.ENDC}"
                )
                self.state[cache_key] = {
                    "color": self.COLOR_GREY,
                    "subscribed": False,
                }
                self._save_state()
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
            Colors.print_color_palette()

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

            self.state[cache_key] = {
                "color": chosen_color,
                "subscribed": is_subscribed,
            }
            if is_subscribed:
                self.subscribed_titles.add(title)
            self._save_state()
            return chosen_color

        else:
            if cache_key in self.state:
                return self.state[cache_key]["color"]

            if title in self.subscribed_titles:
                self.state[cache_key] = {
                    "color": self.COLOR_GREY,
                    "subscribed": False,
                }
                self._save_state()
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
                self.state[cache_key] = {
                    "color": color,
                    "subscribed": is_sub,
                }
                if is_sub:
                    self.subscribed_titles.add(title)
                self._save_state()

            return color
