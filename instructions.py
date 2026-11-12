from betting import bet_limits, bet_tier

TABLE_INSTRUCTIONS = {
    "1": (
        "Poker — Five-Card Draw",
        [
            "Make a better five-card poker hand than the dealer.",
            "After you bet, you get five numbered cards.",
            "To swap cards, type up to 3 positions separated by commas, such as 1,4.",
            "To keep your hand, press Enter.",
            "A win pays 1 to 1. A tie returns your bet.",
        ],
    ),
    "2": (
        "Blackjack",
        [
            "Get closer to 21 than the dealer without going over.",
            "Number cards count their value, J/Q/K count 10, and an ace counts 1 or 11.",
            "Type h to hit (take a card) or s to stand (keep your total).",
            "The dealer draws until reaching 17 or more.",
            "A win pays 1 to 1 and a tie returns your bet.",
            "A blackjack (an ace and a 10-value card on the deal) pays 3 to 2.",
        ],
    ),
    "3": (
        "Roulette",
        [
            "Choose a wager from the list, then enter your bet.",
            "A single number pays 35 to 1 and a dozen pays 2 to 1.",
            "Red, black, odd, even, low (1-18), and high (19-36) pay 1 to 1.",
            "If the ball lands on 0, every wager except a bet on 0 loses.",
            "Choose 9 on the wager list to return to the garage.",
        ],
    ),
}


def betting_info(balance):
    minimum, maximum = bet_limits(balance)
    return [
        f"Your balance of ${balance} is Tier {bet_tier(balance)}: bets from ${minimum} to ${maximum}.",
        "Bet limits rise at $2,500 (Tier 2) and $5,000 (Tier 3). Reach $10,000 to win.",
        "After each round you go straight to your next bet.",
        "Press Enter at the bet prompt to return to the garage.",
    ]


def how_to_play(balance):
    while True:
        print("\nHow to Play")
        print("1. Poker")
        print("2. Blackjack")
        print("3. Roulette")
        print("4. Return to the garage")

        choice = input("Choose a table to learn about: ").strip()
        if choice in TABLE_INSTRUCTIONS:
            title, lines = TABLE_INSTRUCTIONS[choice]
            print(f"\n{title}")
            for line in lines + betting_info(balance):
                print(f"- {line}")
        elif choice in ("4", ""):
            return
        else:
            print("Invalid choice. Please select 1, 2, 3, or 4.")
