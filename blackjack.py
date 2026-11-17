import random

import screen
from betting import get_bet

RANKS = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")
SUITS = ("♠", "♥", "♦", "♣")

BLACKJACK = "blackjack"
WIN = "win"
PUSH = "push"
LOSE = "lose"


def new_deck():
    deck = [(rank, suit) for suit in SUITS for rank in RANKS]
    random.shuffle(deck)
    return deck


def deal_initial_cards(deck):
    """Deal two cards each, alternating, starting with the player."""
    player = [deck.pop()]
    dealer = [deck.pop()]
    player.append(deck.pop())
    dealer.append(deck.pop())
    return player, dealer


def hand_value(hand):
    total = 0
    aces = 0
    for rank, _ in hand:
        if rank == "A":
            total += 11
            aces += 1
        elif rank in ("J", "Q", "K"):
            total += 10
        else:
            total += int(rank)

    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total


def is_blackjack(hand):
    return len(hand) == 2 and hand_value(hand) == 21


def format_hand(hand):
    return " ".join(f"{rank}{suit}" for rank, suit in hand)


def hand_summary(hand):
    return f"{format_hand(hand)} ({hand_value(hand)})"


def table_lines(bet, player, dealer):
    """The blackjack table mid-hand, with the dealer's second card face down."""
    return [
        f"Bet: {screen.money(bet)}",
        "",
        f"Dealer: {format_hand(dealer[:1])} ??",
        f"You:    {hand_summary(player)}",
        "",
    ]


def player_turn(deck, player, dealer, balance, bet):
    """Redraw the table and let the player hit until they stand, bust, or reach 21."""
    while hand_value(player) < 21:
        screen.show("Blackjack", balance, table_lines(bet, player, dealer), at_table=True)
        choice = input("Hit or stand? (h/s): ").strip().lower()

        if choice in ("h", "hit"):
            player.append(deck.pop())
        elif choice in ("s", "stand"):
            return
        else:
            screen.notice("Invalid choice. Please enter h to hit or s to stand.", "error")


def dealer_turn(deck, dealer):
    """The dealer draws on 16 or less and stands on 17 or more, including soft 17."""
    while hand_value(dealer) < 17:
        dealer.append(deck.pop())


def determine_result(player, dealer):
    player_total = hand_value(player)
    dealer_total = hand_value(dealer)

    if player_total > 21:
        return LOSE
    if is_blackjack(player) and is_blackjack(dealer):
        return PUSH
    if is_blackjack(player):
        return BLACKJACK
    if is_blackjack(dealer):
        return LOSE
    if dealer_total > 21 or player_total > dealer_total:
        return WIN
    if player_total < dealer_total:
        return LOSE
    return PUSH


def net_winnings(result, bet):
    """Return the balance change for a result. A blackjack pays 3:2, rounded down."""
    if result == BLACKJACK:
        return bet * 3 // 2
    if result == WIN:
        return bet
    if result == LOSE:
        return -bet
    return 0


def result_message(result, net, player, dealer):
    if result == BLACKJACK:
        return f"Blackjack! You win ${net}."
    if result == WIN:
        if hand_value(dealer) > 21:
            return f"Dealer busts. You win ${net}."
        return f"You beat the dealer. You win ${net}."
    if result == PUSH:
        return "Push. Your bet is returned."
    if hand_value(player) > 21:
        return f"Bust. You lose ${-net}."
    if is_blackjack(dealer):
        return f"Dealer has blackjack. You lose ${-net}."
    return f"Dealer wins. You lose ${-net}."


def blackjack(balance, deck=None):
    """Play one round and return the new balance, or None if the player leaves the table."""
    bet = get_bet(balance, "Blackjack", ["Place a bet to deal a new hand."])
    if bet is None:
        return None

    if deck is None:
        deck = new_deck()

    player, dealer = deal_initial_cards(deck)
    has_natural = is_blackjack(player) or is_blackjack(dealer)
    if not has_natural:
        player_turn(deck, player, dealer, balance, bet)
        if hand_value(player) <= 21:
            dealer_turn(deck, dealer)

    result = determine_result(player, dealer)
    net = net_winnings(result, bet)
    kind = "win" if net > 0 else "lose" if net < 0 else "push"
    screen.record_round(
        "Blackjack",
        result_message(result, net, player, dealer),
        [f"You: {hand_summary(player)} | Dealer: {hand_summary(dealer)}"],
        kind,
    )
    return balance + net
