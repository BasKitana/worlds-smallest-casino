# Blackjack tests cover deck construction, scoring, payouts, and complete rounds.
# Fixed cards and scripted input make the results repeatable without real players.
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


def hand(*ranks):
    # *ranks collects arguments into a tuple. Suits do not affect Blackjack scoring,
    # so these small test fixtures use spades for every requested rank.
    return [(rank, "♠") for rank in ranks]


def stacked_deck(*ranks):
    """Build a deck that deals the given ranks in order."""
    # Reverse the fixture because the game draws from the end with pop().
    return list(reversed(hand(*ranks)))


class DealTest(unittest.TestCase):
    # Verify the real deck is unique and dealing alternates player/dealer correctly.
    def test_new_deck_has_52_unique_cards(self):
        deck = new_deck()

        self.assertEqual(len(deck), 52)
        # A set removes duplicates; its size should still be 52.
        self.assertEqual(len(set(deck)), 52)

    def test_deals_two_cards_each_alternating_from_player(self):
        deck = stacked_deck("2", "3", "4", "5", "6")

        player, dealer = deal_initial_cards(deck)

        self.assertEqual(player, hand("2", "4"))
        self.assertEqual(dealer, hand("3", "5"))
        self.assertEqual(deck, hand("6"))


class HandValueTest(unittest.TestCase):
    # Isolate card values, flexible aces, natural blackjacks, and display formatting.
    def test_number_and_face_cards(self):
        self.assertEqual(hand_value(hand("2", "10")), 12)
        self.assertEqual(hand_value(hand("J", "Q", "K")), 30)

    def test_ace_counts_as_eleven_or_one(self):
        # Include multiple aces and a hand that still busts after both become 1.
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
    # Check winner selection separately from the amount added to the balance.
    def test_results(self):
        # Each row is (player hand, dealer hand, expected result). Cases include
        # both busting, both naturals, a natural versus drawn 21, and ordinary totals.
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
        # The odd $15 bet verifies that the 3:2 bonus rounds down to $22.
        self.assertEqual(net_winnings(BLACKJACK, 100), 150)
        self.assertEqual(net_winnings(BLACKJACK, 15), 22)
        self.assertEqual(net_winnings(WIN, 100), 100)
        self.assertEqual(net_winnings(PUSH, 100), 0)
        self.assertEqual(net_winnings(LOSE, 100), -100)


class PlayBlackjackTest(unittest.TestCase):
    # Exercise complete rounds, checking both balance changes and printed messages.
    def play(self, ranks, inputs, balance=500):
        # Capture print() output; supply a fixed deck and one input value per prompt.
        output = io.StringIO()
        # The trailing "" answers the prompt to return to the garage.
        with patch("builtins.input", side_effect=[*inputs, ""]), redirect_stdout(output):
            new_balance = blackjack(balance, stacked_deck(*ranks))
        # Return net profit/loss so each test can focus on the outcome of its round.
        return new_balance - balance, output.getvalue()

    def test_shows_player_cards_and_only_dealer_upcard_when_dealt(self):
        _, output = self.play(["10", "9", "8", "K"], ["50", "s"])

        # Inspect only the text before the dealer's hidden card is revealed.
        before_choice = output.split("Dealer's cards:")[0]
        self.assertIn("Dealer shows: 9♠ and one face-down card", before_choice)
        self.assertIn("Your cards: 10♠ 8♠ (total 18)", before_choice)
        self.assertNotIn("K♠", before_choice)

    def test_stand_and_beat_dealer(self):
        net, output = self.play(["10", "10", "9", "8"], ["50", "s"])

        self.assertEqual(net, 50)
        self.assertIn("You beat the dealer. You win $50.", output)
        self.assertIn("New balance: $550", output)

    def test_hit_then_bust_loses_without_dealer_drawing(self):
        net, output = self.play(["10", "10", "6", "6", "K"], ["50", "h"])

        self.assertEqual(net, -50)
        self.assertIn("Bust. You lose $50.", output)
        self.assertNotIn("Dealer draws", output)

    def test_hitting_to_21_ends_the_player_turn(self):
        net, output = self.play(["10", "10", "5", "8", "6"], ["50", "h"])

        self.assertEqual(net, 50)
        self.assertIn("Your cards: 10♠ 5♠ 6♠ (total 21)", output)

    def test_dealer_draws_to_17_and_can_bust(self):
        net, output = self.play(["10", "10", "8", "6", "K"], ["50", "s"])

        self.assertEqual(net, 50)
        self.assertIn("Dealer draws: K♠", output)
        self.assertIn("Dealer busts. You win $50.", output)

    def test_dealer_stands_on_soft_17(self):
        net, output = self.play(["10", "A", "8", "6"], ["50", "s"])

        self.assertEqual(net, 50)
        self.assertNotIn("Dealer draws", output)

    def test_equal_totals_push(self):
        net, output = self.play(["10", "10", "8", "8"], ["50", "s"])

        self.assertEqual(net, 0)
        self.assertIn("Push. Your bet is returned.", output)

    def test_player_blackjack_pays_3_to_2_without_choices(self):
        net, output = self.play(["A", "10", "K", "8"], ["50"])

        self.assertEqual(net, 75)
        self.assertIn("Blackjack! You win $75.", output)

    def test_dealer_blackjack_ends_round_without_choices(self):
        net, output = self.play(["10", "A", "9", "K"], ["50"])

        self.assertEqual(net, -50)
        self.assertIn("Dealer has blackjack. You lose $50.", output)

    def test_both_blackjack_push(self):
        net, output = self.play(["A", "A", "K", "Q"], ["50"])

        self.assertEqual(net, 0)
        self.assertIn("Push. Your bet is returned.", output)

    def test_invalid_choice_reprompts(self):
        net, output = self.play(["10", "10", "9", "8"], ["50", "x", "STAND"])

        self.assertEqual(net, 50)
        self.assertIn("Invalid choice. Please enter h to hit or s to stand.", output)

    def test_cancelling_the_bet_deals_nothing(self):
        # An empty deck would fail if the game tried to draw after cancellation.
        net, output = self.play([], [""])

        self.assertEqual(net, 0)
        self.assertNotIn("Your cards", output)

    def test_garage_keeps_the_new_balance(self):
        # Integration check: enter Blackjack from the garage, win, return, then exit.
        output = io.StringIO()
        deck = stacked_deck("10", "10", "9", "8")
        inputs = ["2", "50", "s", "", "4"]
        with (
            # Replace the deck factory where blackjack() looks it up so play is fixed.
            patch("blackjack.new_deck", return_value=deck),
            patch("builtins.input", side_effect=inputs),
            redirect_stdout(output),
        ):
            garage(500)

        self.assertIn("Garage Casino — Balance: $550", output.getvalue())


# Run this file's unittest cases when launched directly.
if __name__ == "__main__":
    unittest.main()
