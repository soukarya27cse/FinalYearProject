import random

print("--NUMBER GUESSING GAME--")
print("Welcome to the guessing game")
print("I am thinking of a number between 1 and 100")
print("And, my dear friend, You have to guess the number.", end='\n\n')
print("Are you ready?")

signal = False
for attempts in range(0, 4):
    ready = input("[Y]es or [N]o: ").lower()
    if ready == "y":
        signal = True
        break
    elif ready == "n":
        print("You have to guess the number.")
        print("I am waiting for you to guess the number.\n")
    else:
        print("User input is not valid.")


if signal:
    n_guess = 1
    invalid_guess_attempts = 0
    generated = random.randint(1, 100)
    print("I have guessed the number!")
    print("Your turn!", end="\n\n")

    while True:
        try:
            guess = int(input("Enter your guess: "))
        except ValueError:
            invalid_guess_attempts += 1
            print("Please enter a valid number. An integer in the range from 1 to 100.\n")
            if invalid_guess_attempts > 3:
                print("Too many attempts!")
                print("Exiting the game...")
                break
            continue

        if guess > 100 or guess < 1:
            invalid_guess_attempts += 1
            print("Please enter a valid number. An integer in the range from 1 to 100.\n")
            if invalid_guess_attempts > 3:
                print("Too many attempts!")
                print("Exiting the game...")
                break
        else:
            invalid_guess_attempts = 0
            if guess == generated:
                print("Hurray! You guessed the number!")
                print(f"#guess: {n_guess}\n")
                if n_guess == 1:
                    print("You must be God!")
                elif n_guess < 6:
                    print("You are a good guesser!")
                else:
                    print("WELL DONE!")
                print("Exiting the game...")
                break
            else:
                print(f"Guess {n_guess}")
                if guess > generated:
                    print("Comment: Too high\n")
                else:
                    print("Comment: Too low\n")
                n_guess += 1

else:
    print("Too many attempts!")
    print("Exiting the game...")
