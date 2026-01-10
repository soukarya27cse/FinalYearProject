<h1>Guessing Number by Machine</h1>

<p>
This project is a <strong>command-line guessing game</strong> written in Python.
In this game, the <em>user selects a number</em> between 1 and 100, and the
<strong>machine attempts to guess it</strong> using logical hints provided by the user.
</p>

<hr>

<h2>Program Overview</h2>

<ul>
    <li>The user silently chooses a number between <strong>1 and 100</strong></li>
    <li>The machine makes a guess</li>
    <li>The user replies whether the guess is:
        <ul>
            <li>Correct</li>
            <li>Too high</li>
            <li>Too low</li>
        </ul>
    </li>
    <li>The machine refines its guesses until it succeeds</li>
</ul>

<hr>

<h2>User Interaction Flow</h2>

<h3>1. Game Start Confirmation</h3>
<p>
The program first confirms whether the user is ready to play.
The user has up to <strong>4 attempts</strong> to respond correctly with:
</p>

<ul>
    <li><code>y</code> – to start the game</li>
    <li><code>n</code> – to delay the start</li>
</ul>

<p>
Invalid inputs are handled, and exceeding the allowed attempts causes the program to exit safely.
</p>

<hr>

<h3>2. Guessing Strategy</h3>

<p>
The machine initializes the guessing range as:
</p>

<pre>
Lower bound (down) = 1
Upper bound (up)   = 100
</pre>

<p>
Each guess is calculated as the midpoint of the current range:
</p>

<pre>
guess = (up + down) / 2
</pre>

<p>
This approach is known as <strong>Binary Search</strong>.
</p>

<div class="highlight">
<strong>Key Insight:</strong><br>
Instead of guessing randomly, the program always halves the search space,
making it extremely efficient.
</div>

<hr>

<h3>3. User Feedback</h3>

<p>
After each guess, the user provides feedback:
</p>

<ul>
    <li><code>Y</code> – the guess is correct</li>
    <li><code>U</code> – the actual number is higher</li>
    <li><code>D</code> – the actual number is lower</li>
</ul>

<p>
Based on the hint:
</p>

<ul>
    <li><strong>Up (u)</strong> → the lower bound is updated</li>
    <li><strong>Down (d)</strong> → the upper bound is updated</li>
</ul>

<p>
This guarantees that the machine never repeats a wrong guess.
</p>

<hr>

<h2>Guess Count and Termination</h2>

<p>
Each guess increments a counter (<code>n_guess</code>) which is used to:
</p>

<ul>
    <li>Display the number of guesses taken</li>
    <li>Provide humorous feedback based on performance</li>
</ul>

<pre>
If guesses == 1  → "I must be God."
If guesses < 6   → "I am a good guesser."
Else             → "Well, I have tried!"
</pre>

<hr>

<h2>Why the Maximum Guess is 7</h2>

<div class="note">
<strong>Observation:</strong><br>
The maximum number of guesses never exceeds <strong>7</strong>.
</div>

<p>
This is not accidental. The guessing strategy follows <strong>binary search</strong>,
whose time complexity is:
</p>

<pre>
O(log₂ N)
</pre>

<p>
For a range of 1 to 100:
</p>

<pre>
log₂(100) ≈ 6.64
</pre>

<p>
Since the number of guesses must be an integer, the worst-case number of guesses is:
</p>

<pre>
⌈log₂(100)⌉ = 7
</pre>

<div class="highlight">
This explains why the machine <strong>never needs more than 7 guesses</strong>,
regardless of the chosen number.
</div>

<hr>

<h2>Error Handling</h2>

<ul>
    <li>Invalid inputs are detected and rejected</li>
    <li>User is given up to 4 retries for each prompt</li>
    <li>Program exits gracefully after repeated invalid attempts</li>
</ul>

<hr>

<h2>Requirements</h2>

<ul>
    <li>Python 3.x</li>
    <li>No external libraries required</li>
</ul>

<hr>

<h2>Educational Value</h2>

<p>
This project demonstrates:
</p>

<ul>
    <li>Binary search in practice</li>
    <li>Human–computer interaction via CLI</li>
    <li>Input validation and control flow</li>
    <li>Logarithmic time complexity</li>
</ul>

<hr>

<h2>Conclusion</h2>

<p>
This guessing game is a clean and effective illustration of how
<strong>mathematical reasoning (log₂)</strong> directly translates into
<strong>efficient algorithms</strong>.
</p>

<p>
It is both a fun game and a solid educational example of
<strong>divide-and-conquer strategies</strong>.
</p>

