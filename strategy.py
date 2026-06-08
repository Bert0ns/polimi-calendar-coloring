from abc import ABC, abstractmethod


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
                        f"Auto-declining '{title}' on {date_str} because you are already subscribed to another date."
                    )
                    self.decision_cache[cache_key] = self.COLOR_GREY
                    return self.COLOR_GREY

                suggestion_str = ""
                default_ans = None
                if description.startswith("Non iscritto"):
                    suggestion_str = " [Suggested: n (Not subscribed)]"
                    default_ans = "n"
                elif description.startswith("Iscritto"):
                    suggestion_str = " [Suggested: y (Subscribed)]"
                    default_ans = "y"

                while True:
                    prompt_msg = f"Are you subscribed to '{title}' on {date_str}?{suggestion_str} (y/n): "
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
                            "Please answer 'y' or 'n'. If there is a suggestion, you can press Enter to accept it."
                        )
                return self.decision_cache[cache_key]
            else:
                if description.startswith("Non iscritto"):
                    return self.COLOR_GREY
                elif description.startswith("Iscritto"):
                    return self.COLOR_RED

        return None
