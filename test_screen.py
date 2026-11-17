# Screen tests check the status line, recent-rounds history, notices, and colors.
# Most tests render with USE_ANSI off, so the output is plain text that is easy to compare.
import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import screen


class PlainScreenTest(unittest.TestCase):
    """Base class: plain text with no clearing or colors, and a fresh game state."""

    # Other test files extend this class so their output has no escape codes and
    # no rounds or notices left over from an earlier test.
    def setUp(self):
        # setUp runs before every test. patch.object switches USE_ANSI off, and
        # addCleanup restores the real value after the test, even if it fails.
        patcher = patch.object(screen, "USE_ANSI", False)
        patcher.start()
        self.addCleanup(patcher.stop)
        # Start with no history, and clear it again afterward for the next test.
        screen.reset()
        self.addCleanup(screen.reset)

    def render(self, *args, **kwargs):
        # Draw one screen and return its text. *args and **kwargs pass along whatever
        # arguments the test gives, exactly as if it had called screen.show() itself.
        output = io.StringIO()
        with redirect_stdout(output):
            screen.show(*args, **kwargs)
        return output.getvalue()


class StatusLineTest(PlainScreenTest):
    # The one-line summary at the top of every screen.
    def test_garage_status_has_balance_and_tier_without_round(self):
        # Menus show the balance and limits but no round number; note the comma in $1,250.
        self.assertEqual(
            screen.status_line("Garage", 1250),
            "WORLD'S SMALLEST CASINO | Garage | $1,250 | Tier 1: $10-$100",
        )

    def test_table_status_shows_the_round_being_played(self):
        # After one finished round, the table is on round 2. $6,000 is in Tier 3.
        screen.record_round("Blackjack", "Push.")
        self.assertEqual(
            screen.status_line("Blackjack", 6000, at_table=True),
            "WORLD'S SMALLEST CASINO | Blackjack | Round 2 | $6,000 | Tier 3: $500-$2,500",
        )

    def test_status_without_balance(self):
        # The start menu appears before the game has a balance.
        self.assertEqual(screen.status_line("Main menu"), "WORLD'S SMALLEST CASINO | Main menu")


class ShowTest(PlainScreenTest):
    # Whole screens: the order of sections and what each one contains.
    def test_body_follows_status_line(self):
        # With no rounds played yet, the history section is left out entirely.
        output = self.render("Garage", 500, ["1. Poker"])

        self.assertTrue(output.startswith("WORLD'S SMALLEST CASINO | Garage | $500"))
        self.assertIn("\n1. Poker\n", output)
        self.assertNotIn("Recent rounds", output)

    def test_notices_show_once(self):
        # The first screen shows the queued message; the second screen does not.
        screen.notice("Bet rejected. The minimum bet is $10.", "error")

        self.assertIn("> Bet rejected. The minimum bet is $10.", self.render("Poker", 500))
        self.assertNotIn("Bet rejected", self.render("Poker", 500))

    def test_history_is_newest_first_numbered_and_spaced(self):
        # Record rounds 1-4. Only the newest 3 fit, so round 1 drops off.
        for number in range(1, 5):
            screen.record_round("Roulette", f"Outcome {number}.", [f"Detail {number}"])

        output = self.render("Roulette", 500, at_table=True)

        # splitlines()[0] is the status line, which now shows the next round, 5.
        self.assertIn("Round 5", output.splitlines()[0])
        self.assertNotIn("Round 1 ·", output)
        # Newest first, details indented under their round, a blank line between rounds.
        self.assertIn(
            "Recent rounds\n\n"
            "  Round 4 · Roulette: Outcome 4.\n    Detail 4\n\n"
            "  Round 3 · Roulette: Outcome 3.\n    Detail 3\n\n"
            "  Round 2 · Roulette: Outcome 2.\n    Detail 2\n",
            output,
        )

    def test_reset_forgets_rounds_and_notices(self):
        # A new game must not show the last game's rounds or messages.
        screen.record_round("Poker", "Push.")
        screen.notice("Tier up!")
        screen.reset()

        output = self.render("Garage", 500)

        self.assertEqual(screen.current_round(), 1)
        self.assertNotIn("Recent rounds", output)
        self.assertNotIn("Tier up!", output)


class AnsiTest(PlainScreenTest):
    # Clearing and colors, which only happen when USE_ANSI is on.
    def test_plain_mode_prints_no_escape_codes(self):
        # Red cards and a colored win would add codes if USE_ANSI were on; "\033" starts every code.
        screen.record_round("Blackjack", "You win $50.", ["You: 10♥ 9♦ (19)"], "win")
        output = self.render("Blackjack", 500, ["Dealer: K♥ ??"])

        self.assertNotIn("\033", output)

    def test_ansi_mode_clears_and_colors(self):
        # Turn colors on for this test only; setUp's patch restores the setting afterward.
        screen.USE_ANSI = True
        screen.record_round("Blackjack", "You win $50.", [], "win")
        screen.notice("Tier up!", "tier")

        output = self.render("Blackjack", 500, ["You: 10♥ 9♠ (19)"])

        # The screen starts by clearing; wins are green (32), tier messages yellow (33),
        # and hearts red (31). Only the 10♥ is red, not the 9♠ next to it.
        self.assertTrue(output.startswith(screen.CLEAR_CODE))
        self.assertIn("\033[32m  Round 1 · Blackjack: You win $50.\033[0m", output)
        self.assertIn("\033[33m> Tier up!\033[0m", output)
        self.assertIn("You: \033[31m10♥\033[0m 9♠ (19)", output)
        # Removing the codes must leave exactly the plain-text screen.
        self.assertEqual(
            screen.strip_ansi(output),
            "WORLD'S SMALLEST CASINO | Blackjack | $500 | Tier 1: $10-$100\n"
            + "-" * screen.WIDTH
            + "\nRecent rounds\n\n  Round 1 · Blackjack: You win $50.\n"
            + "-" * screen.WIDTH
            + "\n> Tier up!\n\nYou: 10♥ 9♠ (19)\n",
        )

    def test_money_uses_thousands_separators(self):
        # Large amounts get a comma; small amounts are unchanged.
        self.assertEqual(screen.money(10000), "$10,000")
        self.assertEqual(screen.money(50), "$50")


# Run this file's unittest cases when launched directly.
if __name__ == "__main__":
    unittest.main()
