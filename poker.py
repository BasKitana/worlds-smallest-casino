# Five-card draw: player and dealer each get one chance to replace cards.
# Cards are (numeric rank, suit) tuples; ranks 2-14 run from two through ace.
import random
from collections import Counter

import screen
from betting import get_bet

# Unlike Blackjack's string ranks, numeric ranks allow direct strength comparisons.
RANKS = {11: "J", 12: "Q", 13: "K", 14: "A"}
SUITS = ("♣", "♦", "♥", "♠")


def create_deck():
    # Build all 52 rank/suit combinations; the round shuffles this list later.
    return [(rank, suit) for rank in range(2, 15) for suit in SUITS]


def deal_hand(deck):
    # Remove five cards from the end of the shared deck so they cannot be dealt again.
    return [deck.pop() for _ in range(5)]


def describe_card(card):
    # Dictionary get() supplies a face-card label, or keeps the number as its default.
    rank, suit = card
    return f"{RANKS.get(rank, rank)}{suit}"


def describe_hand(hand):
    # enumerate(..., 1) labels cards 1-5 to match the player's discard choices.
    return " ".join(f"{index}. {describe_card(card)}" for index, card in enumerate(hand, 1))


def rank_hand(hand):
    # Return (category, tie-breakers...) for a five-card hand. Higher tuples win:
    # Python compares their elements left to right until it finds a difference.
    # Categories: 0 high card, 1 pair, 2 two pair, 3 trips, 4 straight, 5 flush,
    # 6 full house, 7 four of a kind, 8 straight flush (including a royal flush).
    ranks = [rank for rank, _ in hand]
    # Counter counts occurrences of each rank; sorting (count, rank) descending
    # puts larger matching groups first, then higher ranks within equal-size groups.
    counts = Counter(ranks)
    groups = sorted(((count, rank) for rank, count in counts.items()), reverse=True)
    distinct = sorted(counts)  # Sorted dictionary keys give the unique ranks.
    straight_high = 0
    if len(distinct) == 5:
        if distinct == [2, 3, 4, 5, 14]:
            # An ace can act as 1 in A-2-3-4-5, making this a five-high straight.
            straight_high = 5
        elif distinct[-1] - distinct[0] == 4:
            # Five unique ranks spanning four steps must be consecutive.
            straight_high = distinct[-1]

    flush = len({suit for _, suit in hand}) == 1  # A set removes duplicate suits.
    # Check strongest categories first because a hand may satisfy weaker ones too.
    if straight_high and flush:
        return (8, straight_high)
    if groups[0][0] == 4:
        quad = groups[0][1]
        # next() selects the lone unmatched rank to break ties between equal quads.
        return (7, quad, next(rank for rank in ranks if rank != quad))
    if groups[0][0] == 3 and groups[1][0] == 2:
        return (6, groups[0][1], groups[1][1])
    if flush:
        # * expands the sorted ranks into separate tuple elements for tie-breaking.
        return (5, *sorted(ranks, reverse=True))
    if straight_high:
        return (4, straight_high)
    if groups[0][0] == 3:
        trip = groups[0][1]
        # Kickers are unmatched cards, compared highest first when groups tie.
        kickers = sorted((rank for rank in ranks if rank != trip), reverse=True)
        return (3, trip, *kickers)
    if groups[0][0] == 2 and groups[1][0] == 2:
        # Compare the higher pair, then the lower pair, then the remaining card.
        pairs = sorted((rank for count, rank in groups if count == 2), reverse=True)
        kicker = next(rank for rank in ranks if rank not in pairs)
        return (2, *pairs, kicker)
    if groups[0][0] == 2:
        pair = groups[0][1]
        kickers = sorted((rank for rank in ranks if rank != pair), reverse=True)
        return (1, pair, *kickers)
    return (0, *sorted(ranks, reverse=True))


def hand_name(hand):
    # The category number is also the index of its readable name below.
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
    # The hand without position numbers, for the round recap.
    return " ".join(describe_card(card) for card in hand)


def choose_discards(balance, bet, hand):
    # Read positions 1-5 from the player; return zero-based indexes for list access.
    while True:
        # Redraw the bet and the numbered hand (with its current rank) before each try.
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
            # Standing means keeping every card, represented by no discard indexes.
            return []
        parts = [part.strip() for part in choice.split(",")]
        # Require at most three valid positions with no duplicates (e.g. "1,1").
        # The and checks stop at the first failure, before converting invalid text.
        if (
            len(parts) <= 3
            and all(part.isdigit() and 1 <= int(part) <= 5 for part in parts)
            and len({int(part) for part in parts}) == len(parts)
        ):
            return [int(part) - 1 for part in parts]
        # The loop redraws the same hand with this message at the top.
        screen.notice("Invalid choice. Enter up to 3 different positions from 1 to 5.", "error")


def draw_replacements(hand, deck, positions):
    # Copy the hand so the original stays intact; drawing still consumes deck cards.
    updated = list(hand)
    for position in positions:
        updated[position] = deck.pop()
    return updated


def dealer_discards(hand):
    # Simple strategy: keep a straight or better; otherwise keep all matching ranks.
    counts = Counter(rank for rank, _ in hand)
    if rank_hand(hand)[0] >= 4:
        return []
    matched_ranks = {rank for rank, count in counts.items() if count >= 2}
    if matched_ranks:
        return [index for index, (rank, _) in enumerate(hand) if rank not in matched_ranks]
    # Without matches, sort card indexes by rank and keep the two highest cards.
    # The lambda tells sorted() which rank belongs to each index.
    keep = set(sorted(range(5), key=lambda index: hand[index][0], reverse=True)[:2])
    return [index for index in range(5) if index not in keep]


def resolve(player_hand, dealer_hand, bet):
    # Compare category/tie-breaker tuples; suits never break ties in this game.
    # Return only the balance change because no stake has been deducted yet.
    player_score = rank_hand(player_hand)
    dealer_score = rank_hand(dealer_hand)
    if player_score > dealer_score:
        return bet
    if player_score < dealer_score:
        return -bet
    return 0


def poker(balance):
    # Coordinate one complete round. Cancelling the bet returns None, which tells
    # the garage that the player left the table.
    # The two body lines remind the player of the rules on the bet screen.
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

    # Both hands and all replacements use one shuffled deck to avoid duplicate cards.
    deck = create_deck()
    random.shuffle(deck)
    player_hand = deal_hand(deck)
    dealer_hand = deal_hand(deck)
    # The player chooses which cards to swap; the new cards come from the same deck.
    discards = choose_discards(balance, bet, player_hand)
    player_hand = draw_replacements(player_hand, deck, discards)
    # The dealer chooses discards automatically and reveals its hand after drawing.
    dealer_hand = draw_replacements(dealer_hand, deck, dealer_discards(dealer_hand))

    # Name both hands for the recap, then settle the bet.
    # The two names are assigned in one line: yours gets the first, theirs the second.
    yours, theirs = hand_name(player_hand), hand_name(dealer_hand)
    change = resolve(player_hand, dealer_hand, bet)
    # Pick the sentence for the history, plus the kind that sets its color.
    if change > 0:
        outcome, kind = f"Your {yours} beats the dealer's {theirs}. You win ${change}!", "win"
    elif change < 0:
        outcome, kind = f"The dealer's {theirs} beats your {yours}. You lose ${bet}.", "lose"
    else:
        outcome, kind = f"Both have {yours}. Push — your bet is returned.", "push"

    # Save both final hands for the recent-rounds history shown on the next screen.
    screen.record_round(
        "Poker",
        outcome,
        [
            f"You:    {cards_text(player_hand)} ({yours})",
            f"Dealer: {cards_text(dealer_hand)} ({theirs})",
        ],
        kind,
    )
    # A win adds the bet, a loss subtracts it, and a tie adds zero.
    return balance + change
