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
            ["1", "1", "", "2", "", "3", "9", "5"]
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
        output = self.run_game(["1", "invalid", "5"])

        self.assertIn("Invalid choice. Please select 1, 2, 3, 4, or 5.", output)
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
                    with patch("builtins.input", side_effect=[table_choice, "5"]), patch(
                        f"main.{table}", side_effect=[result, None]
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

    def test_table_replays_with_updated_balance_until_player_leaves(self):
        game, output = self.play_garage("roulette", [600, 450, None], ["3", "5"])

        self.assertEqual(
            [call.args for call in game.call_args_list], [(500,), (600,), (450,)]
        )
        self.assertNotIn("Garage Casino — Balance: $600", output)
        self.assertIn("Garage Casino — Balance: $450", output)

    def test_leaving_a_table_without_playing_keeps_balance(self):
        game, output = self.play_garage("blackjack", [None], ["2", "5"])

        self.assertEqual(game.call_count, 1)
        self.assertEqual(output.count("Garage Casino — Balance: $500"), 2)

    def test_tier_change_is_shown_between_rounds_at_the_table(self):
        game, output = self.play_garage("roulette", [2_500, 2_600, None], ["3", "5"])

        self.assertEqual(game.call_count, 3)
        self.assertEqual(output.count("Tier up! Your balance moved to Tier 2."), 1)

    def test_reaching_winning_balance_ends_play_with_victory(self):
        game, output = self.play_garage("poker", [9_999, 10_000], ["1"])

        self.assertEqual(game.call_count, 2)
        self.assertIn("You win the game", output)
        self.assertIn("$10000", output)
        self.assertNotIn("Goodbye!", output)

    def test_balance_above_winning_threshold_also_wins(self):
        _, output = self.play_garage("blackjack", [12_500], ["2"])

        self.assertIn("You win the game", output)


class HowToPlayTest(unittest.TestCase):
    def run_menu(self, inputs, balance=500):
        output = io.StringIO()
        with patch("builtins.input", side_effect=inputs), redirect_stdout(output):
            main.garage(balance)
        return output.getvalue()

    def test_shows_instructions_for_each_selected_table(self):
        output = self.run_menu(["4", "1", "2", "3", "4", "5"])

        self.assertIn("Poker — Five-Card Draw\n- Make a better five-card poker hand", output)
        self.assertIn("Type h to hit (take a card) or s to stand", output)
        self.assertIn("A single number pays 35 to 1", output)
        self.assertEqual(output.count("Press Enter at the bet prompt to return to the garage."), 3)
        self.assertEqual(output.count("Garage Casino — Balance: $500"), 2)
        self.assertEqual(output.count("Goodbye!"), 1)

    def test_betting_info_uses_current_tier(self):
        output = self.run_menu(["4", "2", "", "5"], balance=3000)

        self.assertIn("Your balance of $3000 is Tier 2: bets from $100 to $500.", output)

    def test_invalid_choice_and_blank_return(self):
        output = self.run_menu(["4", "x", "", "5"])

        self.assertIn("Invalid choice. Please select 1, 2, 3, or 4.", output)
        self.assertEqual(output.count("How to Play"), 2)
        self.assertEqual(output.count("Goodbye!"), 1)

    def test_how_to_play_from_the_real_game(self):
        output = CasinoMenuSmokeTest().run_game(["1", "4", "2", "4", "5"])

        self.assertIn("How to Play", output)
        self.assertIn("The dealer draws until reaching 17 or more.", output)


if __name__ == "__main__":
    unittest.main()
