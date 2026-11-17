# Shared betting rules used by all three games. Amounts are whole dollars.
# This module validates a bet but never subtracts money from the balance.
import screen
def bet_tier(balance):
    # Check the highest threshold first because its balances also qualify for Tier 2.
    if balance >= 5000:
        return 3
    if balance >= 2500:
        return 2
    return 1


def bet_limits(balance):
    # Each tuple is (minimum, maximum). Tiers start at 1; tuple indexes start at 0.
    return ((10, 100), (100, 500), (500, 2500))[bet_tier(balance) - 1]


def validate_bet(amount, balance):
    # Return an error message for an invalid amount, or None when it is allowed.
    minimum, maximum = bet_limits(balance)

    # Affordability takes priority if a bet breaks more than one rule.
    if amount > balance:
        return f"You only have ${balance}. You cannot bet ${amount}."
    if amount < minimum:
        return f"The minimum bet is ${minimum}."
    if amount > maximum:
        return f"The maximum bet is ${maximum}."
    return None


def get_bet(balance, location="Table", body=()):
    """Redraw the bet screen until the player enters a valid bet or leaves (None)."""
    while True:
        screen.show(location, balance, [*body, ""] if body else (), at_table=True)
        choice = input("Enter your bet (or press Enter to return to the garage): ").strip()

        if choice == "":
            # None signals cancellation to the calling game; it is not a $0 bet.
            return None
        if not choice.isdigit():
            # Reject ordinary text, negative signs, and decimal amounts before int().
            screen.notice("Invalid bet. Please enter a whole dollar amount.", "error")
            continue  # Redraw the bet screen with the error instead of using this entry.

        amount = int(choice)  # Convert the numeric input string into a whole number.
        error = validate_bet(amount, balance)
        if error:
            # A nonempty error string is true in an if statement; None is false.
            screen.notice(f"Bet rejected. {error}", "error")
        else:
            return amount
