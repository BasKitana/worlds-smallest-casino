"""Graphical version of World's Smallest Casino, built with tkinter.

Run with:  python gui.py
"""

import random
import tkinter as tk

import blackjack as bj
import poker as pk
import roulette as rl
from betting import bet_limits, validate_bet
from main import WINNING_BALANCE

STARTING_BALANCE = 500
FONT = "Segoe UI"

FELT = "#0b5d3b"
FELT_DARK = "#07432a"
GOLD = "#f2c14e"
GOLD_DARK = "#d9a62e"
TEXT = "#f5f5f0"
MUTED = "#b9d9c8"
CARD = "#fdfdf8"
CARD_BACK = "#24407a"
RED = "#c0392b"
BLACK = "#1b1b1b"
GREEN = "#1e8449"
WIN_COLOR = "#7ee2a8"
LOSE_COLOR = "#ff9b8f"


def suit_color(suit):
    return RED if suit in ("♥", "♦") else BLACK


def blackjack_card_text(card):
    rank, suit = card
    return f"{rank}\n{suit}"


def poker_card_text(card):
    rank, suit = card
    return f"{pk.RANKS.get(rank, rank)}\n{suit}"


class CasinoApp:
    def __init__(self, root):
        self.root = root
        self.balance = STARTING_BALANCE
        self.screen = None
        self.spin_frames = 18
        root.title("World's Smallest Casino")
        root.configure(bg=FELT)
        root.geometry("940x780")
        root.minsize(880, 740)
        self.frame = tk.Frame(root, bg=FELT)
        self.frame.pack(fill="both", expand=True, padx=24, pady=16)
        self.show_title()

    # ----- shared widgets -------------------------------------------------

    def clear(self, screen):
        self.screen = screen
        for child in self.frame.winfo_children():
            child.destroy()

    def label(self, parent, text="", size=12, color=TEXT, bold=False):
        return tk.Label(
            parent,
            text=text,
            bg=parent["bg"],
            fg=color,
            font=(FONT, size, "bold" if bold else "normal"),
        )

    def button(self, parent, text, command, primary=False, width=14):
        bg = GOLD if primary else FELT_DARK
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=(FONT, 12, "bold"),
            bg=bg,
            fg=BLACK if primary else TEXT,
            activebackground=GOLD_DARK if primary else GREEN,
            activeforeground=BLACK if primary else TEXT,
            relief="flat",
            bd=0,
            padx=14,
            pady=8,
            width=width,
            cursor="hand2",
        )

    def row(self, parent):
        return tk.Frame(parent, bg=parent["bg"])

    def header(self, title, subtitle=""):
        bar = self.row(self.frame)
        bar.pack(fill="x")
        self.label(bar, title, 22, GOLD, bold=True).pack(side="left")
        self.balance_label = self.label(bar, "", 16, TEXT, bold=True)
        self.balance_label.pack(side="right")
        self.update_balance()
        if subtitle:
            self.label(self.frame, subtitle, 11, MUTED).pack(anchor="w")
        tk.Frame(self.frame, bg=GOLD, height=2).pack(fill="x", pady=(8, 12))

    def update_balance(self):
        self.balance_label.config(text=f"Balance: ${self.balance:,}")

    def card(self, parent, text, color=BLACK, hidden=False, selected=False):
        widget = tk.Label(
            parent,
            text="♣\n♦" if hidden else text,
            bg=CARD_BACK if hidden else CARD,
            fg=MUTED if hidden else color,
            font=(FONT, 16, "bold"),
            width=4,
            height=3,
            relief="raised",
            bd=2,
            highlightthickness=4,
            highlightbackground=GOLD if selected else FELT,
        )
        widget.pack(side="left", padx=6)
        return widget

    def hand_row(self, title):
        wrap = self.row(self.table)
        wrap.pack(pady=6)
        caption = self.label(wrap, title, 12, MUTED, bold=True)
        caption.pack()
        cards = self.row(wrap)
        cards.pack(pady=4)
        return caption, cards

    def draw_cards(self, area, cards, describe, hidden=(), selected=(), on_click=None):
        for child in area.winfo_children():
            child.destroy()
        for index, card in enumerate(cards):
            widget = self.card(
                area,
                describe(card),
                suit_color(card[1]),
                hidden=index in hidden,
                selected=index in selected,
            )
            if on_click:
                widget.config(cursor="hand2")
                widget.bind("<Button-1>", lambda _event, i=index: on_click(i))

    def table_screen(self, screen, title, subtitle):
        self.clear(screen)
        self.header(title, subtitle)
        self.table = self.row(self.frame)
        self.table.pack(fill="x")
        self.message = self.label(self.frame, "", 15, TEXT, bold=True)
        self.message.pack(pady=(8, 0))
        self.detail = self.label(self.frame, "", 12, MUTED)
        self.detail.pack()
        self.controls = self.row(self.frame)
        self.controls.pack(pady=8)

    def reset_controls(self):
        for child in self.controls.winfo_children():
            child.destroy()

    def bet_panel(self, on_bet):
        """Bet entry with +/- buttons, validated by betting.validate_bet."""
        self.reset_controls()
        minimum, maximum = bet_limits(self.balance)
        box = self.row(self.controls)
        box.pack()
        self.label(box, f"Table limits ${minimum:,} – ${maximum:,}", 12, MUTED).pack()

        line = self.row(box)
        line.pack(pady=6)
        amount = tk.StringVar(value=str(minimum))

        def step(delta):
            value = int(amount.get()) if amount.get().isdigit() else minimum
            amount.set(str(max(minimum, min(maximum, self.balance, value + delta))))

        self.button(line, "−", lambda: step(-minimum), width=3).pack(side="left")
        entry = tk.Entry(
            line, textvariable=amount, width=8, justify="center", font=(FONT, 16, "bold")
        )
        entry.pack(side="left", padx=8, ipady=4)
        self.button(line, "+", lambda: step(minimum), width=3).pack(side="left")

        error = self.label(box, "", 11, LOSE_COLOR)

        def submit():
            text = amount.get().strip()
            if not text.isdigit():
                error.config(text="Enter a whole dollar amount.")
                return
            bet = int(text)
            problem = validate_bet(bet, self.balance)
            if problem:
                error.config(text=problem)
                return
            on_bet(bet)

        self.button(line, "Place Bet", submit, primary=True, width=10).pack(
            side="left", padx=(14, 0)
        )
        error.pack(pady=(4, 0))
        entry.bind("<Return>", lambda _event: submit())

        box.amount, box.error, box.submit = amount, error, submit
        self.bet_box = box
        return box

    def finish_round(self, message, net, play_again):
        """Apply winnings or losses, show the new balance, and offer what comes next."""
        self.balance += net
        color = WIN_COLOR if net > 0 else LOSE_COLOR if net < 0 else TEXT
        self.message.config(text=message, fg=color)
        self.detail.config(text=f"New balance: ${self.balance:,}")
        self.update_balance()
        self.reset_controls()

        if self.balance >= WINNING_BALANCE:
            self.button(
                self.controls, "Collect Your Winnings", self.show_victory, primary=True, width=20
            ).pack()
        elif self.balance < bet_limits(self.balance)[0]:
            self.button(self.controls, "Continue", self.show_broke, primary=True).pack()
        else:
            self.button(self.controls, "Play Again", play_again, primary=True).pack(
                side="left", padx=6
            )
            self.button(self.controls, "Back to Garage", self.show_garage).pack(
                side="left", padx=6
            )

    # ----- menus ----------------------------------------------------------

    def show_title(self):
        self.clear("title")
        center = self.row(self.frame)
        center.place(relx=0.5, rely=0.45, anchor="center")
        self.label(center, "♠  ♥  ♣  ♦", 30, GOLD).pack()
        self.label(center, "World's Smallest Casino", 34, TEXT, bold=True).pack(pady=(6, 4))
        self.label(
            center,
            f"Start with ${STARTING_BALANCE}. Reach ${WINNING_BALANCE:,} to break the bank.",
            13,
            MUTED,
        ).pack(pady=(0, 24))
        buttons = self.row(center)
        buttons.pack()
        self.button(buttons, "Start", self.start, primary=True).pack(side="left", padx=8)
        self.button(buttons, "Exit", self.root.destroy).pack(side="left", padx=8)

    def start(self):
        self.balance = STARTING_BALANCE
        self.show_garage()

    def show_garage(self):
        if self.balance < bet_limits(self.balance)[0]:
            self.show_broke()
            return
        self.clear("garage")
        self.header("Garage Casino", "Pick a table. Bet limits rise as your balance grows.")

        tables = self.row(self.frame)
        tables.pack(pady=24)
        for suit, name, blurb, command in (
            ("♠", "Poker", "Five-card draw\nagainst the dealer", self.show_poker),
            ("♥", "Blackjack", "Get closer to 21\nthan the dealer", self.show_blackjack),
            ("●", "Roulette", "European wheel\npays up to 35:1", self.show_roulette),
        ):
            tile = tk.Frame(tables, bg=FELT_DARK, padx=22, pady=18)
            tile.pack(side="left", padx=12)
            self.label(tile, suit, 34, GOLD).pack()
            self.label(tile, name, 18, TEXT, bold=True).pack()
            self.label(tile, blurb, 11, MUTED).pack(pady=(4, 12))
            self.button(tile, f"Play {name}", command, primary=True).pack()

        self.button(self.frame, "Exit", self.root.destroy).pack(pady=8)

    def end_screen(self, screen, symbol, title, text):
        self.clear(screen)
        center = self.row(self.frame)
        center.place(relx=0.5, rely=0.45, anchor="center")
        self.label(center, symbol, 54, GOLD).pack()
        self.label(center, title, 32, TEXT, bold=True).pack(pady=6)
        self.label(center, text, 14, MUTED).pack(pady=(0, 24))
        buttons = self.row(center)
        buttons.pack()
        self.button(buttons, "Play Again", self.start, primary=True).pack(side="left", padx=8)
        self.button(buttons, "Exit", self.root.destroy).pack(side="left", padx=8)

    def show_victory(self):
        self.end_screen(
            "victory",
            "★",
            "You broke the bank!",
            f"You walked out with ${self.balance:,}. Thanks for playing!",
        )

    def show_broke(self):
        minimum = bet_limits(self.balance)[0]
        self.end_screen(
            "broke",
            "♣",
            "Out of chips",
            f"Your balance is ${self.balance:,}, below the ${minimum} minimum bet.",
        )

    # ----- blackjack ------------------------------------------------------

    def show_blackjack(self):
        self.table_screen(
            "blackjack", "Blackjack", "Dealer stands on all 17s · Blackjack pays 3:2 · Push returns your bet"
        )
        self.bj_dealer_caption, self.bj_dealer_area = self.hand_row("Dealer")
        self.bj_player_caption, self.bj_player_area = self.hand_row("You")
        self.message.config(text="Place a bet to deal.")
        self.bet_panel(self.bj_deal)

    def bj_deal(self, bet):
        self.bet = bet
        self.deck = bj.new_deck()
        self.player, self.dealer = bj.deal_initial_cards(self.deck)
        self.bj_render(hide_dealer=True)
        self.detail.config(text=f"Bet: ${bet:,}")

        if bj.is_blackjack(self.player) or bj.is_blackjack(self.dealer):
            self.bj_finish()
            return

        self.message.config(text="Hit or stand?", fg=TEXT)
        self.reset_controls()
        self.button(self.controls, "Hit", self.bj_hit, primary=True).pack(side="left", padx=6)
        self.button(self.controls, "Stand", self.bj_stand).pack(side="left", padx=6)

    def bj_render(self, hide_dealer):
        if hide_dealer:
            shown = bj.hand_value(self.dealer[:1])
            self.bj_dealer_caption.config(text=f"Dealer — shows {shown}")
        else:
            self.bj_dealer_caption.config(text=f"Dealer — {bj.hand_value(self.dealer)}")
        self.bj_player_caption.config(text=f"You — {bj.hand_value(self.player)}")
        self.draw_cards(
            self.bj_dealer_area,
            self.dealer,
            blackjack_card_text,
            hidden={1} if hide_dealer else (),
        )
        self.draw_cards(self.bj_player_area, self.player, blackjack_card_text)

    def bj_hit(self):
        self.player.append(self.deck.pop())
        self.bj_render(hide_dealer=True)
        if bj.hand_value(self.player) >= 21:
            self.bj_stand()

    def bj_stand(self):
        if bj.hand_value(self.player) <= 21:
            while bj.hand_value(self.dealer) < 17:
                self.dealer.append(self.deck.pop())
        self.bj_finish()

    def bj_finish(self):
        self.bj_render(hide_dealer=False)
        result = bj.determine_result(self.player, self.dealer)
        net = bj.net_winnings(result, self.bet)
        self.finish_round(
            bj.result_message(result, net, self.player, self.dealer), net, self.show_blackjack
        )

    # ----- poker ----------------------------------------------------------

    def show_poker(self):
        self.table_screen(
            "poker",
            "Five-Card Draw Poker",
            "Beat the dealer's hand to win even money · Discard up to 3 cards · Ties push",
        )
        self.pk_dealer_caption, self.pk_dealer_area = self.hand_row("Dealer")
        self.pk_player_caption, self.pk_player_area = self.hand_row("You")
        self.message.config(text="Place a bet to deal.")
        self.bet_panel(self.pk_deal)

    def pk_deal(self, bet):
        self.bet = bet
        self.deck = pk.create_deck()
        random.shuffle(self.deck)
        self.player = pk.deal_hand(self.deck)
        self.dealer = pk.deal_hand(self.deck)
        self.discards = set()
        self.detail.config(text=f"Bet: ${bet:,}")
        self.message.config(text="Click up to 3 cards to discard, then draw.", fg=TEXT)
        self.reset_controls()
        self.draw_button = self.button(self.controls, "Stand Pat", self.pk_draw, primary=True)
        self.draw_button.pack()
        self.pk_render(reveal=False)

    def pk_render(self, reveal):
        if reveal:
            self.pk_dealer_caption.config(text=f"Dealer — {pk.hand_name(self.dealer)}")
            self.pk_player_caption.config(text=f"You — {pk.hand_name(self.player)}")
        else:
            self.pk_dealer_caption.config(text="Dealer")
            self.pk_player_caption.config(text=f"You — {pk.hand_name(self.player)}")
        self.draw_cards(
            self.pk_dealer_area,
            self.dealer,
            poker_card_text,
            hidden=() if reveal else set(range(5)),
        )
        self.draw_cards(
            self.pk_player_area,
            self.player,
            poker_card_text,
            selected=() if reveal else self.discards,
            on_click=None if reveal else self.pk_toggle,
        )

    def pk_toggle(self, index):
        if index in self.discards:
            self.discards.remove(index)
        elif len(self.discards) < 3:
            self.discards.add(index)
        else:
            self.message.config(text="You can discard at most 3 cards.", fg=LOSE_COLOR)
            return
        self.message.config(text="Click up to 3 cards to discard, then draw.", fg=TEXT)
        count = len(self.discards)
        self.draw_button.config(text=f"Draw {count}" if count else "Stand Pat")
        self.pk_render(reveal=False)

    def pk_draw(self):
        self.player = pk.draw_replacements(self.player, self.deck, sorted(self.discards))
        self.dealer = pk.draw_replacements(self.dealer, self.deck, pk.dealer_discards(self.dealer))
        self.pk_render(reveal=True)
        net = pk.resolve(self.player, self.dealer, self.bet)
        if net > 0:
            message = f"You win ${net:,} with {pk.hand_name(self.player)}!"
        elif net < 0:
            message = f"Dealer wins with {pk.hand_name(self.dealer)}. You lose ${self.bet:,}."
        else:
            message = "Push — your bet is returned."
        self.finish_round(message, net, self.show_poker)

    # ----- roulette -------------------------------------------------------

    def show_roulette(self):
        self.table_screen(
            "roulette",
            "Roulette",
            "European wheel 0–36 · Number pays 35:1 · Dozen pays 2:1 · Even-money bets pay 1:1",
        )
        self.wager = None
        self.wager_buttons = {}

        top = self.row(self.table)
        top.pack(pady=(0, 8))
        self.rl_ball = tk.Label(
            top, text="–", width=3, bg=FELT_DARK, fg=TEXT, font=(FONT, 30, "bold"), relief="ridge", bd=3
        )
        self.rl_ball.pack(side="left", padx=(0, 16))
        self.rl_wager_label = self.label(top, "Click the board to choose a wager.", 14, GOLD, bold=True)
        self.rl_wager_label.pack(side="left")

        board = self.row(self.table)
        board.pack()
        self.board_button(board, ("Number 0", {0}, 35), "0", GREEN).grid(
            row=0, column=0, rowspan=3, sticky="ns", padx=1, pady=1
        )
        for column in range(12):
            for row in range(3):
                number = column * 3 + (3 - row)
                self.board_button(
                    board, (f"Number {number}", {number}, 35), str(number), RED if number in rl.RED else BLACK
                ).grid(row=row, column=column + 1, padx=1, pady=1)

        for dozen in range(3):
            start = dozen * 12 + 1
            wager = (f"Dozen {start}-{start + 11}", set(range(start, start + 12)), 2)
            self.board_button(board, wager, f"{start}–{start + 11}", FELT_DARK).grid(
                row=3, column=dozen * 4 + 1, columnspan=4, sticky="ew", padx=1, pady=1
            )

        outside = (
            ("6", "1–18", FELT_DARK),
            ("5", "Even", FELT_DARK),
            ("2", "Red", RED),
            ("3", "Black", BLACK),
            ("4", "Odd", FELT_DARK),
            ("7", "19–36", FELT_DARK),
        )
        for index, (key, text, color) in enumerate(outside):
            self.board_button(board, rl.OUTSIDE_WAGERS[key], text, color).grid(
                row=4, column=index * 2 + 1, columnspan=2, sticky="ew", padx=1, pady=1
            )

        self.message.config(text="Choose a wager, then place your bet and spin.")
        self.bet_panel(self.rl_spin)

    def board_button(self, parent, wager, text, color):
        button = tk.Button(
            parent,
            text=text,
            command=lambda: self.rl_select(wager),
            bg=color,
            fg=TEXT,
            activebackground=GOLD,
            activeforeground=BLACK,
            disabledforeground=TEXT,
            font=(FONT, 11, "bold"),
            width=3,
            relief="flat",
            bd=0,
            pady=6,
            cursor="hand2",
        )
        button.original_bg = color
        self.wager_buttons[wager[0]] = button
        return button

    def rl_select(self, wager):
        if self.wager:
            previous = self.wager_buttons.get(self.wager[0])
            if previous:
                previous.config(bg=previous.original_bg, fg=TEXT)
        self.wager = wager
        selected = self.wager_buttons.get(wager[0])
        if selected:
            selected.config(bg=GOLD, fg=BLACK)
        self.rl_wager_label.config(text=f"Your wager: {wager[0]} (pays {wager[2]} to 1)")
        if getattr(self, "bet_box", None):
            self.bet_box.error.config(text="")

    def rl_spin(self, bet):
        if self.wager is None:
            self.bet_box.error.config(text="Choose a wager on the board first.")
            return
        self.bet = bet
        for button in self.wager_buttons.values():
            button.config(state="disabled")
        self.reset_controls()
        self.message.config(text="No more bets!", fg=TEXT)
        self.detail.config(text=f"${bet:,} on {self.wager[0]}")
        self.rl_animate(self.spin_frames, rl.spin())

    def rl_show_number(self, number):
        color = GREEN if number == 0 else RED if number in rl.RED else BLACK
        self.rl_ball.config(text=str(number), bg=color)

    def rl_animate(self, frames_left, result):
        if frames_left > 0:
            self.rl_show_number(random.randint(0, 36))
            delay = 40 + (self.spin_frames - frames_left) * 12
            self.root.after(delay, lambda: self.rl_animate(frames_left - 1, result))
            return

        self.rl_show_number(result)
        net = rl.resolve(self.wager, self.bet, result)
        landed = f"The ball lands on {result} {rl.color(result)}."
        if net > 0:
            message = f"{landed} You win ${net:,}!"
        else:
            message = f"{landed} You lose ${self.bet:,}."
        self.finish_round(message, net, self.show_roulette)


def run():
    root = tk.Tk()
    CasinoApp(root)
    root.mainloop()


if __name__ == "__main__":
    run()
