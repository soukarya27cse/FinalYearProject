print("\033[1m---GUESSING NUMBER BY MACHINE---\033[0m")
print("Welcome to the guessing number game!")
print("You have to select a number in the range of 1 to 100")
print("And, I will guess the number", end="\n\n")
print("Are you ready?")

for attempts in range(4):
    attempt = input("[Y]es or [N]o: ").lower()
    if attempt == 'y':
        break
    elif attempt == 'n':
        print("I am waiting")
        print("\033[1m\n\033[0m")
    else:
        print("Invalid input")

    if attempts == 3:
        print("Too many attempts")
        print("Exiting program")
        exit()

down, up, n_guess = 1, 100, 1
while True:
    guess = int((up + down) / 2)
    print(f"guess {n_guess}")
    print(f"\t\tMy guess is {guess}")
    print("Am I right?")

    user_input = ''
    for attempts in range(4):
        user_input = input("[Y]es or [N]o: ").lower()
        if user_input not in ['y', 'n']:
            print("Invalid input")
        else:
            break

        if attempts == 3:
            print("Too many attempts")
            print("Exiting program")
            exit()


    if user_input == 'y':
        print("HURRAY! I guessed the number.")
        print(f"#Guess: {n_guess}")
        if n_guess == 1:
            print("I must be God.")
        elif n_guess < 6:
            print("I am a good guesser.")
        else:
            print("Well, I have tried!")
        exit()
    else:
        for attempts in range(4):
            user_input = input("Hint: [U]p or [D]own? ").lower()
            if user_input not in ['u', 'd']:
                print("Invalid input")
            else:
                break

            if attempts == 3:
                print("Too many attempts")
                print("Exiting program")
                exit()

    if user_input == 'u':
        down = guess
    else:
        up = guess
    n_guess += 1
