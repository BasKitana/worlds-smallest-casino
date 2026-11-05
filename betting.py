def bet_limits(balance):
    if balance >= 5000:
        return 500, 2500
    if balance >= 2500:
        return 100, 500
    return 10, 100


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
        choice = input("Enter your bet (or press Enter to cancel): ").strip()

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
