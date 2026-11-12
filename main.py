from blackjack import blackjack
from betting import bet_limits, bet_tier
from instructions import how_to_play
from poker import poker
from roulette import roulette

WINNING_BALANCE = 10_000


def victory(balance):
    print(f"\nCongratulations! You reached ${balance} and broke the bank!")
    print("You win the game. Thanks for playing World's Smallest Casino!")


def notify_tier_change(previous_tier, balance):
    tier = bet_tier(balance)
    if tier > previous_tier:
        print(f"Tier up! Your balance moved to Tier {tier}.")
    elif tier < previous_tier:
        print(f"Tier down. Your balance moved to Tier {tier}.")


def play_table(game, balance):
    """Play rounds back to back until the player leaves the table or wins."""
    while True:
        previous_tier = bet_tier(balance)
        result = game(balance)
        if result is None:
            return balance

        balance = result
        notify_tier_change(previous_tier, balance)
        if balance >= WINNING_BALANCE:
            return balance


def garage(balance):
    while True:
        print(f"\nGarage Casino — Balance: ${balance}")
        minimum, maximum = bet_limits(balance)
        print(f"Current tier: Tier {bet_tier(balance)} — Bets: ${minimum}-${maximum}")
        print("1. Poker")
        print("2. Blackjack")
        print("3. Roulette")
        print("4. How to play")
        print("5. Exit")

        choice = input("Choose a table or option: ").strip()
        tables = {"1": poker, "2": blackjack, "3": roulette}
        if choice in tables:
            balance = play_table(tables[choice], balance)
        elif choice == "4":
            how_to_play(balance)
            continue
        elif choice == "5":
            print("Goodbye!")
            return
        else:
            print("Invalid choice. Please select 1, 2, 3, 4, or 5.")
            continue

        if balance >= WINNING_BALANCE:
            victory(balance)
            return


def main():
    while True:
        print("\nWorld's Smallest Casino")
        print("1. Start")
        print("2. Exit")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            garage(500)
            return
        elif choice == "2":
            print("Goodbye!")
            return
        else:
            print("Invalid choice. Please select 1 or 2.")


if __name__ == "__main__":
    main()
