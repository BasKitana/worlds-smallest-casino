import screen
from blackjack import blackjack
from betting import bet_tier
from instructions import how_to_play
from poker import poker
from roulette import roulette

WINNING_BALANCE = 10_000

GARAGE_MENU = [
    "1. Poker",
    "2. Blackjack",
    "3. Roulette",
    "4. How to play",
    "5. Exit",
    "",
]


def victory(balance):
    screen.show(
        "You win!",
        balance,
        [
            f"Congratulations! You reached {screen.money(balance)} and broke the bank!",
            "You win the game. Thanks for playing World's Smallest Casino!",
        ],
    )


def goodbye(balance=None):
    screen.clear()
    if balance is None:
        print("Goodbye!")
    else:
        print(f"Goodbye! You leave the casino with {screen.money(balance)}.")


def notify_tier_change(previous_tier, balance):
    tier = bet_tier(balance)
    if tier > previous_tier:
        screen.notice(f"Tier up! Your balance moved to Tier {tier}.", "tier")
    elif tier < previous_tier:
        screen.notice(f"Tier down. Your balance moved to Tier {tier}.", "tier")


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
    screen.reset()
    while True:
        screen.show("Garage", balance, GARAGE_MENU)

        choice = input("Choose a table or option: ").strip()
        tables = {"1": poker, "2": blackjack, "3": roulette}
        if choice in tables:
            balance = play_table(tables[choice], balance)
        elif choice == "4":
            how_to_play(balance)
            continue
        elif choice == "5":
            goodbye(balance)
            return
        else:
            screen.notice("Invalid choice. Please select 1, 2, 3, 4, or 5.", "error")
            continue

        if balance >= WINNING_BALANCE:
            victory(balance)
            return


def main():
    while True:
        screen.show("Main menu", body=["1. Start", "2. Exit", ""])
        choice = input("Choose an option: ").strip()

        if choice == "1":
            garage(500)
            return
        elif choice == "2":
            goodbye()
            return
        else:
            screen.notice("Invalid choice. Please select 1 or 2.", "error")


if __name__ == "__main__":
    main()
