# Word Ladder Game

A two-player Word Ladder puzzle game with a Tkinter GUI. Each player transforms a
**start** word into a **goal** word one letter at a time, with every intermediate
step required to be a valid dictionary word. Players can also ban a letter for
their opponent, and a bidirectional BFS engine finds (and validates) the optimal
path between any two words.

## Features

- **Bidirectional BFS solver** — finds a shortest transformation path between the
  start and goal words over the loaded dictionary (`bfs_shortest_path`).
- **Ladder validation** — checks a player-submitted path is legal: every step
  changes exactly one letter and every word is in the dictionary
  (`validate_player_path`, `one_letter_diff`).
- **Letter banning** — each player can ban one letter for their opponent; using
  the banned letter, or ending on a goal that contains it, adds a penalty
  (`apply_penalties`, `count_banned_letter_uses`).
- **Scoring** — compares total tries (base path length + penalties) for both
  players and declares a winner or a tie.
- **Dictionary loading** — reads `words.txt` (or a gzip fallback `words.txt.gz`)
  and filters to words matching the start/goal word length, with a small
  built-in fallback list if neither file is present.

## Files

| File         | Purpose                                                        |
|--------------|-----------------------------------------------------------------|
| `gamee.py`   | Game logic (dictionary loading, BFS, validation, scoring) + Tkinter GUI (`WordLadderGUI`) |
| `words.txt`  | Word list used as the game dictionary                          |

## Requirements

- Python 3 with Tkinter (bundled with most standard Python installs)

## Run

```bash
python gamee.py
```

## How to play

1. Enter a **Start** word and a **Goal** word of the same length, and each
   player's name.
2. Click **Load Dictionary** to load words of that length from `words.txt`.
3. Click **Run Bidirectional BFS** to see a reference shortest path.
4. Each player sets a letter to ban for their opponent, then types their own
   ladder (one word per line, from start to goal) into their text box.
5. Click **Validate Ladders** to check both paths are legal, then
   **Reveal & Score** to compute penalties and see who wins.
