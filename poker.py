import random
from collections import Counter

import screen
from betting import get_bet

RANKS = {11: "J", 12: "Q", 13: "K", 14: "A"}
SUITS = ("♣", "♦", "♥", "♠")


def create_deck():
    return [(rank, suit) for rank in range(2, 15) for suit in SUITS]


def deal_hand(deck):
    return [deck.pop() for _ in range(5)]


def describe_card(card):
    rank, suit = card
    return f"{RANKS.get(rank, rank)}{suit}"


def describe_hand(hand):
    return " ".join(f"{index}. {describe_card(card)}" for index, card in enumerate(hand, 1))


def rank_hand(hand):
    ranks = [rank for rank, _ in hand]
    counts = Counter(ranks)
    groups = sorted(((count, rank) for rank, count in counts.items()), reverse=True)
    distinct = sorted(counts)
    straight_high = 0
    if len(distinct) == 5:
        if distinct == [2, 3, 4, 5, 14]:
            straight_high = 5
        elif distinct[-1] - distinct[0] == 4:
            straight_high = distinct[-1]

    flush = len({suit for _, suit in hand}) == 1
    if straight_high and flush:
        return (8, straight_high)
    if groups[0][0] == 4:
        quad = groups[0][1]
        return (7, quad, next(rank for rank in ranks if rank != quad))
    if groups[0][0] == 3 and groups[1][0] == 2:
        return (6, groups[0][1], groups[1][1])
    if flush:
        return (5, *sorted(ranks, reverse=True))
    if straight_high:
        return (4, straight_high)
    if groups[0][0] == 3:
        trip = groups[0][1]
        kickers = sorted((rank for rank in ranks if rank != trip), reverse=True)
        return (3, trip, *kickers)
    if groups[0][0] == 2 and groups[1][0] == 2:
        pairs = sorted((rank for count, rank in groups if count == 2), reverse=True)
        kicker = next(rank for rank in ranks if rank not in pairs)
        return (2, *pairs, kicker)
    if groups[0][0] == 2:
        pair = groups[0][1]
        kickers = sorted((rank for rank in ranks if rank != pair), reverse=True)
        return (1, pair, *kickers)
    return (0, *sorted(ranks, reverse=True))


def hand_name(hand):
    return (
        "high card",
        "one pair",
        "two pair",
        "three of a kind",
        "straight",
        "flush",
        "full house",
        "four of a kind",
        "straight flush",
    )[rank_hand(hand)[0]]


def cards_text(hand):
    return " ".join(describe_card(card) for card in hand)


def choose_discards(balance, bet, hand):
    while True:
        screen.show(
            "Poker",
            balance,
            [
                f"Bet: {screen.money(bet)}",
                "",
                f"Your hand: {describe_hand(hand)}  ({hand_name(hand)})",
                "",
            ],
            at_table=True,
        )
        choice = input(
            "Discard up to 3 cards by position (comma-separated), or press Enter to stand: "
        ).strip()
        if choice == "":
            return []
        parts = [part.strip() for part in choice.split(",")]
        if (
            len(parts) <= 3
            and all(part.isdigit() and 1 <= int(part) <= 5 for part in parts)
            and len({int(part) for part in parts}) == len(parts)
        ):
            return [int(part) - 1 for part in parts]
        screen.notice("Invalid choice. Enter up to 3 different positions from 1 to 5.", "error")


def draw_replacements(hand, deck, positions):
    updated = list(hand)
    for position in positions:
        updated[position] = deck.pop()
    return updated


def dealer_discards(hand):
    counts = Counter(rank for rank, _ in hand)
    if rank_hand(hand)[0] >= 4:
        return []
    matched_ranks = {rank for rank, count in counts.items() if count >= 2}
    if matched_ranks:
        return [index for index, (rank, _) in enumerate(hand) if rank not in matched_ranks]
    keep = set(sorted(range(5), key=lambda index: hand[index][0], reverse=True)[:2])
    return [index for index in range(5) if index not in keep]


def resolve(player_hand, dealer_hand, bet):
    player_score = rank_hand(player_hand)
    dealer_score = rank_hand(dealer_hand)
    if player_score > dealer_score:
        return bet
    if player_score < dealer_score:
        return -bet
    return 0


def poker(balance):
    bet = get_bet(
        balance,
        "Poker",
        [
            "Five-Card Draw: discard and draw up to 3 cards, then beat the dealer's hand.",
            "A win pays 1 to 1 and a tie returns your bet.",
        ],
    )
    if bet is None:
        return None

    deck = create_deck()
    random.shuffle(deck)
    player_hand = deal_hand(deck)
    dealer_hand = deal_hand(deck)
    discards = choose_discards(balance, bet, player_hand)
    player_hand = draw_replacements(player_hand, deck, discards)
    dealer_hand = draw_replacements(dealer_hand, deck, dealer_discards(dealer_hand))

    yours, theirs = hand_name(player_hand), hand_name(dealer_hand)
    change = resolve(player_hand, dealer_hand, bet)
    if change > 0:
        outcome, kind = f"Your {yours} beats the dealer's {theirs}. You win ${change}!", "win"
    elif change < 0:
        outcome, kind = f"The dealer's {theirs} beats your {yours}. You lose ${bet}.", "lose"
    else:
        outcome, kind = f"Both have {yours}. Push — your bet is returned.", "push"

    screen.record_round(
        "Poker",
        outcome,
        [
            f"You:    {cards_text(player_hand)} ({yours})",
            f"Dealer: {cards_text(dealer_hand)} ({theirs})",
        ],
        kind,
    )
    return balance + change
