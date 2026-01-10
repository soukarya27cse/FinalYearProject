import random    # used for random selection
import string    # used to access character sets

# displaying program title and instruction
print("---PASSWORD GENERATOR---")
print("Welcome to the password generator!")
print("To generate a strong password, number of characters must be equal to or greater than 6.")

invalid_attempt = 0
n_char = 0

# loop to look for a valid number of characters
while True:
    try:
        # taking user input for password length
        n_char = int(input("Enter number of characters: "))
        # checking minimum length condition
        if n_char < 6:
            invalid_attempt += 1
            print("Too few characters\n")
        else:
            break
    except ValueError:
        # handling non-integer input
        invalid_attempt += 1
        print("Please enter a positive integer\n")

    # exiting after too many invalid attempts
    if invalid_attempt > 3:
        print("Too many attempts")
        print("Exiting the program...")
        exit()

# creating character sets
alphabet_set = list(string.ascii_letters)
digit_set = list(string.digits)
punctuation_set = list(string.punctuation)

invalid_attempt = 0 # resetting invalid attempt counter

print("\n")
print("Character types: ")

# asking to include alphabet
print("To include alphabet\n\tpress 1 else 0: ")
while True:
    alphabet = input("\t[->] ")
    if alphabet not in ['0', '1']:
        print("Please enter either '0' or '1'")
        invalid_attempt += 1
    else:
        invalid_attempt =0
        break

    if invalid_attempt > 3:
        print("Too many attempts")
        print("Exiting the program...")
        exit()

print("\n")

# asking to include sigits
print("To include digits\n\tpress 2 else 0: ")
while True:
    digit = input("\t[->] ")
    if digit not in ['0', '2']:
        print("Please enter either '0' or '2'")
        invalid_attempt += 1
    else:
        invalid_attempt = 0
        break

    if invalid_attempt > 3:
        print("Too many attempts")
        print("Exiting the program...")
        exit()

print("\n")

# asking to include special characters
print("To include special character(s)\n\tpress 3 else 0: ")
while True:
    special_char = input("\t[->] ")
    if special_char not in ['0', '3']:
        print("Please enter either '0' or '3'")
        invalid_attempt += 1
    else:
        break

    if invalid_attempt > 3:
        print("Too many attempts")
        print("Exiting the program...")
        exit()

# combining user choices into a single string
combination = alphabet + digit + special_char

# initializing counters for character distribution
part, a, b, c = 0, 0, 0, 0
result = [] # list to store generated password characters

# if all character types are selected
if combination.count('0') == 0:
    part = int(.33 * n_char)
    a, b, c = part, part, part
    tmp = n_char - (3 * part)

    # distributing remaining character(s) randomly
    if tmp > 0:
        selected = random.choice(['a', 'b', 'c'])
        if selected == 'a':
            a += tmp
        elif selected == 'b':
            b += tmp
        else:
            c += tmp

# if exactly one character type is excluded
elif combination.count('0') == 1:
    part = int(0.33 * n_char)
    tmp = n_char - (3 * part)
    select_a, select_b, select_c =  tuple(combination)
    if select_a == '0':
        b, c = part, part
        if tmp > 0:
            selected = random.choice(['b', 'c'])
            if selected == 'b':
                b += tmp
            else:
                c += tmp
    elif select_b == '0':
        a, c = part, part
        if tmp > 0:
            selected = random.choice(['a', 'c'])
            if selected == 'a':
                a += tmp
            else:
                c += tmp
    else:
        a, b = part, part
        if tmp > 0:
            selected = random.choice(['a', 'b'])
            if selected == 'a':
                a += tmp
            else:
                b += tmp

# if fewer than two character types are selected
else:
    print("Strong password must contain at least one character type!")
    print("Exiting the program...")
    exit()

# adding random characters to the result list
for i in range(a):
    result.append(random.choice(alphabet_set))
for i in range(b):
    result.append(random.choice(digit_set))
for i in range(c):
    result.append(random.choice(punctuation_set))
random.shuffle(result) # shuffling the password characters

# displaying the generated password
print(f"Your password is: {''.join(result)}")
print("Exiting the program...")
