<h1>Password Generator</h1>
<p>
This project is a <strong> command-line-based password generator</strong> written in Python.
It interactively guides the user through password creation while enforcing basic
password-strength rules.
</p>

<hr>
<h2>Features</h2>
<ul>
    <li>Minimum password length enforcement (≥ 6 characters)</li>
    <li>User-controlled inclusion of:
        <ul>
            <li>Alphabets (uppercase & lowercase)</li>
            <li>Digits</li>
            <li>Special characters</li>
        </ul>
    </li>
    <li>Balanced distribution of selected character types</li>
    <li>Randomized final password order</li>
    <li>Input validation with limited retry attempts</li>
</ul>
<hr>
<h2>How It Works</h2>
<h3>1. Password Length</h3>
<p>
The user is prompted to enter the desired password length.
If the value is:
</p>
<ul>
    <li>Non-numeric → the program asks again</li>
    <li>Less than 6 → the program rejects it</li>
    <li>Invalid more than 3 times → the program exits</li>
</ul>
<h3>2. Character Type Selection</h3>
<p>
The user chooses which character types to include:
</p>
<ul>
    <li><strong>Alphabets</strong>: press <code>1</code> to include, <code>0</code> to exclude</li>
    <li><strong>Digits</strong>: press <code>2</code> to include, <code>0</code> to exclude</li>
    <li><strong>Special Characters</strong>: press <code>3</code> to include, <code>0</code> to exclude</li>
</ul>
<p>
At least one character type must be selected for password generation.
</p>
<h3>3. Character Distribution Logic</h3>
<p>
The program calculates how many characters to take from each selected category:
</p>
<ul>
    <li>If all three types are selected, the password is split approximately into thirds</li>
    <li>If only two types are selected, the password is split evenly between them</li>
    <li>Any remaining characters are randomly assigned to one of the active types</li>
</ul>
<h3>4. Password Generation</h3>
<ul>
    <li>Random characters are selected from each enabled character set</li>
    <li>All characters are combined into a list</li>
    <li>The list is shuffled to remove positional patterns</li>
    <li>The final password is displayed</li>
</ul>
<hr>
<h2>Example Interaction</h2>
<pre>
---PASSWORD GENERATOR---
Welcome to the password generator!
To generate a strong password, number of characters must be equal to or greater than 6.

Enter number of characters: 10

Character types:
To include alphabets
    press 1 else 0:
    [->] 1

To include digits
    press 2 else 0:
    [->] 2

To include special character(s)
    press 3 else 0:
    [->] 3
  
Your password is: a9$K2@pZ!4
</pre>
<hr>
<h2>Requirements</h2>
<ul>
    <li>Python 3.x</li>
    <li>Standard library modules:
        <ul>
            <li><code>random</code></li>
            <li><code>string</code></li>
        </ul>
    </li>
</ul>
<hr>
<h2>Notes</h2>
<div class="note">
<p>
This project is intended for <strong>learning and experimentation</strong>.
While it generates reasonably strong passwords, it uses Python's
<code>random</code> module, which is not cryptographically secure.
</p>
</div>
<hr>
<h2>License</h2>
<p>
This project is provided for educational use. You are free to modify,
extend, and experiment with it.
</p>
