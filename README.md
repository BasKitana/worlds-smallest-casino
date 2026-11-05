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
