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

# "\033[" starts an ANSI escape code: a few characters the terminal treats as a
# command instead of text. These clear the screen and scrollback, then move to the top.
CLEAR_CODE = "\033[2J\033[3J\033[H"
RESET = "\033[0m"
# Color codes by kind of message; "\033[0m" (RESET) returns to normal text.
COLORS = {
    "bold": "1",
    "win": "32",
    "lose": "31",
    "error": "31",
    "red": "31",
    "tier": "33",
}

# Module-level state shared by every screen during one game. The leading underscore
# marks _notices as internal: other files should call notice() instead.
rounds_played = 0
history = []  # Newest round first, at most HISTORY_SIZE entries.
_notices = []


def reset():
    """Start a new game: forget past rounds and pending notices."""
    # global lets this function reassign the module-level counter, not a local copy.
    global rounds_played
    rounds_played = 0
    history.clear()
    _notices.clear()


def money(amount):
    # The "," format option adds thousands separators: 1250 becomes "$1,250".
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
    # Split on single spaces so join() puts the line back exactly as it was.
    return " ".join(
        paint(word, "red") if word.endswith(("♥", "♦")) else word for word in line.split(" ")
    )


def strip_ansi(text):
    """Remove ANSI escape codes, for reading output in tests."""
    plain = []
    in_code = False
    # Skip from each escape character up to the letter that ends its code.
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
    # Insert at index 0 so the newest round is first, then drop rounds past the limit.
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

    # Each notice is shown once, then the queue is emptied for the next screen.
    for text, kind in _notices:
        print(paint(f"> {text}", kind))
    _notices.clear()

    print()
    for line in body:
        print(color_cards(line))
