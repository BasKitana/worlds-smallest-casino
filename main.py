# Entry point: the start menu opens the garage, which routes players to each game.
# The garage keeps the balance in memory; closing the program does not save it.
import screen
from blackjack import blackjack
from betting import bet_limits, bet_tier
from instructions import how_to_play
from poker import poker
from roulette import roulette

# Underscores make numeric literals easier to read: 10_000 is the integer 10000.
WINNING_BALANCE = 10_000
# Below the smallest bet allowed ($10, Tier 1's minimum), the player can't bet at
# all, so the game ends. This covers $0 and any leftover amount from $1 to $9.
# bet_limits(0) returns Tier 1's (minimum, maximum); [0] picks the minimum.
LOSING_BALANCE = bet_limits(0)[0]

# The garage choices drawn as the body of the garage screen. The empty string
# at the end adds a blank line before the input prompt.
GARAGE_MENU = [
    "1. Poker",
    "2. Blackjack",
    "3. Roulette",
    "4. How to play",
    "5. Exit",
    "",
]


def victory(balance):
    # Draw the end-of-game screen once the player reaches or exceeds the target.
    screen.show(
        "You win!",
        balance,
        [
            f"Congratulations! You reached {screen.money(balance)} and broke the bank!",
            "You win the game. Thanks for playing World's Smallest Casino!",
        ],
    )


def game_over(balance):
    # Draw the losing screen. Like victory(), it is the last thing the garage draws
    # before returning, so no other screen clears it away.
    if balance == 0:
        broke = "You lost every last dollar!"
    else:
        broke = (
            f"You're down to {screen.money(balance)}. "
            f"That won't even cover a {screen.money(LOSING_BALANCE)} bet."
        )
    screen.show(
        "Game over",
        balance,
        [
            broke,
            "The garage door rattles shut behind you.",
            "Your boss called. Twice. Maybe it's time to go to work?",
            "",
            # paint() colors these words red, like other losses.
            screen.paint("GAME OVER. Thanks for playing World's Smallest Casino!", "lose"),
        ],
    )


def goodbye(balance=None):
    # Clear the screen one last time; after Start, also show the money the player leaves with.
    screen.clear()
    if balance is None:
        print("Goodbye!")
    else:
        print(f"Goodbye! You leave the casino with {screen.money(balance)}.")


def notify_tier_change(previous_tier, balance):
    # Compare tiers before and after a round; queue a message only if the tier changed.
    tier = bet_tier(balance)
    if tier > previous_tier:
        screen.notice(f"Tier up! Your balance moved to Tier {tier}.", "tier")
    elif tier < previous_tier:
        screen.notice(f"Tier down. Your balance moved to Tier {tier}.", "tier")


def play_table(game, balance):
    """Play rounds back to back until the player leaves the table, wins, or goes broke."""
    # game is the table's function itself (poker, blackjack, or roulette). Python
    # functions can be passed around like any other value and called later.
    while True:
        # Remember the tier before the round so a change can be announced after it.
        previous_tier = bet_tier(balance)
        result = game(balance)
        # None means the player cancelled, so no round was played: back to the garage.
        if result is None:
            return balance

        balance = result
        notify_tier_change(previous_tier, balance)
        # Stop at the winning or losing balance. Only stop here: the garage draws the
        # victory or game-over screen, because anything drawn here would be cleared
        # right away when the garage redraws its menu.
        if balance >= WINNING_BALANCE:
            return balance
        if balance < LOSING_BALANCE:
            return balance


def garage(balance):
    # A new game starts with no round history. Each visit to a table plays rounds
    # until the player leaves, then returns the balance for the next menu visit.
    screen.reset()
    while True:
        screen.show("Garage", balance, GARAGE_MENU)

        # input() returns text; strip() removes surrounding spaces before comparison.
        choice = input("Choose a table or option: ").strip()
        # Map each menu choice to its table's function; play_table() calls the one chosen.
        tables = {"1": poker, "2": blackjack, "3": roulette}
        if choice in tables:
            # Assigning the returned balance carries the results into future rounds.
            balance = play_table(tables[choice], balance)
        elif choice == "4":
            how_to_play(balance)
            # Reading instructions can't change the balance, so skip the victory check.
            continue
        elif choice == "5":
            goodbye(balance)
            # return leaves this function, ending the garage's otherwise endless loop.
            return
        else:
            screen.notice("Invalid choice. Please select 1, 2, 3, 4, or 5.", "error")
            # Redraw the menu immediately; no table has returned a new balance.
            continue

        # Check after returning from any table; reaching or passing the target wins.
        if balance >= WINNING_BALANCE:
            victory(balance)
            # Returning also lets main() finish, so victory ends the session.
            return
        # Too little money for any bet: show the game-over screen and end the session.
        if balance < LOSING_BALANCE:
            game_over(balance)
            return


def main():
    # Invalid choices repeat the start menu; starting creates a fresh $500 session.
    while True:
        # No balance is shown yet; body= names the argument so balance can be skipped.
        screen.show("Main menu", body=["1. Start", "2. Exit", ""])
        choice = input("Choose an option: ").strip()

        if choice == "1":
            garage(500)
            # Once the garage exits, finish instead of showing the start menu again.
            return
        elif choice == "2":
            goodbye()
            return
        else:
            # The loop redraws the start menu with this message at the top.
            screen.notice("Invalid choice. Please select 1 or 2.", "error")


# Run the menu only when launched directly, not when tests import this module.
if __name__ == "__main__":
    main()
