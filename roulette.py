# European Roulette uses numbers 0-36, with a single green zero.
# Each wager is (display label, set of winning numbers, profit multiplier).
import random

import screen
from betting import get_bet

RED = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
# range() excludes its upper bound; set subtraction keeps non-red numbers 1-36.
BLACK = set(range(1, 37)) - RED

# Menu choices map to preset wagers. Zero is excluded, even from the "Even" bet.
# % is the remainder operator: n % 2 is 1 for odd numbers and 0 for even numbers.
OUTSIDE_WAGERS = {
    "2": ("Red", RED, 1),
    "3": ("Black", BLACK, 1),
    "4": ("Odd", {n for n in range(1, 37) if n % 2 == 1}, 1),
    "5": ("Even", {n for n in range(1, 37) if n % 2 == 0}, 1),
    "6": ("Low (1-18)", set(range(1, 19)), 1),
    "7": ("High (19-36)", set(range(19, 37)), 1),
}

WAGER_MENU = [
    "Roulette Wagers",
    "1. Single number (pays 35 to 1)",
    "2. Red (pays 1 to 1)",
    "3. Black (pays 1 to 1)",
    "4. Odd (pays 1 to 1)",
    "5. Even (pays 1 to 1)",
    "6. Low 1-18 (pays 1 to 1)",
    "7. High 19-36 (pays 1 to 1)",
    "8. Dozen (pays 2 to 1)",
    "9. Return to the garage",
    "",
]


def color(number):
    # Translate a valid wheel number into the color shown in the result message.
    if number == 0:
        return "Green"
    return "Red" if number in RED else "Black"


def ask_number(prompt, low, high, balance=None, title=""):
    # Retry until an integer falls within both inclusive bounds; blank means back.
    while True:
        screen.show("Roulette", balance, [title, ""] if title else (), at_table=True)
        choice = input(prompt).strip()
        if choice == "":
            return None
        if choice.isdigit() and low <= int(choice) <= high:
            return int(choice)
        screen.notice(f"Invalid choice. Please enter a number from {low} to {high}.", "error")


def choose_wager(balance=None):
    # Return a wager tuple, or None when the player chooses to leave the table.
    while True:
        screen.show("Roulette", balance, WAGER_MENU, at_table=True)
        choice = input("Choose a wager: ").strip()

        if choice == "1":
            number = ask_number(
                "Pick a number (0-36, or press Enter to go back): ",
                0,
                36,
                balance,
                "Single number (pays 35 to 1)",
            )
            if number is None:
                # Cancel just this number selection and redisplay the wager menu.
                continue
            return (f"Number {number}", {number}, 35)
        elif choice in OUTSIDE_WAGERS:
            return OUTSIDE_WAGERS[choice]
        elif choice == "8":
            dozen = ask_number(
                "Pick a dozen (1 = 1-12, 2 = 13-24, 3 = 25-36, or press Enter to go back): ",
                1,
                3,
                balance,
                "Dozen (pays 2 to 1)",
            )
            if dozen is None:
                continue
            # Convert choices 1, 2, 3 into starting numbers 1, 13, 25.
            start = (dozen - 1) * 12 + 1
            return (f"Dozen {start}-{start + 11}", set(range(start, start + 12)), 2)
        elif choice == "9":
            return None
        else:
            screen.notice("Invalid choice. Please select 1 through 9.", "error")


def spin():
    # randint includes both endpoints, giving 37 possible results including zero.
    return random.randint(0, 36)


def resolve(wager, bet, number):
    # Ignore the display label and check whether the result belongs to the wager.
    # Return net profit/loss: the calling game has not deducted the original stake.
    _, numbers, payout = wager
    if number in numbers:
        return bet * payout
    return -bet


def roulette(balance):
    # Play one spin. Returning None if either selection is cancelled tells the
    # garage that the player left the table.
    wager = choose_wager(balance)
    if wager is None:
        return None

    name, _, payout = wager
    bet = get_bet(balance, "Roulette", [f"Wager: {name} (pays {payout} to 1)"])
    if bet is None:
        return None

    number = spin()
    change = resolve(wager, bet, number)
    landed = f"The ball lands on {number} {color(number)}."
    if change > 0:
        outcome, kind = f"{landed} You win ${change}!", "win"
    else:
        outcome, kind = f"{landed} You lose ${bet}.", "lose"

    # Save the spin for the recent-rounds history shown on the next screen, then
    # return the new balance: add winnings or subtract the lost stake exactly once.
    screen.record_round("Roulette", outcome, [f"Wager: ${bet} on {name}"], kind)
    return balance + change
