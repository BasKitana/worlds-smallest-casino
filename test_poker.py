# Poker tests check hand strength, tie-breakers, dealer choices, and round payouts.
# Numeric ranks use 11=jack, 12=queen, 13=king, 14=ace, just like poker.py.
import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from poker import dealer_discards, hand_name, poker, rank_hand, resolve


def cards(ranks, suits="♣♦♥♠♣"):
    # zip pairs each rank with the corresponding suit; list builds a reusable hand.
    # The default suits avoid accidental flushes; repeated suits create flush fixtures.
    return list(zip(ranks, suits))


class HandRankingTest(unittest.TestCase):
    # Call scoring directly so shuffled deals and user choices cannot affect results.
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
        # Each example supplies one category; subTest reports which category failed.
        for hand, expected in examples:
            with self.subTest(expected=expected):
                self.assertEqual(hand_name(hand), expected)

    def test_ace_low_straight_and_kicker_tiebreaks(self):
        # The "wheel" is A-2-3-4-5, which loses to a six-high straight.
        wheel = cards([14, 2, 3, 4, 5])
        six_high = cards([2, 3, 4, 5, 6])
        self.assertEqual(rank_hand(wheel), (4, 5))
        self.assertGreater(rank_hand(six_high), rank_hand(wheel))
        # Equal pairs of nines are decided by the next highest card: ace beats king.
        self.assertGreater(
            rank_hand(cards([9, 9, 14, 8, 7])),
            rank_hand(cards([9, 9, 13, 12, 11])),
        )

    def test_category_ranks_and_tie_breakers(self):
        # A flush outranks a straight; identical two-pair hands produce equal scores.
        self.assertGreater(
            rank_hand(cards([14, 11, 9, 6, 2], "♣♣♣♣♣")),
            rank_hand(cards([2, 3, 4, 5, 6])),
        )
        self.assertEqual(rank_hand(cards([13, 13, 8, 8, 2])), rank_hand(cards([13, 13, 8, 8, 2])))


class PokerRoundTest(unittest.TestCase):
    # Verify the dealer strategy and how results affect the player's balance.
    def test_dealer_keeps_pairs_and_discards_three_high_cards(self):
        # Discard indexes start at 0. Keep the pair, or the top two unmatched cards.
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
        # Give the player a royal flush and the dealer a hand that draws three cards.
        player_hand = cards([10, 11, 12, 13, 14], "♠♠♠♠♠")
        dealer_hand = cards([2, 3, 4, 5, 7])
        replacements = cards([8, 9, 10], "♣♦♥")
        # Reverse the deal order because pop() draws from the list's end.
        deck = list(reversed(player_hand + dealer_hand + replacements))
        output = io.StringIO()
        # Bet $10, stand, then return to the garage. Replace deck creation and disable
        # shuffling so the prepared deal survives; capture print() output for assertions.
        with patch("builtins.input", side_effect=["10", "", ""]), patch(
            "poker.create_deck", return_value=deck
        ), patch("poker.random.shuffle"), redirect_stdout(output):
            balance = poker(500)

        self.assertEqual(balance, 510)
        self.assertIn("discard and draw up to 3 cards", output.getvalue())
        self.assertIn("You win $10!", output.getvalue())
        self.assertIn("New balance: $510", output.getvalue())

    def test_cancelled_bet_keeps_balance(self):
        # A blank bet leaves before any cards are dealt or money changes hands.
        output = io.StringIO()
        with patch("builtins.input", return_value=""), redirect_stdout(output):
            balance = poker(500)
        self.assertEqual(balance, 500)


# Run this file's unittest cases when launched directly.
if __name__ == "__main__":
    unittest.main()
