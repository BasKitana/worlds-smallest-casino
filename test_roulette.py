# Roulette tests check the wheel, wager selection, payouts, and complete spins.
# Tests supply keyboard responses and fixed spin results to avoid randomness.
import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import screen
from roulette import BLACK, RED, choose_wager, color, resolve, roulette
from test_screen import PlainScreenTest


class WheelTest(unittest.TestCase):
    # The 36 nonzero numbers must split into 18 red and 18 black pockets.
    def test_red_and_black_split_one_to_thirty_six(self):
        self.assertEqual(len(RED), 18)
        self.assertEqual(len(BLACK), 18)
        # | takes the set union: together the colors must cover every number 1-36.
        self.assertEqual(RED | BLACK, set(range(1, 37)))

    def test_colors(self):
        # 0 is the green pocket; 1 is red and 2 is black on a European wheel.
        self.assertEqual(color(0), "Green")
        self.assertEqual(color(1), "Red")
        self.assertEqual(color(2), "Black")


class ChooseWagerTest(PlainScreenTest):
    # Check menu input independently from bets and wheel outcomes.
    def choose(self, inputs):
        # Feed a response per input() call and capture printed prompts/messages.
        # The with block restores normal input and stdout when it finishes.
        output = io.StringIO()
        with patch("builtins.input", side_effect=inputs), redirect_stdout(output):
            wager = choose_wager()
        return wager, output.getvalue()

    def test_single_number(self):
        # Option 1, then 17: a single-number wager that pays 35 to 1.
        wager, _ = self.choose(["1", "17"])

        self.assertEqual(wager, ("Number 17", {17}, 35))

    def test_single_number_rejects_out_of_range(self):
        # Select a number bet, reject 37 and text, then accept the valid edge value 0.
        wager, output = self.choose(["1", "37", "abc", "0"])

        self.assertEqual(wager, ("Number 0", {0}, 35))
        self.assertIn("Please enter a number from 0 to 36.", output)

    def test_outside_wager(self):
        # Option 2 returns the preset Red wager at once, with no follow-up question.
        wager, _ = self.choose(["2"])

        self.assertEqual(wager, ("Red", RED, 1))

    def test_dozen(self):
        # Menu option 8, then dozen 2: range(13, 25) includes 13 through 24.
        wager, _ = self.choose(["8", "2"])

        self.assertEqual(wager, ("Dozen 13-24", set(range(13, 25)), 2))

    def test_blank_number_goes_back_to_wager_menu(self):
        # Cancel the number prompt, then choose Black from the redisplayed menu.
        wager, output = self.choose(["1", "", "3"])

        self.assertEqual(wager, ("Black", BLACK, 1))
        self.assertEqual(output.count("Roulette Wagers"), 2)

    def test_blank_dozen_goes_back_to_wager_menu(self):
        # Cancel the dozen prompt, then choose 9 to leave from the redrawn wager list.
        wager, output = self.choose(["8", "", "9"])

        self.assertIsNone(wager)
        self.assertEqual(output.count("Roulette Wagers"), 2)

    def test_invalid_choice_then_return(self):
        # 0 is not on the wager list, so it is rejected before 9 leaves the table.
        wager, output = self.choose(["0", "9"])

        self.assertIsNone(wager)
        self.assertIn("Please select 1 through 9.", output)


class ResolveTest(unittest.TestCase):
    # Wagers use (label, winning-number set, multiplier); payouts are net changes.
    def test_single_number_pays_35_to_1(self):
        # A $10 bet on 17: landing on 17 wins $350, and any other number loses the $10.
        self.assertEqual(resolve(("Number 17", {17}, 35), 10, 17), 350)
        self.assertEqual(resolve(("Number 17", {17}, 35), 10, 18), -10)

    def test_even_money_wagers(self):
        # 1 is red and 2 is black, so a $50 bet on red wins once and loses once.
        self.assertEqual(resolve(("Red", RED, 1), 50, 1), 50)
        self.assertEqual(resolve(("Red", RED, 1), 50, 2), -50)

    def test_dozen_pays_2_to_1(self):
        # 12 is in the first dozen (1-12), but 13 is not.
        wager = ("Dozen 1-12", set(range(1, 13)), 2)
        self.assertEqual(resolve(wager, 100, 12), 200)
        self.assertEqual(resolve(wager, 100, 13), -100)

    def test_zero_loses_outside_wagers(self):
        # Green zero belongs to neither red nor black, so both tested bets lose.
        for wager in (("Red", RED, 1), ("Black", BLACK, 1)):
            self.assertEqual(resolve(wager, 20, 0), -20)


class RouletteRoundTest(PlainScreenTest):
    # Combine menu selection, betting, settlement, and the recorded round result.
    def play(self, balance, inputs, number):
        # Replace spin() with a fixed number while the rest of the round runs normally.
        output = io.StringIO()
        with patch("builtins.input", side_effect=inputs), patch(
            "roulette.spin", return_value=number
        ), redirect_stdout(output):
            balance = roulette(balance)
        return balance, output.getvalue()

    def test_winning_round(self):
        # Choose Red and bet $100, with the wheel forced to land on 3 (red).
        balance, output = self.play(500, ["2", "100"], 3)

        self.assertEqual(balance, 600)
        self.assertIn("Wager: Red (pays 1 to 1)", output)
        latest = screen.history[0]
        self.assertEqual(latest["outcome"], "The ball lands on 3 Red. You win $100!")
        self.assertEqual(latest["details"], ["Wager: $100 on Red"])
        self.assertEqual(latest["kind"], "win")

    def test_losing_round(self):
        # Bet $50 on number 7, but force the wheel to land on 8.
        balance, output = self.play(500, ["1", "7", "50"], 8)

        self.assertEqual(balance, 450)
        latest = screen.history[0]
        self.assertEqual(latest["outcome"], "The ball lands on 8 Black. You lose $50.")
        self.assertEqual(latest["details"], ["Wager: $50 on Number 7"])
        self.assertEqual(latest["kind"], "lose")

    def test_return_before_betting_leaves_the_table(self):
        # Choosing 9 leaves before betting, so nothing is spun or recorded.
        balance, _ = self.play(500, ["9"], 0)

        self.assertIsNone(balance)
        self.assertEqual(screen.history, [])

    def test_cancel_bet_leaves_the_table(self):
        # Choose Red, then press Enter at the bet prompt to leave.
        balance, _ = self.play(500, ["2", ""], 0)

        self.assertIsNone(balance)


# Run this file's unittest cases when launched directly.
if __name__ == "__main__":
    unittest.main()
