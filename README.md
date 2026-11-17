# World's Smallest Casino

A small text menu with a $500 starting balance and playable Poker, Blackjack, and Roulette tables.

## Run

```sh
python3 main.py
```

## Test

```sh
python3 -m unittest
```

## Scope

The numbered requirements below include the early placeholder-menu milestones;
all three tables are now playable.

- R01: Show the root menu and start or exit.
- R02: Show the garage menu with a $500 balance; table selections are placeholders.
- R03: Return to the garage after a placeholder selection and exit from either menu.
- R05: `betting.get_bet(balance)` accepts a whole-dollar bet only if it is affordable and within the current tier's limits.
- R06: Rejected bets explain whether they are below the minimum, above the maximum, or greater than the balance.
- R09: The Blackjack table takes a bet, deals two cards each from a fresh 52-card deck, and shows the player's cards and the dealer's face-up card.
- R10: The player can hit or stand. The dealer draws to 17 and stands on soft 17. A win pays 1:1, a blackjack pays 3:2 rounded down to whole dollars, and a push returns the bet.
- R11: The Roulette table offers single number (35:1), red/black, odd/even, low/high (1:1), and dozen (2:1) wagers on a European wheel (0-36).
- R12: Each spin picks a random number, pays out or takes the bet, and the garage keeps the new balance.
- R13: Poker is five-card draw against a dealer, using standard five-card hand rankings and even-money win/loss payouts; ties return the bet.
- R14: Players may stand or discard up to three cards, and the dealer draws according to a simple pair/high-card strategy.
- Update balance: after each completed round, winnings are added or losses subtracted and the new balance is shown.
- Win the game: when the balance reaches $10,000 or more, play ends with a victory message.

## Understanding the files

Read the code in this order. Each Python file contains comments explaining its
purpose, important steps, and less obvious Python syntax.

1. `main.py`: starts the program, shows menus, keeps the balance between rounds,
   announces betting-tier changes, and ends the session at $10,000 or more.
2. `betting.py`: chooses a tier from the balance, supplies its minimum/maximum
   bets, and asks for an affordable whole-dollar bet. A blank entry cancels.
3. `blackjack.py`: builds a deck, deals cards, handles hit/stand decisions,
   adjusts ace values, compares hands, and calculates the round's payout.
4. `roulette.py`: turns menu choices into sets of winning numbers, spins the
   wheel, and calculates winnings or losses from the selected wager.
5. `poker.py`: deals five-card hands, replaces discards, ranks hands with
   tie-breakers, and compares the player's hand with the dealer's.
6. `test_main.py`, `test_betting.py`, `test_blackjack.py`, `test_roulette.py`,
   and `test_poker.py`: check their corresponding modules. They use scripted
   input and controlled game results to make interactive behavior repeatable.
7. `.gitignore`: tells Git to ignore generated Python caches and compiled files.
   This `README.md` provides the run/test commands and a guide to the project.

The main flow is `main()` → `garage(balance)` → the selected game → the garage.
Each game returns a balance. A bet is not deducted in advance: settlement adds
the profit for a win, subtracts the stake for a loss, or adds zero for a tie.
The balance exists only in memory; a new session starts at $500.

The tests run with Python's built-in `unittest` library. Methods starting with
`test_` are test cases, and assertions check the expected result. `patch()`
temporarily substitutes input or random behavior; output capture lets tests
check messages without requiring a person to play the game.
