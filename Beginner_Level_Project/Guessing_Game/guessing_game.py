import random

print("--GUESSING GAME--")
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
        if attempts < 3:
            print("You have to guess the number.")
            print("I am waiting for you to guess the number.")
        else:
            print("Exiting the game.")
    else:
        if attempts < 3:
            print("User input is not valid.")
        else:
            print("Exiting the game...")

if signal:
    n_guess = 1
    generated = random.randint(1, 100)
    print("I have guessed the number!")
    print("Your turn!", end="\n\n")
    attempts = 0
    while True:
        guess = int(input("Enter your guess: "))
        if guess in range(1, 101):
            attempts = 0
            if guess == generated:
                print("Hurray! You guessed the number!")
                print(f"#guess: {n_guess}")
                if n_guess == 1:
                    print("You must be God!")
                elif n_guess < 5:
                    print("You are a good guesser!")
                else:
                    print("WELL DONE!")
                print("\n")
                print("Exiting the game...")
                break
            else:
                if guess > generated:
                    print("Too high ")
                else:
                    print("Too low")
                n_guess += 1
                print("\n")
        else:
            if attempts < 3:
                print("user input is not valid.")
            else:
                print("Exiting the game...")
                break
            attempts += 1
