import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import screen
from poker import dealer_discards, hand_name, poker, rank_hand, resolve
from test_screen import PlainScreenTest


def cards(ranks, suits="♣♦♥♠♣"):
    return list(zip(ranks, suits))


class HandRankingTest(unittest.TestCase):
    def test_all_hand_categories(self):
        examples = [
            (cards([14, 13, 12, 11, 9]), "high card"),
            (cards([14, 14, 12, 9, 7]), "one pair"),
            (cards([14, 14, 12, 12, 7]), "two pair"),
            (cards([14, 14, 14, 12, 7]), "three of a kind"),
            (cards([2, 3, 4, 5, 6]), "straight"),
            (cards([14, 11, 9, 6, 2], "♣♣♣♣♣"), "flush"),
            (cards([14, 14, 14, 12, 12]), "full house"),
            (cards([14, 14, 14, 14, 12]), "four of a kind"),
            (cards([10, 11, 12, 13, 14], "♠♠♠♠♠"), "straight flush"),
        ]
        for hand, expected in examples:
            with self.subTest(expected=expected):
                self.assertEqual(hand_name(hand), expected)

    def test_ace_low_straight_and_kicker_tiebreaks(self):
        wheel = cards([14, 2, 3, 4, 5])
        six_high = cards([2, 3, 4, 5, 6])
        self.assertEqual(rank_hand(wheel), (4, 5))
        self.assertGreater(rank_hand(six_high), rank_hand(wheel))
        self.assertGreater(
            rank_hand(cards([9, 9, 14, 8, 7])),
            rank_hand(cards([9, 9, 13, 12, 11])),
        )

    def test_category_ranks_and_tie_breakers(self):
        self.assertGreater(
            rank_hand(cards([14, 11, 9, 6, 2], "♣♣♣♣♣")),
            rank_hand(cards([2, 3, 4, 5, 6])),
        )
        self.assertEqual(rank_hand(cards([13, 13, 8, 8, 2])), rank_hand(cards([13, 13, 8, 8, 2])))


class PokerRoundTest(PlainScreenTest):
    def test_dealer_keeps_pairs_and_discards_three_high_cards(self):
        pair = cards([10, 10, 14, 8, 4])
        self.assertEqual(dealer_discards(pair), [2, 3, 4])
        self.assertEqual(dealer_discards(cards([14, 11, 9, 6, 2])), [2, 3, 4])

    def test_resolve_win_loss_and_tie(self):
        strong = cards([10, 11, 12, 13, 14], "♠♠♠♠♠")
        weaker = cards([2, 3, 4, 5, 7])
        self.assertEqual(resolve(strong, weaker, 25), 25)
        self.assertEqual(resolve(weaker, strong, 25), -25)
        self.assertEqual(resolve(strong, strong, 25), 0)

    def test_round_displays_choices_and_updates_balance_on_win(self):
        player_hand = cards([10, 11, 12, 13, 14], "♠♠♠♠♠")
        dealer_hand = cards([2, 3, 4, 5, 7])
        replacements = cards([8, 9, 10], "♣♦♥")
        deck = list(reversed(player_hand + dealer_hand + replacements))
        output = io.StringIO()
        with patch("builtins.input", side_effect=["10", ""]), patch(
            "poker.create_deck", return_value=deck
        ), patch("poker.random.shuffle"), redirect_stdout(output):
            balance = poker(500)

        self.assertEqual(balance, 510)
        self.assertIn("discard and draw up to 3 cards", output.getvalue())
        self.assertIn(
            "Your hand: 1. 10♠ 2. J♠ 3. Q♠ 4. K♠ 5. A♠  (straight flush)", output.getvalue()
        )
        latest = screen.history[0]
        self.assertTrue(latest["outcome"].startswith("Your straight flush beats the dealer's"))
        self.assertTrue(latest["outcome"].endswith("You win $10!"))
        self.assertEqual(latest["details"][0], "You:    10♠ J♠ Q♠ K♠ A♠ (straight flush)")
        self.assertTrue(latest["details"][1].startswith("Dealer: "))

    def test_invalid_discard_redraws_with_error(self):
        output = io.StringIO()
        with patch("builtins.input", side_effect=["10", "1,2,3,4", "9", ""]), redirect_stdout(
            output
        ):
            poker(500)

        output = output.getvalue()
        self.assertEqual(
            output.count("> Invalid choice. Enter up to 3 different positions from 1 to 5."), 2
        )
        self.assertEqual(output.count("Your hand:"), 3)

    def test_cancelled_bet_leaves_the_table(self):
        output = io.StringIO()
        with patch("builtins.input", return_value=""), redirect_stdout(output):
            balance = poker(500)
        self.assertIsNone(balance)


if __name__ == "__main__":
    unittest.main()
