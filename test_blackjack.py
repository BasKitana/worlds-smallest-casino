import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from blackjack import (
    BLACKJACK,
    LOSE,
    PUSH,
    WIN,
    blackjack,
    deal_initial_cards,
    determine_result,
    format_hand,
    hand_value,
    is_blackjack,
    net_winnings,
    new_deck,
)
from main import garage
import screen
from test_screen import PlainScreenTest


def hand(*ranks):
    return [(rank, "♠") for rank in ranks]


def stacked_deck(*ranks):
    """Build a deck that deals the given ranks in order."""
    return list(reversed(hand(*ranks)))


class DealTest(unittest.TestCase):
    def test_new_deck_has_52_unique_cards(self):
        deck = new_deck()

        self.assertEqual(len(deck), 52)
        self.assertEqual(len(set(deck)), 52)

    def test_deals_two_cards_each_alternating_from_player(self):
        deck = stacked_deck("2", "3", "4", "5", "6")

        player, dealer = deal_initial_cards(deck)

        self.assertEqual(player, hand("2", "4"))
        self.assertEqual(dealer, hand("3", "5"))
        self.assertEqual(deck, hand("6"))


class HandValueTest(unittest.TestCase):
    def test_number_and_face_cards(self):
        self.assertEqual(hand_value(hand("2", "10")), 12)
        self.assertEqual(hand_value(hand("J", "Q", "K")), 30)

    def test_ace_counts_as_eleven_or_one(self):
        self.assertEqual(hand_value(hand("A", "6")), 17)
        self.assertEqual(hand_value(hand("A", "6", "10")), 17)
        self.assertEqual(hand_value(hand("A", "A")), 12)
        self.assertEqual(hand_value(hand("A", "A", "9")), 21)
        self.assertEqual(hand_value(hand("A", "A", "K", "K")), 22)

    def test_blackjack_needs_exactly_two_cards(self):
        self.assertTrue(is_blackjack(hand("A", "K")))
        self.assertFalse(is_blackjack(hand("7", "7", "7")))

    def test_format_hand(self):
        self.assertEqual(format_hand([("A", "♠"), ("10", "♥")]), "A♠ 10♥")


class DetermineResultTest(unittest.TestCase):
    def test_results(self):
        cases = [
            (hand("K", "Q", "2"), hand("K", "2"), LOSE),
            (hand("K", "Q", "2"), hand("K", "Q", "5"), LOSE),
            (hand("A", "K"), hand("A", "Q"), PUSH),
            (hand("A", "K"), hand("7", "7", "7"), BLACKJACK),
            (hand("7", "7", "7"), hand("A", "K"), LOSE),
            (hand("K", "8"), hand("K", "6", "9"), WIN),
            (hand("K", "9"), hand("K", "8"), WIN),
            (hand("K", "7"), hand("K", "8"), LOSE),
            (hand("K", "8"), hand("Q", "8"), PUSH),
        ]
        for player, dealer, expected in cases:
            with self.subTest(player=player, dealer=dealer):
                self.assertEqual(determine_result(player, dealer), expected)

    def test_net_winnings(self):
        self.assertEqual(net_winnings(BLACKJACK, 100), 150)
        self.assertEqual(net_winnings(BLACKJACK, 15), 22)
        self.assertEqual(net_winnings(WIN, 100), 100)
        self.assertEqual(net_winnings(PUSH, 100), 0)
        self.assertEqual(net_winnings(LOSE, 100), -100)


class PlayBlackjackTest(PlainScreenTest):
    def play(self, ranks, inputs, balance=500):
        output = io.StringIO()
        with patch("builtins.input", side_effect=inputs), redirect_stdout(output):
            new_balance = blackjack(balance, stacked_deck(*ranks))
        return new_balance - balance, output.getvalue()

    def latest(self):
        entry = screen.history[0]
        return entry["outcome"], entry["details"][0], entry["kind"]

    def test_shows_player_cards_and_only_dealer_upcard_when_dealt(self):
        _, output = self.play(["10", "9", "8", "K"], ["50", "s"])

        self.assertIn("Bet: $50\n\nDealer: 9♠ ??\nYou:    10♠ 8♠ (18)\n", output)
        self.assertNotIn("K♠", output)

    def test_stand_and_beat_dealer(self):
        net, _ = self.play(["10", "10", "9", "8"], ["50", "s"])

        self.assertEqual(net, 50)
        self.assertEqual(
            self.latest(),
            ("You beat the dealer. You win $50.", "You: 10♠ 9♠ (19) | Dealer: 10♠ 8♠ (18)", "win"),
        )

    def test_table_redraws_after_each_hit(self):
        _, output = self.play(["2", "10", "3", "8", "4", "5"], ["50", "h", "h", "s"])

        self.assertEqual(output.count("Dealer: 10♠ ??"), 3)
        self.assertIn("You:    2♠ 3♠ (5)", output)
        self.assertIn("You:    2♠ 3♠ 4♠ (9)", output)
        self.assertIn("You:    2♠ 3♠ 4♠ 5♠ (14)", output)

    def test_hit_then_bust_loses_without_dealer_drawing(self):
        net, _ = self.play(["10", "10", "6", "6", "K"], ["50", "h"])

        self.assertEqual(net, -50)
        self.assertEqual(
            self.latest(),
            ("Bust. You lose $50.", "You: 10♠ 6♠ K♠ (26) | Dealer: 10♠ 6♠ (16)", "lose"),
        )

    def test_hitting_to_21_ends_the_player_turn(self):
        net, _ = self.play(["10", "10", "5", "8", "6"], ["50", "h"])

        self.assertEqual(net, 50)
        self.assertIn("You: 10♠ 5♠ 6♠ (21)", self.latest()[1])

    def test_dealer_draws_to_17_and_can_bust(self):
        net, _ = self.play(["10", "10", "8", "6", "K"], ["50", "s"])

        self.assertEqual(net, 50)
        self.assertEqual(self.latest()[0], "Dealer busts. You win $50.")
        self.assertIn("Dealer: 10♠ 6♠ K♠ (26)", self.latest()[1])

    def test_dealer_stands_on_soft_17(self):
        net, _ = self.play(["10", "A", "8", "6"], ["50", "s"])

        self.assertEqual(net, 50)
        self.assertIn("Dealer: A♠ 6♠ (17)", self.latest()[1])

    def test_equal_totals_push(self):
        net, _ = self.play(["10", "10", "8", "8"], ["50", "s"])

        self.assertEqual(net, 0)
        self.assertEqual(self.latest()[0], "Push. Your bet is returned.")
        self.assertEqual(self.latest()[2], "push")

    def test_player_blackjack_pays_3_to_2_without_choices(self):
        net, _ = self.play(["A", "10", "K", "8"], ["50"])

        self.assertEqual(net, 75)
        self.assertEqual(self.latest()[0], "Blackjack! You win $75.")

    def test_dealer_blackjack_ends_round_without_choices(self):
        net, _ = self.play(["10", "A", "9", "K"], ["50"])

        self.assertEqual(net, -50)
        self.assertEqual(self.latest()[0], "Dealer has blackjack. You lose $50.")

    def test_both_blackjack_push(self):
        net, _ = self.play(["A", "A", "K", "Q"], ["50"])

        self.assertEqual(net, 0)
        self.assertEqual(self.latest()[0], "Push. Your bet is returned.")

    def test_invalid_choice_reprompts(self):
        net, output = self.play(["10", "10", "9", "8"], ["50", "x", "STAND"])

        self.assertEqual(net, 50)
        self.assertEqual(
            output.count("> Invalid choice. Please enter h to hit or s to stand."), 1
        )

    def test_cancelling_the_bet_leaves_the_table_without_dealing(self):
        output = io.StringIO()
        with patch("builtins.input", side_effect=[""]), redirect_stdout(output):
            result = blackjack(500, stacked_deck())

        self.assertIsNone(result)
        self.assertNotIn("You:", output.getvalue())
        self.assertEqual(screen.history, [])

    def play_garage(self, decks, inputs):
        output = io.StringIO()
        with (
            patch("blackjack.new_deck", side_effect=decks),
            patch("builtins.input", side_effect=inputs),
            redirect_stdout(output),
        ):
            garage(500)
        return output.getvalue()

    def test_round_goes_straight_to_next_bet_and_garage_keeps_balance(self):
        output = self.play_garage([stacked_deck("10", "10", "9", "8")], ["2", "50", "s", "", "5"])

        next_bet = output.split("You:    10♠ 9♠ (19)\n")[-1].lstrip()
        self.assertTrue(next_bet.startswith("WORLD'S SMALLEST CASINO | Blackjack | Round 2 | $550"))
        self.assertIn("  Round 1 · Blackjack: You beat the dealer. You win $50.", next_bet)
        self.assertIn("Place a bet to deal a new hand.", next_bet)
        self.assertIn("WORLD'S SMALLEST CASINO | Garage | $550", output)

    def test_rounds_are_numbered_and_spaced_apart(self):
        decks = [stacked_deck("10", "10", "9", "8"), stacked_deck("10", "10", "7", "8")]
        output = self.play_garage(decks, ["2", "50", "s", "50", "s", "", "5"])

        self.assertIn("| Blackjack | Round 3 | $500 |", output)
        self.assertIn(
            "Recent rounds\n\n"
            "  Round 2 · Blackjack: Dealer wins. You lose $50.\n"
            "    You: 10♠ 7♠ (17) | Dealer: 10♠ 8♠ (18)\n\n"
            "  Round 1 · Blackjack: You beat the dealer. You win $50.\n"
            "    You: 10♠ 9♠ (19) | Dealer: 10♠ 8♠ (18)\n",
            output,
        )


if __name__ == "__main__":
    unittest.main()
