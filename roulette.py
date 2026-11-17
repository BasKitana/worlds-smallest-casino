# European Roulette uses numbers 0-36, with a single green zero.
# Each wager is (display label, set of winning numbers, profit multiplier).
import random

from betting import get_bet

RED = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
# range() excludes its upper bound; set subtraction keeps non-red numbers 1-36.
BLACK = set(range(1, 37)) - RED

# Menu choices map to preset wagers. Zero is excluded, even from the "Even" bet.
# % is the remainder operator: n % 2 is 1 for odd numbers and 0 for even numbers.
OUTSIDE_WAGERS = {
    "2": ("Red", RED, 1),
    "3": ("Black", BLACK, 1),
    "4": ("Odd", {n for n in range(1, 37) if n % 2 == 1}, 1),
    "5": ("Even", {n for n in range(1, 37) if n % 2 == 0}, 1),
    "6": ("Low (1-18)", set(range(1, 19)), 1),
    "7": ("High (19-36)", set(range(19, 37)), 1),
}


def color(number):
    # Translate a valid wheel number into the color shown in the result message.
    if number == 0:
        return "Green"
    return "Red" if number in RED else "Black"


def ask_number(prompt, low, high):
    # Retry until an integer falls within both inclusive bounds; blank means back.
    while True:
        choice = input(prompt).strip()
        if choice == "":
            return None
        if choice.isdigit() and low <= int(choice) <= high:
            return int(choice)
        print(f"Invalid choice. Please enter a number from {low} to {high}.")


def choose_wager():
    # Return a wager tuple, or None when the player chooses to leave the table.
    while True:
        print("\nRoulette Wagers")
        print("1. Single number (pays 35 to 1)")
        print("2. Red (pays 1 to 1)")
        print("3. Black (pays 1 to 1)")
        print("4. Odd (pays 1 to 1)")
        print("5. Even (pays 1 to 1)")
        print("6. Low 1-18 (pays 1 to 1)")
        print("7. High 19-36 (pays 1 to 1)")
        print("8. Dozen (pays 2 to 1)")
        print("9. Return to the garage")

        choice = input("Choose a wager: ").strip()

        if choice == "1":
            number = ask_number("Pick a number (0-36, or press Enter to go back): ", 0, 36)
            if number is None:
                # Cancel just this number selection and redisplay the wager menu.
                continue
            return (f"Number {number}", {number}, 35)
        elif choice in OUTSIDE_WAGERS:
            return OUTSIDE_WAGERS[choice]
        elif choice == "8":
            dozen = ask_number(
                "Pick a dozen (1 = 1-12, 2 = 13-24, 3 = 25-36, or press Enter to go back): ", 1, 3
            )
            if dozen is None:
                continue
            # Convert choices 1, 2, 3 into starting numbers 1, 13, 25.
            start = (dozen - 1) * 12 + 1
            return (f"Dozen {start}-{start + 11}", set(range(start, start + 12)), 2)
        elif choice == "9":
            return None
        else:
            print("Invalid choice. Please select 1 through 9.")


def spin():
    # randint includes both endpoints, giving 37 possible results including zero.
    return random.randint(0, 36)


def resolve(wager, bet, number):
    # Ignore the display label and check whether the result belongs to the wager.
    # Return net profit/loss: the calling game has not deducted the original stake.
    _, numbers, payout = wager
    if number in numbers:
        return bet * payout
    return -bet


def roulette(balance):
    # Play one spin, returning the unchanged balance if either selection is cancelled.
    print("\nRoulette")

    wager = choose_wager()
    if wager is None:
        return balance

    bet = get_bet(balance)
    if bet is None:
        return balance

    number = spin()
    change = resolve(wager, bet, number)
    print(f"\nYou bet ${bet} on {wager[0]}.")
    print(f"The ball lands on {number} {color(number)}.")
    if change > 0:
        print(f"You win ${change}!")
    else:
        print(f"You lose ${bet}.")

    balance += change  # Add winnings or subtract the lost stake exactly once.
    print(f"New balance: ${balance}")
    input("Press Enter to return to the garage...")
    return balance
