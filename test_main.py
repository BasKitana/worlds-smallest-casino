import io
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from main import garage


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
        for table, table_choice in (("poker", "1"), ("roulette", "3")):
            for start, result, message in (
                (2499, 2500, "Tier up! Your balance moved to Tier 2."),
                (2500, 2499, "Tier down. Your balance moved to Tier 1."),
            ):
                with self.subTest(table=table, start=start):
                    output = io.StringIO()
                    with patch("builtins.input", side_effect=[table_choice, "4"]), patch(
                        f"main.{table}", return_value=result
                    ), redirect_stdout(output):
                        garage(start)

                    self.assertIn(message, output.getvalue())
                    self.assertIn(f"Garage Casino — Balance: ${result}", output.getvalue())


if __name__ == "__main__":
    unittest.main()
