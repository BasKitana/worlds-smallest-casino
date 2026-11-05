from blackjack import blackjack
from betting import bet_limits, bet_tier
from poker import poker
from roulette import roulette


def notify_tier_change(previous_tier, balance):
    tier = bet_tier(balance)
    if tier > previous_tier:
        print(f"Tier up! Your balance moved to Tier {tier}.")
    elif tier < previous_tier:
        print(f"Tier down. Your balance moved to Tier {tier}.")


def garage(balance):
    while True:
        print(f"\nGarage Casino — Balance: ${balance}")
        minimum, maximum = bet_limits(balance)
        print(f"Current tier: Tier {bet_tier(balance)} — Bets: ${minimum}-${maximum}")
        print("1. Poker")
        print("2. Blackjack")
        print("3. Roulette")
        print("4. Exit")

        choice = input("Choose a table or exit: ").strip()
        if choice == "1":
            previous_tier = bet_tier(balance)
            balance = poker(balance)
            notify_tier_change(previous_tier, balance)
        elif choice == "2":
            previous_tier = bet_tier(balance)
            balance = blackjack(balance)
            notify_tier_change(previous_tier, balance)
        elif choice == "3":
            previous_tier = bet_tier(balance)
            balance = roulette(balance)
            notify_tier_change(previous_tier, balance)
        elif choice == "4":
            print("Goodbye!")
            return
        else:
            print("Invalid choice. Please select 1, 2, 3, or 4.")


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
