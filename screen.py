"""Terminal screens for the casino.

Every step clears the terminal and redraws a status line, the most recent
rounds, and any notices (errors, tier changes), so the vital information
survives each clear. Only print and ANSI escape codes are used, so this
needs no libraries.
"""

# A typical screen drawn by show(), from top to bottom:
#
#   WORLD'S SMALLEST CASINO | Blackjack | Round 3 | $550 | Tier 1: $10-$100   <- status_line()
#   --------------------------------------------------------------------------
#   Recent rounds                                                             <- history
#
#     Round 2 · Blackjack: You beat the dealer. You win $50.
#       You: 10♠ 9♠ (19) | Dealer: 10♣ 8♥ (18)
#   --------------------------------------------------------------------------
#   > Bet rejected. The minimum bet is $10.                                   <- notices
#
#   Place a bet to deal a new hand.                                           <- body
#
# The game files only decide what goes in the body and which notices or rounds
# to add; this file owns how everything looks.

# betting is one of this project's own files, not a library. It supplies the
# tier and bet limits shown in the status line.
import betting

USE_ANSI = True  # Tests turn this off to get plain text with no clearing.
WIDTH = 74  # Number of "-" characters in each divider line.
HISTORY_SIZE = 3  # How many finished rounds stay on screen.

# "\033[" starts an ANSI escape code: a few characters the terminal treats as a
# command instead of text. "\033" is the Escape character written in octal.
# 2J clears the visible screen, 3J clears the scrollback (text you could scroll
# up to), and H moves the cursor to the top-left corner.
CLEAR_CODE = "\033[2J\033[3J\033[H"
RESET = "\033[0m"  # Turns off any color or bold set by an earlier code.
# Color codes by kind of message: 1 is bold, 31 red, 32 green, and 33 yellow.
# A kind missing from this dictionary, such as "push" or "info", stays uncolored.
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
# Each entry is a dictionary describing one finished round (see record_round()).
history = []  # Newest round first, at most HISTORY_SIZE entries.
# Each notice is a (text, kind) tuple waiting to appear on the next screen.
_notices = []


def reset():
    """Start a new game: forget past rounds and pending notices."""
    # global lets this function reassign the module-level counter, not a local copy.
    global rounds_played
    rounds_played = 0
    # clear() empties the existing lists in place, so every file that refers to
    # screen.history sees the same, now-empty list.
    history.clear()
    _notices.clear()


def money(amount):
    # The "," format option adds thousands separators: 1250 becomes "$1,250".
    return f"${amount:,}"


def paint(text, kind):
    """Wrap text in the ANSI color for its kind, then reset the color afterward."""
    # get() returns None for a kind with no color instead of raising a KeyError.
    code = COLORS.get(kind)
    if not USE_ANSI or code is None:
        return text
    # "\033[32m" switches to green (for example); RESET switches back to normal.
    return f"\033[{code}m{text}{RESET}"


def color_cards(line):
    """Show hearts and diamonds cards in red."""
    if not USE_ANSI:
        return line
    # A card such as "10♥" ends in its suit, so checking the last character finds it.
    # endswith() accepts a tuple and matches either suit.
    # Split on single spaces so join() puts the line back exactly as it was.
    return " ".join(
        paint(word, "red") if word.endswith(("♥", "♦")) else word for word in line.split(" ")
    )


def strip_ansi(text):
    """Remove ANSI escape codes, for reading output in tests."""
    plain = []
    # in_code is True while we are inside a code such as "\033[32m".
    in_code = False
    # Skip from each escape character up to the letter that ends its code.
    for char in text:
        if in_code:
            # The code ends at its final letter (m, J, or H); keep skipping until then.
            in_code = not char.isalpha()
        elif char == "\033":
            in_code = True
        else:
            plain.append(char)
    # Building a list and joining once is faster than adding strings in a loop.
    return "".join(plain)


def current_round():
    """The number of the round being played now (one more than the rounds finished)."""
    return rounds_played + 1


def notice(text, kind="info"):
    """Queue a message for the top of the next screen."""
    # The message isn't printed now, because the next screen would clear it at once.
    _notices.append((text, kind))


def record_round(table, outcome, details=(), kind="info"):
    """Number a finished round and add it to the recent-rounds history."""
    # global is needed because += reassigns the module-level counter.
    global rounds_played
    rounds_played += 1
    history.insert(
        0,
        {
            "round": rounds_played,
            "table": table,  # Which game was played, e.g. "Blackjack".
            "outcome": outcome,  # One sentence such as "You win $50."
            "details": list(details),  # Extra lines, such as both final hands.
            "kind": kind,  # Sets the color: "win", "lose", or "push".
        },
    )
    # Insert at index 0 so the newest round is first, then drop rounds past the limit.
    # del with a slice removes every entry from index HISTORY_SIZE to the end.
    del history[HISTORY_SIZE:]


def status_line(location, balance=None, at_table=False):
    """Build the one-line summary shown at the top of every screen."""
    parts = ["WORLD'S SMALLEST CASINO", location]
    # The round number only matters while playing, not on the menus.
    if at_table:
        parts.append(f"Round {current_round()}")
    # The main menu has no balance yet because the game has not started.
    if balance is not None:
        minimum, maximum = betting.bet_limits(balance)
        parts.append(money(balance))
        parts.append(f"Tier {betting.bet_tier(balance)}: {money(minimum)}-{money(maximum)}")
    # " | ".join() puts a separator between parts, but not before the first one.
    return " | ".join(parts)


def clear():
    """Wipe the terminal (does nothing in tests, where USE_ANSI is False)."""
    # end="" stops print() from adding a newline, so drawing starts on the top line.
    if USE_ANSI:
        print(CLEAR_CODE, end="")


def show(location, balance=None, body=(), at_table=False):
    """Clear the terminal and draw one full screen."""
    # 1. Start from a blank terminal.
    clear()

    # 2. Status line in bold, followed by a divider. "-" * WIDTH repeats the dash.
    print(paint(status_line(location, balance, at_table), "bold"))
    print("-" * WIDTH)

    # 3. Recent rounds, newest first. An empty list counts as False, so the whole
    # block is skipped before the first round has finished.
    if history:
        print("Recent rounds")
        for entry in history:
            # A blank line before each round keeps rounds visually separate.
            print()
            headline = f"  Round {entry['round']} · {entry['table']}: {entry['outcome']}"
            print(paint(headline, entry["kind"]))
            # Indent the detail lines under their round so it is clear what they belong to.
            for detail in entry["details"]:
                print(color_cards(f"    {detail}"))
        print("-" * WIDTH)

    # 4. Notices, such as errors or tier changes, each starting with ">".
    # Each notice is shown once, then the queue is emptied for the next screen.
    for text, kind in _notices:
        print(paint(f"> {text}", kind))
    _notices.clear()

    # 5. The body: whatever this step needs, such as a menu or the cards on the table.
    # The caller asks for input right after this, so the prompt appears below the body.
    print()
    for line in body:
        print(color_cards(line))
