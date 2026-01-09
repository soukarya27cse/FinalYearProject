import random

print("--WORD GUESSING GAME--")
print("Welcome to the guessing game")
print("I will take some words from you. And I will select a word from the list.")
print("And, my dear friend, You have to guess the word.", end='\n\n')
print("Are you ready?")

signal = False
for attempts in range(0, 4):
    attempt = input("[Y]es or [N]o: ").lower()
    if attempt == "y":
        signal = True
        break
    elif attempt == "n":
            print("I am waiting for you...\n")
    else:
        print("User input is not valid!\n")

if not signal:
    print("Too many attempts")
    print("Exiting the game...")
    exit()

cardinality = 0
n_guess = 1
invalid_guess_attempts = 0
print("\n#items: ")

while True:
    try:
        cardinality = int(input("Enter: "))
    except ValueError:
        invalid_guess_attempts += 1
        print("Invalid input. Please enter a valid number.\n")
        if invalid_guess_attempts > 3:
            print("Too many attempts")
            print("Exiting the game...")
            exit()
        continue

    if cardinality < 2:
        print("Please enter at least 2.\n")
        invalid_guess_attempts += 1
        if invalid_guess_attempts > 3:
            print("Too many attempts")
            print("Exiting the game...")
            exit()
    else:
        break

bucket = []
print("ENTER WORDS: ")
for _item in range(cardinality):
    bucket.append(input(f"b{_item + 1}: ").lower())

print("\n")
print("Here is your word-list: ")
print(bucket, end="\n")

selected_word = random.choice(bucket)
print("I have selected a word")
print("Guess the word\n")

while True:
     print(f"\033[1mGuess {n_guess}\033[0m")
     guess_word = input("Guess: ").lower()

     if guess_word in bucket:
        invalid_guess_attempts = 0
        if guess_word == selected_word:
            print("\n\033[1mHurray! You guessed the word!\033[0m")
            print(f"#guess: {n_guess}")
            if n_guess == 1:
                print("You must be God!")
            elif n_guess < 6:
                print("You are a good guesser!")
            else:
                print("Well done!")
                print("Exiting the game...")
            exit()
        else:
            print("Comment: Try again!\n")
     else:
        print(f"Comment: {guess_word} not in the list. Please try again.\n")
     n_guess += 1
