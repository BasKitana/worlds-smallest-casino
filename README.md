# World's Smallest Casino

A small text menu with a $500 starting balance and placeholder entries for Poker, Blackjack, and Roulette. Table wagering and gameplay are not implemented.

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
