import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from betting import bet_limits, get_bet, validate_bet


class BetLimitsTest(unittest.TestCase):
    def test_tier_boundaries(self):
        self.assertEqual(bet_limits(500), (10, 100))
        self.assertEqual(bet_limits(2499), (10, 100))
        self.assertEqual(bet_limits(2500), (100, 500))
        self.assertEqual(bet_limits(4999), (100, 500))
        self.assertEqual(bet_limits(5000), (500, 2500))
        self.assertEqual(bet_limits(9999), (500, 2500))


class ValidateBetTest(unittest.TestCase):
    def test_accepts_bets_within_limits(self):
        self.assertIsNone(validate_bet(10, 500))
        self.assertIsNone(validate_bet(100, 500))
        self.assertIsNone(validate_bet(500, 3000))
        self.assertIsNone(validate_bet(2500, 6000))

    def test_rejects_bet_below_minimum(self):
        self.assertEqual(validate_bet(9, 500), "The minimum bet is $10.")
        self.assertEqual(validate_bet(99, 3000), "The minimum bet is $100.")

    def test_rejects_bet_above_maximum(self):
        self.assertEqual(validate_bet(101, 500), "The maximum bet is $100.")
        self.assertEqual(validate_bet(2501, 6000), "The maximum bet is $2500.")

    def test_rejects_bet_greater_than_balance(self):
        self.assertEqual(
            validate_bet(50, 40), "You only have $40. You cannot bet $50."
        )


class GetBetTest(unittest.TestCase):
    def run_get_bet(self, balance, inputs):
        output = io.StringIO()
        with patch("builtins.input", side_effect=inputs), redirect_stdout(output):
            amount = get_bet(balance)
        return amount, output.getvalue()

    def test_reprompts_until_valid_bet(self):
        amount, output = self.run_get_bet(500, ["abc", "5", "200", "50"])

        self.assertEqual(amount, 50)
        self.assertIn("Please enter a whole dollar amount.", output)
        self.assertIn("Bet rejected. The minimum bet is $10.", output)
        self.assertIn("Bet rejected. The maximum bet is $100.", output)
        self.assertIn("Bet accepted: $50", output)

    def test_shows_current_tier_limits(self):
        _, output = self.run_get_bet(3000, ["100"])

        self.assertIn("Balance: $3000 — Bets: $100-$500", output)

    def test_blank_input_cancels(self):
        amount, _ = self.run_get_bet(500, [""])

        self.assertIsNone(amount)


if __name__ == "__main__":
    unittest.main()
