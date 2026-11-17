# Shared betting rules used by all three games. Amounts are whole dollars.
# This module validates a bet but never subtracts money from the balance.
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


def get_bet(balance):
    # Keep asking until an amount passes validation or the player cancels.
    minimum, maximum = bet_limits(balance)

    while True:
        print(f"\nBalance: ${balance} — Bets: ${minimum}-${maximum}")
        choice = input("Enter your bet (or press Enter to cancel): ").strip()

        if choice == "":
            # None signals cancellation to the calling game; it is not a $0 bet.
            return None
        if not choice.isdigit():
            # Reject ordinary text, negative signs, and decimal amounts before int().
            print("Invalid bet. Please enter a whole dollar amount.")
            continue  # Restart the prompt without validating this entry as an amount.

        amount = int(choice)  # Convert the numeric input string into a whole number.
        error = validate_bet(amount, balance)
        if error:
            # A nonempty error string is true in an if statement; None is false.
            print(f"Bet rejected. {error}")
        else:
            print(f"Bet accepted: ${amount}")
            return amount
