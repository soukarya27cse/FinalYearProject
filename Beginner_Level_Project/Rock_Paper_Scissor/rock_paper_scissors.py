import random

print("\033[1m--ROCK PAPER SCISSORS--\033[0m")
print("Welcome to the Rock Paper Scissors game!")

inventory = {1 : 'paper', 2 : 'rock', 3 : 'scissors'}
match, score_m, score_y = 0, 0, 0

invalid_attempts = 0
print("Enter the number of rounds: ")
while True:
    try:
        match = int(input("[->] "))
    except ValueError:
        invalid_attempts += 1
        print("Please enter a valid input!\n")
        if invalid_attempts > 3:
            print("Too many attempts!")
            exit()
        continue

    if match < 1:
        invalid_attempts += 1
        print("Input must be at least 1!\n")
        if invalid_attempts > 3:
            print("Too many attempts!")
            exit()
    else:
        break

print("For Rock, press 1")
print("For Paper, press 2")
print("For Scissor, press 3")

for turn in range(match):
    user = 0
    print(f"\nRound {turn + 1}")
    computer = random.choice(list(inventory.keys()))
    print("Let's Go!")
    while True:
        try:
            user = int(input("[->] "))
        except ValueError:
            print("Please enter a valid input!\n")
            continue

        if user not in range(1, 4):
            print("Please enter a valid input!\n")
        else:
            break

    print(f"Me: {inventory[computer]}\t You: {inventory[user]}")
    if user == computer:
        continue
    else:
        if (user == 1 and computer == 2) or (user == 3 and computer == 1) or (user == 2 and user == 3):
            score_y += 1
        else:
            score_m += 1

print("\n")
print(f"Your Score: {score_y}")
print(f"My Score: {score_m}")
if score_m > score_y:
    print("I win!")
elif score_m < score_y:
    print("You win!")
else:
    print("It's a draw!")
