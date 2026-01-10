# importing the 'random' module to generate a random number
import random

# displaying game title and introduction
print("--NUMBER GUESSING GAME--")
print("Welcome to the guessing game")
print("I am thinking of a number between 1 and 100")
print("And, my dear friend, you have to guess the number.", end='\n\n')
print("Are you ready?")

signal = False # Flag to check whether the user is ready to play

# loop to ask the user if they are ready (maximum 4 attempts)
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

# if user agreed to play
if signal:
    n_guess = 1 # counter to tract the number of valid guesses
    invalid_guess_attempts = 0 # counter for invalid guess attempts
    generated = random.randint(1, 100) # generating random numbers between 1 and 100
    print("I have guessed the number!") 
    print("Your turn!", end="\n\n")

    # infinite loop until the user guesses correctly or exits
    while True:
        try:
            # taking the user's guess
            guess = int(input("Enter your guess: "))
        except ValueError:
            # handling non-integer input
            invalid_guess_attempts += 1
            print("Please enter a valid number. An integer in the range from 1 to 100.\n")
            if invalid_guess_attempts > 3:
                print("Too many attempts!")
                print("Exiting the game...")
                break
            continue

        # checking if the number is outside the valid range
        if guess > 100 or guess < 1:
            invalid_guess_attempts += 1
            print("Please enter a valid number. An integer in the range from 1 to 100.\n")
            if invalid_guess_attempts > 3:
                print("Too many attempts!")
                print("Exiting the game...")
                break
        else:
            # reset invalid attempts 
            invalid_guess_attempts = 0

            # if user guessed the correct number
            if guess == generated:
                print("\033[1m\nHurray! You guessed the number!\033[0m")
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
                # guess handling if the guess is not right
                print(f"Guess {n_guess}")
                if guess > generated:
                    print("HINT: Too high\n")
                else:
                    print("HINT: Too low\n")
                n_guess += 1 # increment guess count

# if user never agreed to play or just messing around
else:
    print("Too many attempts!")
    print("Exiting the game...")
