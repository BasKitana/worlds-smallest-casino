"""Terminal screens for the casino.

Every step clears the terminal and redraws a status line, the most recent
rounds, and any notices (errors, tier changes), so the vital information
survives each clear. Only print and ANSI escape codes are used, so this
needs no libraries.
"""

import betting

USE_ANSI = True  # Tests turn this off to get plain text with no clearing.
WIDTH = 74
HISTORY_SIZE = 3

CLEAR_CODE = "\033[2J\033[3J\033[H"  # Clear screen and scrollback, cursor to top.
RESET = "\033[0m"
COLORS = {
    "bold": "1",
    "win": "32",
    "lose": "31",
    "error": "31",
    "red": "31",
    "tier": "33",
}

rounds_played = 0
history = []
_notices = []


def reset():
    """Start a new game: forget past rounds and pending notices."""
    global rounds_played
    rounds_played = 0
    history.clear()
    _notices.clear()


def money(amount):
    return f"${amount:,}"


def paint(text, kind):
    code = COLORS.get(kind)
    if not USE_ANSI or code is None:
        return text
    return f"\033[{code}m{text}{RESET}"


def color_cards(line):
    """Show hearts and diamonds cards in red."""
    if not USE_ANSI:
        return line
    return " ".join(
        paint(word, "red") if word.endswith(("♥", "♦")) else word for word in line.split(" ")
    )


def strip_ansi(text):
    """Remove ANSI escape codes, for reading output in tests."""
    plain = []
    in_code = False
    for char in text:
        if in_code:
            in_code = not char.isalpha()
        elif char == "\033":
            in_code = True
        else:
            plain.append(char)
    return "".join(plain)


def current_round():
    return rounds_played + 1


def notice(text, kind="info"):
    """Queue a message for the top of the next screen."""
    _notices.append((text, kind))


def record_round(table, outcome, details=(), kind="info"):
    """Number a finished round and add it to the recent-rounds history."""
    global rounds_played
    rounds_played += 1
    history.insert(
        0,
        {
            "round": rounds_played,
            "table": table,
            "outcome": outcome,
            "details": list(details),
            "kind": kind,
        },
    )
    del history[HISTORY_SIZE:]


def status_line(location, balance=None, at_table=False):
    parts = ["WORLD'S SMALLEST CASINO", location]
    if at_table:
        parts.append(f"Round {current_round()}")
    if balance is not None:
        minimum, maximum = betting.bet_limits(balance)
        parts.append(money(balance))
        parts.append(f"Tier {betting.bet_tier(balance)}: {money(minimum)}-{money(maximum)}")
    return " | ".join(parts)


def clear():
    if USE_ANSI:
        print(CLEAR_CODE, end="")


def show(location, balance=None, body=(), at_table=False):
    """Clear the terminal and draw one full screen."""
    clear()
    print(paint(status_line(location, balance, at_table), "bold"))
    print("-" * WIDTH)

    if history:
        print("Recent rounds")
        for entry in history:
            print()
            headline = f"  Round {entry['round']} · {entry['table']}: {entry['outcome']}"
            print(paint(headline, entry["kind"]))
            for detail in entry["details"]:
                print(color_cards(f"    {detail}"))
        print("-" * WIDTH)

    for text, kind in _notices:
        print(paint(f"> {text}", kind))
    _notices.clear()

    print()
    for line in body:
        print(color_cards(line))
