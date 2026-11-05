import unittest
from unittest.mock import patch

try:
    import tkinter as tk

    _root = tk.Tk()
    _root.destroy()
    TK_AVAILABLE = True
except Exception:  # no display or no Tk install
    TK_AVAILABLE = False

if TK_AVAILABLE:
    import gui


@unittest.skipUnless(TK_AVAILABLE, "Tk display not available")
class GuiTest(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = gui.CasinoApp(self.root)
        self.app.spin_frames = 0

    def tearDown(self):
        self.root.destroy()

    def place_bet(self, amount):
        self.app.bet_box.amount.set(str(amount))
        self.app.bet_box.submit()

    def control_buttons(self):
        return {child["text"]: child for child in self.app.controls.winfo_children()}

    def test_start_opens_garage_with_starting_balance(self):
        self.assertEqual(self.app.screen, "title")
        self.app.start()

        self.assertEqual(self.app.screen, "garage")
        self.assertEqual(self.app.balance_label["text"], "Balance: $500")

    def test_bet_over_table_maximum_is_rejected(self):
        self.app.start()
        self.app.show_blackjack()
        self.place_bet(150)

        self.assertIn("maximum bet is $100", self.app.bet_box.error["text"])
        self.assertEqual(self.app.balance, 500)

    def test_blackjack_win_adds_bet_to_balance(self):
        # Cards are popped from the end: player 10, dealer 9, player K, dealer 7, dealer draws K.
        deck = [("K", "♠"), ("7", "♣"), ("K", "♥"), ("9", "♦"), ("10", "♠")]
        self.app.start()
        self.app.show_blackjack()
        with patch.object(gui.bj, "new_deck", return_value=deck):
            self.place_bet(50)
        self.app.bj_stand()

        self.assertEqual(self.app.balance, 550)
        self.assertIn("Dealer busts", self.app.message["text"])
        self.assertEqual(self.app.balance_label["text"], "Balance: $550")
        self.assertIn("Play Again", self.control_buttons())

    def test_roulette_requires_a_wager_before_spinning(self):
        self.app.start()
        self.app.show_roulette()
        self.place_bet(10)

        self.assertIn("Choose a wager", self.app.bet_box.error["text"])
        self.assertEqual(self.app.balance, 500)

    def test_roulette_single_number_pays_35_to_1(self):
        self.app.start()
        self.app.show_roulette()
        self.app.wager_buttons["Number 17"].invoke()
        with patch.object(gui.rl, "spin", return_value=17):
            self.place_bet(10)

        self.assertEqual(self.app.balance, 850)
        self.assertIn("lands on 17", self.app.message["text"])

    def test_poker_allows_at_most_three_discards(self):
        self.app.start()
        self.app.show_poker()
        self.place_bet(10)
        for index in range(4):
            self.app.pk_toggle(index)

        self.assertEqual(self.app.discards, {0, 1, 2})
        self.assertIn("at most 3", self.app.message["text"])
        self.assertEqual(self.app.draw_button["text"], "Draw 3")

    def test_reaching_winning_balance_leads_to_victory_screen(self):
        self.app.balance = 9_990
        self.app.show_roulette()
        self.app.wager_buttons["Red"].invoke()
        with patch.object(gui.rl, "spin", return_value=1):
            self.place_bet(500)

        self.assertEqual(self.app.balance, 10_490)
        self.control_buttons()["Collect Your Winnings"].invoke()
        self.assertEqual(self.app.screen, "victory")

    def test_player_below_minimum_bet_sees_game_over(self):
        self.app.balance = 5
        self.app.show_garage()

        self.assertEqual(self.app.screen, "broke")


if __name__ == "__main__":
    unittest.main()
