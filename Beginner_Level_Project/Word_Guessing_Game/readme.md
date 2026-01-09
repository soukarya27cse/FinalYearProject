<h1>Word Guessing Game (Python)</h1>

<p>
A simple command-line word guessing game written in Python.
The program collects a list of words from the user, randomly selects one word,
and challenges the player to guess it correctly.
</p>

<ol>
    <li>
        <strong>Game Overview</strong>
        <ul>
            <li>The game asks the player if they are ready to play.</li>
            <li>The player has up to <strong>4 attempts</strong> to respond correctly (<code>Y</code> or <code>N</code>).</li>
            <li>If the player agrees, the game asks for the number of words to be entered.</li>
            <li>The player provides a list of words.</li>
            <li>The game randomly selects one word from the list.</li>
            <li>The player keeps guessing until the correct word is found.</li>
        </ul>
    </li>
    <li>
        <strong>Features</strong>
        <ul>
            <li>Random word selection using Python’s <code>random</code> module</li>
            <li>User-defined word list</li>
            <li>Input validation for:
                <ul>
                    <li>Non-integer input when entering the number of words</li>
                    <li>Invalid number of words (less than 2)</li>
                </ul>
            </li>
            <li>Case-insensitive word handling</li>
            <li>Guess counter with performance feedback</li>
            <li>Graceful exit after too many invalid attempts</li>
        </ul>
    </li>
    <li>
        <strong>Performance Messages</strong>
        <ul>
            <li><strong>1 guess</strong> → “You must be God!”</li>
            <li><strong>Less than 6 guesses</strong> → “You are a good guesser!”</li>
            <li><strong>6 or more guesses</strong> → “Well done!”</li>
        </ul>
    </li>
    <li>
        <strong>How to Run</strong>
        <p>Make sure Python 3 is installed, then run:</p>
        <pre><code>python3 word_guessing_game.py</code></pre>
    </li>
    <li>
        <strong>Requirements</strong>
        <ul>
            <li>Python 3.x</li>
            <li>Uses only the built-in <code>random</code> module</li>
        </ul>
    </li>
    <li>
        <strong>Learning Objectives</strong>
        <ul>
            <li>Loops and conditional statements</li>
            <li>User input handling</li>
            <li>Exception handling (<code>try</code> / <code>except</code>)</li>
            <li>State management using counters</li>
            <li>Basic game logic and control flow</li>
        </ul>
    </li>
</ol>
