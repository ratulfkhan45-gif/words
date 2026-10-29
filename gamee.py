#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gzip
from collections import deque
from functools import lru_cache
from typing import List, Optional, Set, Dict

import tkinter as tk
from tkinter import ttk, messagebox

ALPHABET = "abcdefghijklmnopqrstuvwxyz"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORDS_PATH = os.path.join(BASE_DIR, "words.txt")
WORDS_GZ_PATH = os.path.join(BASE_DIR, "words.txt.gz")

_LEXICON: Optional[Set[str]] = None

DEFAULT_WORDS = {
    "hit", "hot", "dot", "dog", "lot", "log", "cog",
    "cat", "cot", "fog", "fig", "fin", "fan", "fun", "pun", "pin", "pan",
    "pit", "pot", "put", "but", "bat", "bet", "bit", "bot", "bog", "bag", "bug",
    "rag"
}


def _add_lines_of_length(lines, word_len: int, out: Set[str]) -> None:
    for line in lines:
        w = line.strip().lower()
        if len(w) == word_len and w.isalpha():
            out.add(w)


def load_dictionary(word_len: int, extra_words: Optional[Set[str]] = None) -> Set[str]:
    words: Set[str] = set()

    try:
        if os.path.exists(WORDS_PATH):
            with open(WORDS_PATH, "r", encoding="utf-8") as f:
                _add_lines_of_length(f, word_len, words)

        elif os.path.exists(WORDS_GZ_PATH):
            with gzip.open(WORDS_GZ_PATH, "rt", encoding="utf-8") as f:
                _add_lines_of_length(f, word_len, words)

        else:
            for w in DEFAULT_WORDS:
                if len(w) == word_len:
                    words.add(w)

    except UnicodeDecodeError:
        with open(WORDS_PATH, "r", encoding="latin-1") as f:
            _add_lines_of_length(f, word_len, words)

    if extra_words:
        words |= {
            w.lower()
            for w in extra_words
            if len(w) == word_len and w.isalpha()
        }

    return words


@lru_cache(maxsize=200_000)
def _neighbors_cached(word: str) -> tuple:
    assert _LEXICON is not None, "Lexicon not initialized."

    out = []
    wlist = list(word)

    for i in range(len(word)):
        original = wlist[i]

        for c in ALPHABET:
            if c == original:
                continue

            wlist[i] = c
            candidate = "".join(wlist)

            if candidate in _LEXICON:
                out.append(candidate)

        wlist[i] = original

    return tuple(out)


def neighbors(word: str, lexicon: Set[str]) -> List[str]:
    if _LEXICON is not None:
        return list(_neighbors_cached(word))

    out = []
    wlist = list(word)

    for i in range(len(word)):
        original = wlist[i]

        for c in ALPHABET:
            if c == original:
                continue

            wlist[i] = c
            candidate = "".join(wlist)

            if candidate in lexicon:
                out.append(candidate)

        wlist[i] = original

    return out


def bfs_shortest_path(start: str, goal: str, words: Set[str]) -> Optional[List[str]]:
    start = start.lower()
    goal = goal.lower()

    if start == goal:
        return [start]

    if len(start) != len(goal):
        return None

    words = set(words)
    words.add(start)
    words.add(goal)

    q_start = deque([start])
    q_goal = deque([goal])

    parent_start: Dict[str, Optional[str]] = {start: None}
    parent_goal: Dict[str, Optional[str]] = {goal: None}

    visited_start = {start}
    visited_goal = {goal}

    def expand_frontier(queue, visited_self, visited_other, parent_self):
        if not queue:
            return None

        current = queue.popleft()

        for nxt in neighbors(current, words):
            if nxt in visited_self:
                continue

            parent_self[nxt] = current

            if nxt in visited_other:
                return nxt

            visited_self.add(nxt)
            queue.append(nxt)

        return None

    while q_start and q_goal:
        if len(q_start) <= len(q_goal):
            meet = expand_frontier(q_start, visited_start, visited_goal, parent_start)
        else:
            meet = expand_frontier(q_goal, visited_goal, visited_start, parent_goal)

        if meet is not None:
            left = []
            node = meet

            while node is not None:
                left.append(node)
                node = parent_start.get(node)

            left.reverse()

            right = []
            node = parent_goal.get(meet)

            while node is not None:
                right.append(node)
                node = parent_goal.get(node)

            return left + right

    return None


def one_letter_diff(a: str, b: str) -> bool:
    if len(a) != len(b):
        return False

    return sum(1 for x, y in zip(a, b) if x != y) == 1


def validate_player_path(path: List[str], start: str, goal: str, words: Set[str]) -> Optional[str]:
    if not path:
        return "Empty path."

    path = [w.lower() for w in path]
    start = start.lower()
    goal = goal.lower()

    if path[0] != start:
        return f"Path must start with '{start}'."

    if path[-1] != goal:
        return f"Path must end with '{goal}'."

    L = len(start)

    for w in path:
        if len(w) != L:
            return "All words must have the same length as start and goal."

        if not w.isalpha():
            return "Words must be alphabetic."

        if w not in words and w not in {start, goal}:
            return f"Word '{w}' is not in dictionary."

    for a, b in zip(path, path[1:]):
        if not one_letter_diff(a, b):
            return f"'{a}' -> '{b}' is not a one-letter change."

    return None


def count_banned_letter_uses(path: List[str], banned_letter: str) -> int:
    banned_letter = banned_letter.lower()
    count = 0

    for index, word in enumerate(path):
        if index == 0:
            continue

        if banned_letter in word.lower():
            count += 1

    return count


def apply_penalties(path: List[str], banned_letter_for_player: str, goal: str, opponent_banned_letter: str) -> dict:
    base_tries = max(0, len(path) - 1)
    ban_uses = count_banned_letter_uses(path, opponent_banned_letter)
    ban_penalty = 3 * ban_uses
    goal_letter_penalty = 2 if banned_letter_for_player.lower() in set(goal.lower()) else 0
    total = base_tries + ban_penalty + goal_letter_penalty

    return {
        "base_tries": base_tries,
        "ban_uses": ban_uses,
        "ban_penalty": ban_penalty,
        "goal_letter_penalty": goal_letter_penalty,
        "total_tries": total
    }


class WordLadderGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Word Ladder Game")
        self.geometry("1000x720")
        self.minsize(920, 640)

        self.words: Set[str] = set()
        self.loaded_word_length: Optional[int] = None
        self.shortest_path: Optional[List[str]] = None

        top = ttk.LabelFrame(self, text="Setup")
        top.pack(fill="x", padx=12, pady=8)

        ttk.Label(top, text="Start:").grid(row=0, column=0, padx=6, pady=6, sticky="e")
        self.start_var = tk.StringVar(value="hit")
        ttk.Entry(top, textvariable=self.start_var, width=14).grid(row=0, column=1, padx=6, pady=6)

        ttk.Label(top, text="Goal:").grid(row=0, column=2, padx=6, pady=6, sticky="e")
        self.goal_var = tk.StringVar(value="cog")
        ttk.Entry(top, textvariable=self.goal_var, width=14).grid(row=0, column=3, padx=6, pady=6)

        ttk.Label(top, text="Player 1:").grid(row=0, column=4, padx=6, pady=6, sticky="e")
        self.p1_var = tk.StringVar(value="Player 1")
        ttk.Entry(top, textvariable=self.p1_var, width=16).grid(row=0, column=5, padx=6, pady=6)

        ttk.Label(top, text="Player 2:").grid(row=0, column=6, padx=6, pady=6, sticky="e")
        self.p2_var = tk.StringVar(value="Player 2")
        ttk.Entry(top, textvariable=self.p2_var, width=16).grid(row=0, column=7, padx=6, pady=6)

        ttk.Button(top, text="Load Dictionary", command=self.on_load_dict).grid(row=1, column=0, padx=6, pady=6, sticky="ew", columnspan=2)
        ttk.Button(top, text="Run Bidirectional BFS", command=self.on_run_bfs).grid(row=1, column=2, padx=6, pady=6, sticky="ew", columnspan=2)
        ttk.Button(top, text="Reset", command=self.on_reset).grid(row=1, column=4, padx=6, pady=6, sticky="ew", columnspan=2)

        ban_frame = ttk.LabelFrame(self, text="Hidden Banned Letters")
        ban_frame.pack(fill="x", padx=12, pady=8)

        ttk.Label(ban_frame, text="P1 bans for P2:").grid(row=0, column=0, padx=6, pady=6, sticky="e")
        self.ban1_var = tk.StringVar()
        ttk.Entry(ban_frame, textvariable=self.ban1_var, width=8, show="*").grid(row=0, column=1, padx=6, pady=6)

        ttk.Label(ban_frame, text="P2 bans for P1:").grid(row=0, column=2, padx=6, pady=6, sticky="e")
        self.ban2_var = tk.StringVar()
        ttk.Entry(ban_frame, textvariable=self.ban2_var, width=8, show="*").grid(row=0, column=3, padx=6, pady=6)

        ttk.Label(
            ban_frame,
            text="If your chosen banned letter occurs in the goal word, you get +2 tries."
        ).grid(row=0, column=4, padx=12, pady=6, sticky="w")

        ladder_frame = ttk.LabelFrame(self, text="Submit Ladders")
        ladder_frame.pack(fill="x", padx=12, pady=8)

        ttk.Label(ladder_frame, text="P1 Ladder:").grid(row=0, column=0, padx=6, pady=6, sticky="e")
        self.p1_ladder_var = tk.StringVar(value="hit hot dot dog cog")
        ttk.Entry(ladder_frame, textvariable=self.p1_ladder_var, width=90).grid(row=0, column=1, padx=6, pady=6, sticky="ew")

        ttk.Label(ladder_frame, text="P2 Ladder:").grid(row=1, column=0, padx=6, pady=6, sticky="e")
        self.p2_ladder_var = tk.StringVar(value="hit hot lot log cog")
        ttk.Entry(ladder_frame, textvariable=self.p2_ladder_var, width=90).grid(row=1, column=1, padx=6, pady=6, sticky="ew")

        ladder_frame.columnconfigure(1, weight=1)

        btns = ttk.Frame(self)
        btns.pack(fill="x", padx=12, pady=6)

        ttk.Button(btns, text="Validate Ladders", command=self.on_validate).pack(side="left", padx=6)
        ttk.Button(btns, text="Reveal & Score", command=self.on_score).pack(side="left", padx=6)

        out_frame = ttk.Frame(self)
        out_frame.pack(fill="both", expand=True, padx=12, pady=8)

        bfs_box = ttk.LabelFrame(out_frame, text="Shortest Path / Dictionary Info")
        bfs_box.pack(side="left", fill="both", expand=True, padx=(0, 6))

        self.bfs_text = tk.Text(bfs_box, height=14, wrap="word")
        self.bfs_text.pack(fill="both", expand=True, padx=6, pady=6)

        res_box = ttk.LabelFrame(out_frame, text="Results & Scores")
        res_box.pack(side="left", fill="both", expand=True, padx=(6, 0))

        self.res_text = tk.Text(res_box, height=14, wrap="word")
        self.res_text.pack(fill="both", expand=True, padx=6, pady=6)

        self.status_var = tk.StringVar(value="Ready")
        status = ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w")
        status.pack(side="bottom", fill="x")

    def parse_ladder(self, text: str) -> List[str]:
        text = (text or "").replace(",", " ")
        return [w.strip().lower() for w in text.split() if w.strip()]

    def set_status(self, msg: str):
        self.status_var.set(msg)
        self.update_idletasks()

    def append_bfs(self, msg: str):
        self.bfs_text.insert("end", msg + "\n")
        self.bfs_text.see("end")

    def append_res(self, msg: str):
        self.res_text.insert("end", msg + "\n")
        self.res_text.see("end")

    def clear_outputs(self):
        self.bfs_text.delete("1.0", "end")
        self.res_text.delete("1.0", "end")

    def load_words_for_current_input(self) -> bool:
        start = self.start_var.get().strip().lower()
        goal = self.goal_var.get().strip().lower()

        if not start or not goal:
            messagebox.showwarning("Missing Input", "Please enter both start and goal words.")
            return False

        if not start.isalpha() or not goal.isalpha():
            messagebox.showerror("Invalid Input", "Start and goal words must contain letters only.")
            return False

        if len(start) != len(goal):
            messagebox.showerror("Length Mismatch", "Start and goal words must have the same length.")
            return False

        word_len = len(start)

        if self.words and self.loaded_word_length == word_len:
            return True

        self.words = load_dictionary(word_len, extra_words={start, goal})
        self.words.add(start)
        self.words.add(goal)
        self.loaded_word_length = word_len

        global _LEXICON
        _LEXICON = frozenset(self.words)
        _neighbors_cached.cache_clear()

        if not self.words:
            messagebox.showerror("Dictionary Error", "No words were loaded.")
            return False

        return True

    def on_load_dict(self):
        self.clear_outputs()

        self.words = set()
        self.loaded_word_length = None

        if not self.load_words_for_current_input():
            return

        start = self.start_var.get().strip().lower()

        msg = f"Dictionary loaded with {len(self.words)} words of length {len(start)}."
        self.set_status(msg)
        self.append_bfs(msg)

        if os.path.exists(WORDS_PATH):
            self.append_bfs(f"Loaded from: {WORDS_PATH}")
        elif os.path.exists(WORDS_GZ_PATH):
            self.append_bfs(f"Loaded from: {WORDS_GZ_PATH}")
        else:
            self.append_bfs("words.txt not found. Using built-in demo dictionary.")

        sample = sorted(self.words)[:80]
        self.append_bfs("\nSample loaded words:")
        self.append_bfs(", ".join(sample))

    def on_run_bfs(self):
        if not self.load_words_for_current_input():
            return

        self.clear_outputs()

        start = self.start_var.get().strip().lower()
        goal = self.goal_var.get().strip().lower()

        self.set_status("Running bidirectional BFS...")

        path = bfs_shortest_path(start, goal, self.words)
        self.shortest_path = path

        if path:
            self.append_bfs(f"Shortest path: {' -> '.join(path)}")
            self.append_bfs(f"Steps: {len(path) - 1}")
        else:
            self.append_bfs("No path found with the current dictionary.")

        self.set_status("BFS complete.")

    def on_validate(self):
        if not self.load_words_for_current_input():
            return

        start = self.start_var.get().strip().lower()
        goal = self.goal_var.get().strip().lower()

        p1_path = self.parse_ladder(self.p1_ladder_var.get())
        p2_path = self.parse_ladder(self.p2_ladder_var.get())

        err1 = validate_player_path(p1_path, start, goal, self.words)
        err2 = validate_player_path(p2_path, start, goal, self.words)

        self.res_text.delete("1.0", "end")

        if err1:
            self.append_res(f"{self.p1_var.get()}'s ladder invalid: {err1}")
        else:
            self.append_res(f"{self.p1_var.get()}'s ladder is valid. Steps = {max(0, len(p1_path) - 1)}")

        if err2:
            self.append_res(f"{self.p2_var.get()}'s ladder invalid: {err2}")
        else:
            self.append_res(f"{self.p2_var.get()}'s ladder is valid. Steps = {max(0, len(p2_path) - 1)}")

        if not err1 and not err2:
            self.append_res("Both ladders are valid. You may now Reveal & Score.")

        self.set_status("Validation complete.")

    def on_score(self):
        if not self.load_words_for_current_input():
            return

        start = self.start_var.get().strip().lower()
        goal = self.goal_var.get().strip().lower()

        p1 = self.p1_var.get().strip() or "Player 1"
        p2 = self.p2_var.get().strip() or "Player 2"

        ban1 = self.ban1_var.get().strip().lower()
        ban2 = self.ban2_var.get().strip().lower()

        if len(ban1) != 1 or not ban1.isalpha():
            messagebox.showwarning("Invalid Letter", f"{p1}'s banned letter is invalid. Using 'q'.")
            ban1 = "q"
            self.ban1_var.set(ban1)

        if len(ban2) != 1 or not ban2.isalpha():
            messagebox.showwarning("Invalid Letter", f"{p2}'s banned letter is invalid. Using 'z'.")
            ban2 = "z"
            self.ban2_var.set(ban2)

        p1_path = self.parse_ladder(self.p1_ladder_var.get())
        p2_path = self.parse_ladder(self.p2_ladder_var.get())

        err1 = validate_player_path(p1_path, start, goal, self.words)
        err2 = validate_player_path(p2_path, start, goal, self.words)

        self.res_text.delete("1.0", "end")

        if err1 or err2:
            if err1:
                self.append_res(f"{p1}'s ladder invalid: {err1}")
            if err2:
                self.append_res(f"{p2}'s ladder invalid: {err2}")

            self.set_status("Fix invalid ladders before scoring.")
            return

        self.append_res("=== Revealed Banned Letters ===")
        self.append_res(f"{p1} banned '{ban1}' for {p2}.")
        self.append_res(f"{p2} banned '{ban2}' for {p1}.")

        score1 = apply_penalties(p1_path, ban1, goal, ban2)
        score2 = apply_penalties(p2_path, ban2, goal, ban1)

        def show_score(player, path, own_ban, opponent_ban, score):
            self.append_res(f"\n--- {player} ---")
            self.append_res("Path: " + " -> ".join(path))
            self.append_res(f"Base tries: {score['base_tries']}")
            self.append_res(f"Opponent banned letter '{opponent_ban}' used {score['ban_uses']} time(s): +{score['ban_penalty']}")
            self.append_res(f"Goal-letter penalty for chosen ban '{own_ban}': +{score['goal_letter_penalty']}")
            self.append_res(f"Total tries: {score['total_tries']}")

        show_score(p1, p1_path, ban1, ban2, score1)
        show_score(p2, p2_path, ban2, ban1, score2)

        self.append_res("\n=== Result ===")

        if score1["total_tries"] < score2["total_tries"]:
            self.append_res(f"Winner: {p1}")
        elif score2["total_tries"] < score1["total_tries"]:
            self.append_res(f"Winner: {p2}")
        else:
            self.append_res("Result: Tie")

        self.set_status("Scoring complete.")

    def on_reset(self):
        self.words = set()
        self.loaded_word_length = None
        self.shortest_path = None

        self.start_var.set("hit")
        self.goal_var.set("cog")
        self.p1_var.set("Player 1")
        self.p2_var.set("Player 2")
        self.ban1_var.set("")
        self.ban2_var.set("")
        self.p1_ladder_var.set("hit hot dot dog cog")
        self.p2_ladder_var.set("hit hot lot log cog")

        global _LEXICON
        _LEXICON = None
        _neighbors_cached.cache_clear()

        self.clear_outputs()
        self.set_status("Reset complete.")


def main():
    app = WordLadderGUI()
    app.mainloop()


if __name__ == "__main__":
    main()