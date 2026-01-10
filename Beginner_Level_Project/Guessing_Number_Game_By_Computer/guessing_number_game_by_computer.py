# displaying the game title and introduction
print("\033[1m---GUESSING NUMBER BY MACHINE---\033[0m")
print("Welcome to the guessing number game!")
print("You have to select a number in the range of 1 to 100")
print("And, I will guess the number", end="\n\n")
print("Are you ready?")

# loop to check if the user is ready (maximum 4 attempts)
for attempts in range(4):
    attempt = input("[Y]es or [N]o: ").lower()
    if attempt == 'y':
        break # user's ready, break the for loop and proceed
    elif attempt == 'n': # user not ready
        print("I am waiting")
        print("\033[1m\n\033[0m")
    else: # handling invalid input
        print("Invalid input")

    # exiting the program after too many invalid attempts
    if attempts == 3:
        print("Too many attempts")
        print("Exiting program")
        exit()
        
## initializing lower and upper bound, and guess counter
down, up, n_guess = 1, 100, 1

# infinite loop 
while True:
    # machine makes a guess
    guess = int((up + down) / 2)
    print(f"guess {n_guess}")
    print(f"\t\tMy guess is {guess}")
    print("Am I right?")

    user_input = '' # variable to store user response
    for attempts in range(4):
        user_input = input("[Y]es or [N]o: ").lower()
        if user_input not in ['y', 'n']: # handling invalid input
            print("Invalid input")
        else:
            break

        # exiting after too many invalid attempts
        if attempts == 3:
            print("Too many attempts")
            print("Exiting program")
            exit()

    # if machine guessed correctly
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
        # asking the user for a hint
        for attempts in range(4):
            user_input = input("Hint: [U]p or [D]own? ").lower()
            if user_input not in ['u', 'd']:
                # handling invalid input
                print("Invalid input")
            else:
                break
            
            # exiting after too many invalid attempts
            if attempts == 3:
                print("Too many attempts")
                print("Exiting program")
                exit()

    # adjusting the guessing range based on user hint
    if user_input == 'u':
        down = guess
    else:
        up = guess
    n_guess += 1 # increment guess counter
