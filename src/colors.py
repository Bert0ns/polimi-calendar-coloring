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

    @staticmethod
    def print_color_palette():
        """Prints the full 11-color Google Calendar palette with ANSI colors."""
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
