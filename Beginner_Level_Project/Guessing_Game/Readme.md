<h1>Guessing Game (Python)</h1>

<p>
A simple command-line guessing game written in Python.
The program randomly selects a number between 1 and 100, and the player must guess it correctly using hints provided by the game.
</p>

<ol>
    <li><strong>Game Overview</strong>
        <ul>
            <li>The game prompts the player to confirm their readiness to play.</li>
            <li>The player has up to 4 attempts to respond correctly (Y or N).</li>
            <li>If the player agrees, the game generates a random number between 1 and 100.</li>
            <li>The player repeatedly guesses the number until:
                <ul>
                    <li>The correct number is guessed, or</li>
                    <li>Too many invalid inputs are given.</li>
                </ul>
            </li>
        </ul>
    </li>

    <li><strong>Features</strong>
        <ul>
            <li>Random number generation using Python’s <code>random</code> module</li>
            <li>Input validation for:
                <ul>
                    <li>Non-integer values</li>
                    <li>Numbers outside the range 1–100</li>
                </ul>
            </li>
            <li>Hint system:
                <ul>
                    <li>Too high</li>
                    <li>Too low</li>
                </ul>
            </li>
            <li>Performance feedback based on number of guesses</li>
            <li>Graceful exit after too many invalid attempts</li>
        </ul>
    </li>

    <li><strong>Performance Messages</strong>
        <ul>
            <li>1 guess → “You must be God!”</li>
            <li>Less than 6 guesses → “You are a good guesser!”</li>
            <li>6 or more guesses → “WELL DONE!”</li>
        </ul>
    </li>

    <li><strong>How to Run</strong>
        <p>Make sure Python 3 is installed, then run:</p>
        <pre><code>python guessing_game.py</code></pre>
    </li>

    <li><strong>Requirements</strong>
        <ul>
            <li>Python 3.x</li>
            <li>Uses only the built-in <code>random</code> module</li>
        </ul>
    </li>

    <li><strong>Learning Objectives</strong>
        <ul>
            <li>Loops and conditionals</li>
            <li>Exception handling (<code>try</code> / <code>except</code>)</li>
            <li>Input validation</li>
            <li>Basic game logic and control flow</li>
        </ul>
    </li>
</ol>

</body>
</html>
