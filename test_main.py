import io
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import main


ROOT = Path(__file__).resolve().parent


class CasinoMenuSmokeTest(unittest.TestCase):
    def run_game(self, inputs):
        return subprocess.run(
            [sys.executable, str(ROOT / "main.py")],
            input="\n".join(inputs) + "\n",
            text=True,
            capture_output=True,
            check=True,
            timeout=5,
        ).stdout

    def test_start_tables_return_with_balance_and_exit(self):
        output = self.run_game(
            ["1", "1", "", "2", "", "3", "9", "4"]
        )

        self.assertIn("Garage Casino — Balance: $500", output)
        self.assertIn("Poker — Five-Card Draw", output)
        self.assertIn("Blackjack\n", output)
        self.assertNotIn("Placeholder", output)
        self.assertIn("Roulette Wagers", output)
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
        for table, table_choice in (("poker", "1"), ("blackjack", "2"), ("roulette", "3")):
            for start, result, tier, limits, message in (
                (2499, 2500, 2, "$100-$500", "Tier up! Your balance moved to Tier 2."),
                (2500, 2499, 1, "$10-$100", "Tier down. Your balance moved to Tier 1."),
                (4999, 5000, 3, "$500-$2500", "Tier up! Your balance moved to Tier 3."),
                (5000, 4999, 2, "$100-$500", "Tier down. Your balance moved to Tier 2."),
                (2500, 2600, 2, "$100-$500", None),
            ):
                with self.subTest(table=table, start=start, result=result):
                    output = io.StringIO()
                    with patch("builtins.input", side_effect=[table_choice, "4"]), patch(
                        f"main.{table}", return_value=result
                    ), redirect_stdout(output):
                        main.garage(start)

                    output = output.getvalue()
                    if message:
                        self.assertIn(message, output)
                    else:
                        self.assertNotIn("Tier up!", output)
                        self.assertNotIn("Tier down.", output)
                    self.assertIn(f"Garage Casino — Balance: ${result}", output)
                    self.assertIn(f"Current tier: Tier {tier} — Bets: {limits}", output)


class GarageBalanceTest(unittest.TestCase):
    def play_garage(self, table, results, inputs):
        with patch.object(main, table, side_effect=results) as game, patch(
            "builtins.input", side_effect=inputs
        ), patch("builtins.print") as fake_print:
            main.garage(500)
        output = "\n".join(" ".join(map(str, call.args)) for call in fake_print.call_args_list)
        return game, output

    def test_garage_keeps_updated_balance_after_each_round(self):
        game, output = self.play_garage("roulette", [600, 450], ["3", "3", "4"])

        self.assertEqual([call.args for call in game.call_args_list], [(500,), (600,)])
        self.assertIn("Garage Casino — Balance: $600", output)
        self.assertIn("Garage Casino — Balance: $450", output)

    def test_reaching_winning_balance_ends_play_with_victory(self):
        game, output = self.play_garage("poker", [9_999, 10_000], ["1", "1"])

        self.assertEqual(game.call_count, 2)
        self.assertIn("You win the game", output)
        self.assertIn("$10000", output)
        self.assertNotIn("Goodbye!", output)

    def test_balance_above_winning_threshold_also_wins(self):
        _, output = self.play_garage("blackjack", [12_500], ["2"])

        self.assertIn("You win the game", output)


if __name__ == "__main__":
    unittest.main()
