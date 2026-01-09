<h1>Rock Paper Scissors Game (Python)</h1>

<p>
A simple command-line implementation of the classic <strong>Rock Paper Scissors </strong> game written in Python.
The player competes against the computer over a user-defined number of rounds.
</p>

<ol>
    <li>
        <strong>Game Overview</strong>
        <ul>
            <li>The game welcomes the player and explains the rules.</li>
            <li>The player enters the number of rounds to be played.</li>
            <li>In each round:
                <ul>
                    <li>The computer randomly selects Rock, Paper, or Scissors.</li>
                    <li>The player selects their choice using numeric input.</li>
                    <li>The round winner is determined based on standard game rules.</li>
                </ul>
            </li>
            <li>Scores are tracked across all rounds.</li>
            <li>The final winner is announced at the end of the game.</li>
        </ul>
    </li>
    <li>
        <strong>Controls</strong>
        <ul>
            <li><code>1</code> → Rock</li>
            <li><code>2</code> → Paper</li>
            <li><code>3</code> → Scissor</li>
        </ul>
    </li>
    <li>
        <strong>Features</strong>
        <ul>
            <li>Random computer choice using Python’s <code>random</code> module</li>
            <li>User-defined number of rounds</li>
            <li>Input validation with attempt limits</li>
            <li>Score tracking for both player and computer</li>
            <li>Clear round-by-round output</li>
            <li>Final match result (Win / Lose / Draw)</li>
        </ul>
    </li>
    <li>
        <strong>Scoring Rules</strong>
        <ul>
            <li>Rock beats Scissor</li>
            <li>Scissor beats Paper</li>
            <li>Paper beats Rock</li>
            <li>Identical choices result in a draw for that round</li>
        </ul>
    </li>
    <li>
        <strong>How to Run</strong>
        <p>Ensure Python 3 is installed, then run:</p>
        <pre><code>python rock_paper_scissor.py</code></pre>
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
            <li>Loops and conditional logic</li>
            <li>Dictionary usage</li>
            <li>Input validation and error handling</li>
            <li>Randomization</li>
            <li>Score tracking and game flow design</li>
        </ul>
    </li>
</ol>
