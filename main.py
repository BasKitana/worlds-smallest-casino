# Entry point: the start menu opens the garage, which routes players to each game.
# The garage keeps the balance in memory; closing the program does not save it.
from blackjack import blackjack
from betting import bet_limits, bet_tier
from poker import poker
from roulette import roulette

# Underscores make numeric literals easier to read: 10_000 is the integer 10000.
WINNING_BALANCE = 10_000


def victory(balance):
    # Display the end-of-game reward once the player reaches or exceeds the target.
    print(f"\nCongratulations! You reached ${balance} and broke the bank!")
    print("You win the game. Thanks for playing World's Smallest Casino!")


def notify_tier_change(previous_tier, balance):
    # Compare tiers before and after a round; print nothing if the tier is unchanged.
    tier = bet_tier(balance)
    if tier > previous_tier:
        print(f"Tier up! Your balance moved to Tier {tier}.")
    elif tier < previous_tier:
        print(f"Tier down. Your balance moved to Tier {tier}.")


def garage(balance):
    # Each table plays one round and returns the balance for the next menu visit.
    while True:
        print(f"\nGarage Casino — Balance: ${balance}")
        # Unpack the two limits returned as a (minimum, maximum) tuple.
        minimum, maximum = bet_limits(balance)
        print(f"Current tier: Tier {bet_tier(balance)} — Bets: ${minimum}-${maximum}")
        print("1. Poker")
        print("2. Blackjack")
        print("3. Roulette")
        print("4. Exit")

        # input() returns text; strip() removes surrounding spaces before comparison.
        choice = input("Choose a table or exit: ").strip()
        if choice == "1":
            # Keep the old tier so a win or loss can trigger a tier-change message.
            # Assigning the returned balance carries the result into future rounds.
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
            # return leaves this function, ending the garage's otherwise endless loop.
            return
        else:
            print("Invalid choice. Please select 1, 2, 3, or 4.")
            # Retry the menu immediately; no table has returned a new balance.
            continue

        # Check after returning from any table; reaching or passing the target wins.
        if balance >= WINNING_BALANCE:
            victory(balance)
            # Returning also lets main() finish, so victory ends the session.
            return


def main():
    # Invalid choices repeat the start menu; starting creates a fresh $500 session.
    while True:
        print("\nWorld's Smallest Casino")
        print("1. Start")
        print("2. Exit")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            garage(500)
            # Once the garage exits, finish instead of showing the start menu again.
            return
        elif choice == "2":
            print("Goodbye!")
            return
        else:
            print("Invalid choice. Please select 1 or 2.")


# Run the menu only when launched directly, not when tests import this module.
if __name__ == "__main__":
    main()
