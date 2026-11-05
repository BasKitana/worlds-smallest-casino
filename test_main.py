import subprocess
import sys
import unittest
from pathlib import Path


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
        for table in ("Poker", "Blackjack"):
            self.assertIn(f"{table} — Placeholder", output)
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


if __name__ == "__main__":
    unittest.main()
