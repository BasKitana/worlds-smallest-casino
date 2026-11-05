from blackjack import blackjack
from roulette import roulette


def garage(balance):
    while True:
        print(f"\nGarage Casino — Balance: ${balance}")
        print("1. Poker")
        print("2. Blackjack")
        print("3. Roulette")
        print("4. Exit")

        choice = input("Choose a table or exit: ").strip()
        tables = {"1": "Poker"}

        if choice == "2":
            balance = blackjack(balance)
        elif choice == "3":
            balance = roulette(balance)
        elif choice in tables:
            print(f"\n{tables[choice]} — Placeholder")
            input("Press Enter to return to the garage...")
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
