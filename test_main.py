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
import screen
from test_screen import PlainScreenTest


# Locate main.py relative to this file, regardless of the shell's working directory.
ROOT = Path(__file__).resolve().parent


# The start of the garage's status line, shared by many assertions below.
GARAGE = "WORLD'S SMALLEST CASINO | Garage"


def run_game(inputs, raw=False):
    """Run the real game in a subprocess, with ANSI codes stripped unless raw is set."""
    # Use this test runner's Python and feed each list entry as one typed line.
    # Capture output for assertions; fail on a crash or a wait longer than 5 seconds.
    output = subprocess.run(
        [sys.executable, str(ROOT / "main.py")],
        input="\n".join(inputs) + "\n",
        text=True,
        capture_output=True,
        check=True,
        timeout=5,
    ).stdout
    return output if raw else screen.strip_ansi(output)


class CasinoMenuSmokeTest(PlainScreenTest):
    # Smoke tests exercise the real command-line program as a separate process.
    def run_game(self, inputs):
        # Kept as a method so the tests below can call self.run_game().
        return run_game(inputs)

    def test_start_tables_return_with_balance_and_exit(self):
        # Start, cancel Poker, cancel Blackjack, leave Roulette, then exit the garage.
        output = self.run_game(
            ["1", "1", "", "2", "", "3", "9", "5"]
        )

        self.assertIn("| Poker | Round 1 | $500 |", output)
        self.assertIn("Five-Card Draw: discard and draw up to 3 cards", output)
        self.assertIn("| Blackjack | Round 1 | $500 |", output)
        self.assertNotIn("Placeholder", output)
        self.assertIn("Roulette Wagers", output)
        # The garage appears initially and after leaving each of the three tables.
        self.assertEqual(output.count(f"{GARAGE} | $500 | Tier 1: $10-$100"), 4)
        self.assertEqual(output.count("| Main menu"), 1)
        self.assertIn("Goodbye! You leave the casino with $500.", output)

    def test_every_screen_clears_the_terminal(self):
        # Start, open How to Play, read Blackjack's instructions, go back, and exit.
        # raw=True keeps the ANSI codes so the clears themselves can be counted.
        raw = run_game(["1", "4", "2", "4", "5"], raw=True)

        # Main menu, garage, two How to Play screens, garage, then the goodbye screen.
        self.assertEqual(raw.count(screen.CLEAR_CODE), 6)
        self.assertEqual(raw.count(screen.CLEAR_CODE + "\033[1mWORLD'S SMALLEST CASINO"), 5)
        self.assertTrue(raw.endswith(screen.CLEAR_CODE + "Goodbye! You leave the casino with $500.\n"))

    def test_invalid_input_and_root_exit(self):
        # An unknown choice at the start menu shows an error, then 2 exits.
        output = self.run_game(["invalid", "2"])

        self.assertIn("Invalid choice. Please select 1 or 2.", output)
        self.assertIn("Goodbye!", output)

    def test_invalid_input_and_garage_exit(self):
        # Start, type an unknown choice in the garage, then exit. The garage is drawn
        # twice: once before the error and once with it.
        output = self.run_game(["1", "invalid", "5"])

        self.assertIn("> Invalid choice. Please select 1, 2, 3, 4, or 5.", output)
        self.assertEqual(output.count(GARAGE), 2)
        self.assertEqual(output.count("| Main menu"), 1)
        self.assertEqual(output.count("Goodbye!"), 1)

    def test_garage_displays_tier_changes_after_table_returns(self):
        # Exercise all tables across both tier thresholds, plus an unchanged tier.
        for table, table_choice in (("poker", "1"), ("blackjack", "2"), ("roulette", "3")):
            for start, result, tier, limits, message in (
                (2499, 2500, 2, "$100-$500", "Tier up! Your balance moved to Tier 2."),
                (2500, 2499, 1, "$10-$100", "Tier down. Your balance moved to Tier 1."),
                (4999, 5000, 3, "$500-$2,500", "Tier up! Your balance moved to Tier 3."),
                (5000, 4999, 2, "$100-$500", "Tier down. Your balance moved to Tier 2."),
                (2500, 2600, 2, "$100-$500", None),
            ):
                with self.subTest(table=table, start=start, result=result):
                    # subTest labels each case so a failure identifies its table/balance.
                    output = io.StringIO()
                    # Replace the table function where main looks it up: one round
                    # returns a known balance, then None means the player left.
                    # input's side_effect entries are consumed one call at a time;
                    # redirect_stdout captures print() text in an in-memory buffer.
                    with patch("builtins.input", side_effect=[table_choice, "5"]), patch(
                        f"main.{table}", side_effect=[result, None]
                    ), redirect_stdout(output):
                        main.garage(start)

                    output = output.getvalue()
                    if message:
                        self.assertEqual(output.count(f"> {message}"), 1)
                    else:
                        # Moving within a tier must not announce a tier change.
                        self.assertNotIn("Tier up!", output)
                        self.assertNotIn("Tier down.", output)
                    self.assertIn(
                        f"{GARAGE} | {screen.money(result)} | Tier {tier}: {limits}", output
                    )


class GarageBalanceTest(PlainScreenTest):
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

    def test_table_replays_with_updated_balance_until_player_leaves(self):
        # Each round must receive the previous round's result: $500, then $600, then $450.
        game, output = self.play_garage("roulette", [600, 450, None], ["3", "5"])

        self.assertEqual(
            [call.args for call in game.call_args_list], [(500,), (600,), (450,)]
        )
        self.assertNotIn(f"{GARAGE} | $600", output)
        self.assertIn(f"{GARAGE} | $450", output)

    def test_leaving_a_table_without_playing_keeps_balance(self):
        # Enter Blackjack but leave at once (None), so no round is played and the garage
        # is drawn again at $500.
        game, output = self.play_garage("blackjack", [None], ["2", "5"])

        self.assertEqual(game.call_count, 1)
        self.assertEqual(output.count(f"{GARAGE} | $500"), 2)

    def test_tier_change_is_shown_between_rounds_at_the_table(self):
        # Round 1 reaches $2,500 (Tier 2) and round 2 stays in Tier 2, so the message
        # appears once, between rounds, without returning to the garage.
        game, output = self.play_garage("roulette", [2_500, 2_600, None], ["3", "5"])

        self.assertEqual(game.call_count, 3)
        self.assertEqual(output.count("Tier up! Your balance moved to Tier 2."), 1)

    def test_reaching_winning_balance_ends_play_with_victory(self):
        # $9,999 keeps playing; exactly $10,000 ends without an extra exit prompt.
        game, output = self.play_garage("poker", [9_999, 10_000], ["1"])

        self.assertEqual(game.call_count, 2)
        self.assertIn("You win the game", output)
        self.assertIn("You reached $10,000", output)
        self.assertNotIn("Goodbye!", output)

    def test_balance_above_winning_threshold_also_wins(self):
        # A large win may skip past the target and must still count as victory.
        _, output = self.play_garage("blackjack", [12_500], ["2"])

        self.assertIn("You win the game", output)


class HowToPlayTest(PlainScreenTest):
    # Open How to Play from the garage and check the instructions for each table.
    def run_menu(self, inputs, balance=500):
        # Run the garage with scripted choices and return everything it printed.
        output = io.StringIO()
        with patch("builtins.input", side_effect=inputs), redirect_stdout(output):
            main.garage(balance)
        return output.getvalue()

    def test_shows_instructions_for_each_selected_table(self):
        # Open How to Play, view all three tables, go back, then exit. Every table's
        # instructions end with the same betting reminders, so that line appears 3 times.
        output = self.run_menu(["4", "1", "2", "3", "4", "5"])

        self.assertIn("Poker — Five-Card Draw\n- Make a better five-card poker hand", output)
        self.assertIn("Type h to hit (take a card) or s to stand", output)
        self.assertIn("A single number pays 35 to 1", output)
        self.assertEqual(output.count("Press Enter at the bet prompt to return to the garage."), 3)
        self.assertEqual(output.count(f"{GARAGE} | $500"), 2)
        self.assertEqual(output.count("Goodbye!"), 1)

    def test_betting_info_uses_current_tier(self):
        # At $3,000 the reminders use Tier 2's limits. A blank entry leaves How to Play.
        output = self.run_menu(["4", "2", "", "5"], balance=3000)

        self.assertIn("Your balance of $3000 is Tier 2: bets from $100 to $500.", output)

    def test_invalid_choice_and_blank_return(self):
        # x is rejected, which redraws How to Play once more; Enter then goes back.
        output = self.run_menu(["4", "x", "", "5"])

        self.assertIn("> Invalid choice. Please select 1, 2, 3, or 4.", output)
        self.assertEqual(output.count("| How to Play |"), 2)
        self.assertEqual(output.count("Goodbye!"), 1)

    def test_how_to_play_from_the_real_game(self):
        # The same menu in the real program, as started with python3 main.py.
        output = run_game(["1", "4", "2", "4", "5"])

        self.assertIn("| How to Play |", output)
        self.assertIn("The dealer draws until reaching 17 or more.", output)


# This also lets you run just this file with python3 test_main.py.
if __name__ == "__main__":
    unittest.main()
