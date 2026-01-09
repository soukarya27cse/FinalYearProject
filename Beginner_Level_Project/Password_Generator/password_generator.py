import random
import string

print("---PASSWORD GENERATOR---")
print("Welcome to the password generator!")
print("To generate a strong password, number of characters must be equal to or greater than 6.")
invalid_attempt = 0
n_char = 0
while True:
    try:
        n_char = int(input("Enter number of characters: "))
    except ValueError:
        invalid_attempt += 1
        print("Please enter a positive integer\n")
        continue

    if n_char < 6:
        invalid_attempt += 1
        print("Too few characters\n")
    else:
        break

    if invalid_attempt > 3:
        print("Too many attempts")
        print("Exiting the program...")
        exit()


alphabet_set = list(string.ascii_letters)
digit_set = list(string.digits)
punctuation_set = list(string.punctuation)

invalid_attempt = 0

print("\n")
print("Character types: ")
print("To include alphabets\n\tpress 1 else 0: ")
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

combination = alphabet + digit + special_char

part, a, b, c = 0, 0, 0, 0
result = []
if combination.count('0') == 0:
    part = int(.33 * n_char)
    a, b, c = part, part, part
    tmp = n_char - (3 * part)
    if tmp > 0:
        selected = random.choice(['a', 'b', 'c'])
        if selected == 'a':
            a += tmp
        elif selected == 'b':
            b += tmp
        else:
            c += tmp

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

else:
    print("Strong password must contain at least one character type!")
    print("Exiting the program...")
    exit()

for i in range(a):
    result.append(random.choice(alphabet_set))
for i in range(b):
    result.append(random.choice(digit_set))
for i in range(c):
    result.append(random.choice(punctuation_set))
random.shuffle(result)

print(f"Your password is: {''.join(result)}")
print("Exiting the program...")
