# Menu tests check navigation, displayed balances, and tier-change notifications.
# unittest discovers test_* methods; assertions describe the expected behavior.
import io
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import main


# Locate main.py relative to this file, regardless of the shell's working directory.
ROOT = Path(__file__).resolve().parent


class CasinoMenuSmokeTest(unittest.TestCase):
    # Smoke tests exercise the real command-line program as a separate process.
    def run_game(self, inputs):
        # Use this test runner's Python and feed each list entry as one typed line.
        # Capture output for assertions; fail on a crash or a wait longer than 5 seconds.
        return subprocess.run(
            [sys.executable, str(ROOT / "main.py")],
            input="\n".join(inputs) + "\n",
            text=True,
            capture_output=True,
            check=True,
            timeout=5,
        ).stdout

    def test_start_tables_return_with_balance_and_exit(self):
        # Start, cancel Poker, cancel Blackjack, leave Roulette, then exit the garage.
        output = self.run_game(
            ["1", "1", "", "2", "", "3", "9", "4"]
        )

        self.assertIn("Garage Casino — Balance: $500", output)
        self.assertIn("Poker — Five-Card Draw", output)
        self.assertIn("Blackjack\n", output)
        self.assertNotIn("Placeholder", output)
        self.assertIn("Roulette Wagers", output)
        # The garage appears initially and after each of the three table visits.
        self.assertEqual(output.count("Garage Casino — Balance: $500"), 4)
        self.assertEqual(output.count("World's Smallest Casino"), 1)
        self.assertEqual(output.count("Goodbye!"), 1)

    def test_invalid_input_and_root_exit(self):
        output = self.run_game(["invalid", "2"])

        self.assertIn("Invalid choice. Please select 1 or 2.", output)
        self.assertIn("Goodbye!", output)

    def test_invalid_input_and_garage_exit(self):
        output = self.run_game(["1", "invalid", "4"])

        self.assertIn("Invalid choice. Please select 1, 2, 3, or 4.", output)
        self.assertIn("Garage Casino — Balance: $500", output)
        self.assertEqual(output.count("World's Smallest Casino"), 1)
        self.assertEqual(output.count("Goodbye!"), 1)

    def test_garage_displays_tier_changes_after_table_returns(self):
        # Exercise all tables across both tier thresholds, plus an unchanged tier.
        for table, table_choice in (("poker", "1"), ("blackjack", "2"), ("roulette", "3")):
            for start, result, tier, limits, message in (
                (2499, 2500, 2, "$100-$500", "Tier up! Your balance moved to Tier 2."),
                (2500, 2499, 1, "$10-$100", "Tier down. Your balance moved to Tier 1."),
                (4999, 5000, 3, "$500-$2500", "Tier up! Your balance moved to Tier 3."),
                (5000, 4999, 2, "$100-$500", "Tier down. Your balance moved to Tier 2."),
                (2500, 2600, 2, "$100-$500", None),
            ):
                with self.subTest(table=table, start=start, result=result):
                    # subTest labels each case so a failure identifies its table/balance.
                    output = io.StringIO()
                    # Replace the table function where main looks it up, supplying a
                    # known returned balance without needing a random winning round.
                    # input's side_effect entries are consumed one call at a time;
                    # redirect_stdout captures print() text in an in-memory buffer.
                    with patch("builtins.input", side_effect=[table_choice, "4"]), patch(
                        f"main.{table}", return_value=result
                    ), redirect_stdout(output):
                        main.garage(start)

                    output = output.getvalue()
                    if message:
                        self.assertIn(message, output)
                    else:
                        # Moving within a tier must not announce a tier change.
                        self.assertNotIn("Tier up!", output)
                        self.assertNotIn("Tier down.", output)
                    self.assertIn(f"Garage Casino — Balance: ${result}", output)
                    self.assertIn(f"Current tier: Tier {tier} — Bets: {limits}", output)


class GarageBalanceTest(unittest.TestCase):
    # Check balance persistence between rounds and the $10,000 victory condition.
    def play_garage(self, table, results, inputs):
        # Replace the selected table with successive returned balances. Record print
        # calls and table calls so tests can inspect messages and incoming balances.
        with patch.object(main, table, side_effect=results) as game, patch(
            "builtins.input", side_effect=inputs
        ), patch("builtins.print") as fake_print:
            main.garage(500)
        # Reconstruct printed lines by converting each recorded argument to text.
        output = "\n".join(" ".join(map(str, call.args)) for call in fake_print.call_args_list)
        return game, output

    def test_garage_keeps_updated_balance_after_each_round(self):
        # The second round must receive the first round's $600 result, not $500.
        game, output = self.play_garage("roulette", [600, 450], ["3", "3", "4"])

        self.assertEqual([call.args for call in game.call_args_list], [(500,), (600,)])
        self.assertIn("Garage Casino — Balance: $600", output)
        self.assertIn("Garage Casino — Balance: $450", output)

    def test_reaching_winning_balance_ends_play_with_victory(self):
        # $9,999 continues play; exactly $10,000 ends without an extra exit prompt.
        game, output = self.play_garage("poker", [9_999, 10_000], ["1", "1"])

        self.assertEqual(game.call_count, 2)
        self.assertIn("You win the game", output)
        self.assertIn("$10000", output)
        self.assertNotIn("Goodbye!", output)

    def test_balance_above_winning_threshold_also_wins(self):
        # A large win may skip past the target and must still count as victory.
        _, output = self.play_garage("blackjack", [12_500], ["2"])

        self.assertIn("You win the game", output)


# This also lets you run just this file with python3 test_main.py.
if __name__ == "__main__":
    unittest.main()
