def bet_tier(balance):
    if balance >= 5000:
        return 3
    if balance >= 2500:
        return 2
    return 1


def bet_limits(balance):
    return ((10, 100), (100, 500), (500, 2500))[bet_tier(balance) - 1]


def validate_bet(amount, balance):
    minimum, maximum = bet_limits(balance)

    if amount > balance:
        return f"You only have ${balance}. You cannot bet ${amount}."
    if amount < minimum:
        return f"The minimum bet is ${minimum}."
    if amount > maximum:
        return f"The maximum bet is ${maximum}."
    return None


def get_bet(balance):
    minimum, maximum = bet_limits(balance)

    while True:
        print(f"\nBalance: ${balance} — Bets: ${minimum}-${maximum}")
        choice = input("Enter your bet (or press Enter to return to the garage): ").strip()

        if choice == "":
            return None
        if not choice.isdigit():
            print("Invalid bet. Please enter a whole dollar amount.")
            continue

        amount = int(choice)
        error = validate_bet(amount, balance)
        if error:
            print(f"Bet rejected. {error}")
        else:
            print(f"Bet accepted: ${amount}")
            return amount
