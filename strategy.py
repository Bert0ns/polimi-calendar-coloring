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


class PolimiExamColoringStrategy(EventColoringStrategy):
    """
    Strategy for coloring Polimi exams based on enrollment status.
    Rules:
    - Title starts with "Esame: " AND Description starts with "Non iscritto" -> Grey ('8')
    - Title starts with "Esame: " AND Description starts with "Iscritto" -> Red ('11')
    - In interactive mode, prompts the user instead of relying on the description.
    """

    COLOR_GREY = "8"
    COLOR_RED = "11"

    def __init__(self, interactive=False):
        self.interactive = interactive
        # Cache decisions so we don't ask multiple times for the exact same exam
        self.decision_cache = {}
        # Track titles of exams the user is already subscribed to
        self.subscribed_titles = set()

    def determine_color(self, event):
        title = event.get("summary", "")
        description = event.get("description", "")

        if title.startswith("Esame: "):
            if self.interactive:
                start_info = event.get("start", {})
                date_str = start_info.get(
                    "dateTime", start_info.get("date", "Unknown Date")
                )
                if "T" in date_str:
                    date_str = date_str.split("T")[0]

                cache_key = f"{title} ({date_str})"

                if cache_key in self.decision_cache:
                    return self.decision_cache[cache_key]

                # Since a student can only subscribe to one date per exam,
                # if they already said 'y' to this exam on a different date, auto-decline this one.
                if title in self.subscribed_titles:
                    print(
                        f"{Colors.WARNING} ↳ Auto-declining '{title}' on {date_str} (already subscribed to another date){Colors.ENDC}"
                    )
                    self.decision_cache[cache_key] = self.COLOR_GREY
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
                    prompt_msg = f"{Colors.OKCYAN}❓ Subscribed to '{title}' on {date_str}?{suggestion_str}: {Colors.ENDC}"
                    ans = input(prompt_msg).strip().lower()

                    # Default to suggestion if user just presses Enter
                    if ans == "" and default_ans:
                        ans = default_ans

                    if ans in ["y", "yes"]:
                        self.decision_cache[cache_key] = self.COLOR_RED
                        self.subscribed_titles.add(title)
                        break
                    elif ans in ["n", "no"]:
                        self.decision_cache[cache_key] = self.COLOR_GREY
                        break
                    else:
                        print(
                            f"{Colors.WARNING} ↳ Please answer 'y' or 'n' (or press Enter for suggestion).{Colors.ENDC}"
                        )
                return self.decision_cache[cache_key]
            else:
                if description.startswith("Non iscritto"):
                    return self.COLOR_GREY
                elif description.startswith("Iscritto"):
                    return self.COLOR_RED

        return None
