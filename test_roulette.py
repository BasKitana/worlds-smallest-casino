import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from roulette import BLACK, RED, choose_wager, color, resolve, roulette


class WheelTest(unittest.TestCase):
    def test_red_and_black_split_one_to_thirty_six(self):
        self.assertEqual(len(RED), 18)
        self.assertEqual(len(BLACK), 18)
        self.assertEqual(RED | BLACK, set(range(1, 37)))

    def test_colors(self):
        self.assertEqual(color(0), "Green")
        self.assertEqual(color(1), "Red")
        self.assertEqual(color(2), "Black")


class ChooseWagerTest(unittest.TestCase):
    def choose(self, inputs):
        output = io.StringIO()
        with patch("builtins.input", side_effect=inputs), redirect_stdout(output):
            wager = choose_wager()
        return wager, output.getvalue()

    def test_single_number(self):
        wager, _ = self.choose(["1", "17"])

        self.assertEqual(wager, ("Number 17", {17}, 35))

    def test_single_number_rejects_out_of_range(self):
        wager, output = self.choose(["1", "37", "abc", "0"])

        self.assertEqual(wager, ("Number 0", {0}, 35))
        self.assertIn("Please enter a number from 0 to 36.", output)

    def test_outside_wager(self):
        wager, _ = self.choose(["2"])

        self.assertEqual(wager, ("Red", RED, 1))

    def test_dozen(self):
        wager, _ = self.choose(["8", "2"])

        self.assertEqual(wager, ("Dozen 13-24", set(range(13, 25)), 2))

    def test_blank_number_goes_back_to_wager_menu(self):
        wager, output = self.choose(["1", "", "3"])

        self.assertEqual(wager, ("Black", BLACK, 1))
        self.assertEqual(output.count("Roulette Wagers"), 2)

    def test_blank_dozen_goes_back_to_wager_menu(self):
        wager, output = self.choose(["8", "", "9"])

        self.assertIsNone(wager)
        self.assertEqual(output.count("Roulette Wagers"), 2)

    def test_invalid_choice_then_return(self):
        wager, output = self.choose(["0", "9"])

        self.assertIsNone(wager)
        self.assertIn("Please select 1 through 9.", output)


class ResolveTest(unittest.TestCase):
    def test_single_number_pays_35_to_1(self):
        self.assertEqual(resolve(("Number 17", {17}, 35), 10, 17), 350)
        self.assertEqual(resolve(("Number 17", {17}, 35), 10, 18), -10)

    def test_even_money_wagers(self):
        self.assertEqual(resolve(("Red", RED, 1), 50, 1), 50)
        self.assertEqual(resolve(("Red", RED, 1), 50, 2), -50)

    def test_dozen_pays_2_to_1(self):
        wager = ("Dozen 1-12", set(range(1, 13)), 2)
        self.assertEqual(resolve(wager, 100, 12), 200)
        self.assertEqual(resolve(wager, 100, 13), -100)

    def test_zero_loses_outside_wagers(self):
        for wager in (("Red", RED, 1), ("Black", BLACK, 1)):
            self.assertEqual(resolve(wager, 20, 0), -20)


class RouletteRoundTest(unittest.TestCase):
    def play(self, balance, inputs, number):
        output = io.StringIO()
        with patch("builtins.input", side_effect=inputs), patch(
            "roulette.spin", return_value=number
        ), redirect_stdout(output):
            balance = roulette(balance)
        return balance, output.getvalue()

    def test_winning_round(self):
        balance, output = self.play(500, ["2", "100"], 3)

        self.assertEqual(balance, 600)
        self.assertIn("The ball lands on 3 Red.", output)
        self.assertIn("You win $100!", output)
        self.assertIn("New balance: $600", output)

    def test_losing_round(self):
        balance, output = self.play(500, ["1", "7", "50"], 8)

        self.assertEqual(balance, 450)
        self.assertIn("You bet $50 on Number 7.", output)
        self.assertIn("You lose $50.", output)

    def test_return_before_betting_leaves_the_table(self):
        balance, _ = self.play(500, ["9"], 0)

        self.assertIsNone(balance)

    def test_cancel_bet_leaves_the_table(self):
        balance, _ = self.play(500, ["2", ""], 0)

        self.assertIsNone(balance)


if __name__ == "__main__":
    unittest.main()
