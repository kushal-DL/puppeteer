"""Automated prompt-answer driver for the mock LLM.

Polls GET /pending, crafts an intelligent response based on the schema and
prompt context, and POSTs to /respond.  Repeats until the job completes.
"""

import json
import sys
import time
import urllib.request
import urllib.error

MOCK_URL = "http://localhost:11435"
HIVESHIP_URL = "http://localhost:80"
JOB_ID = sys.argv[1] if len(sys.argv) > 1 else None


def get(url):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def post(url, data):
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def job_status():
    if not JOB_ID:
        return None
    try:
        return get(f"{HIVESHIP_URL}/status/{JOB_ID}")
    except Exception:
        return None


# ── Response generators per schema type ───────────────────────────────────────

def make_workflow_plan(prompt: str) -> dict:
    return {
        "team_name": "chess-game-team",
        "agents": [
            {
                "agent_name": "architect",
                "role_description": "Design the chess game architecture: board representation, move validation, game loop, and bot algorithm. Produce a detailed technical spec.",
                "depends_on": [],
                "input_keys": ["initial_goal", "repo_context"],
                "read_files": [],
                "output_format": "text",
                "system_instruction": "You are a software architect specializing in game development. Design a clean, modular terminal chess game in Python with a heuristic-based bot."
            },
            {
                "agent_name": "implementer",
                "role_description": "Write the complete chess_game.py file implementing the full game: board display, move parsing, legal move generation, check/checkmate detection, and a heuristic evaluation bot. All code in one self-contained file.",
                "depends_on": ["architect"],
                "input_keys": ["architect"],
                "read_files": [],
                "output_format": "text",
                "system_instruction": "You are an expert Python developer. Implement a complete, runnable terminal chess game. The bot must use piece-square tables and material evaluation with a depth-limited minimax (max depth 3) — NOT brute force. All code in one file."
            },
            {
                "agent_name": "tester",
                "role_description": "Review the implementation for correctness, verify move validation logic, and provide run instructions.",
                "depends_on": ["implementer"],
                "input_keys": ["implementer"],
                "read_files": [],
                "output_format": "text",
                "system_instruction": "You are a QA engineer. Verify the chess implementation handles edge cases (castling, en passant, promotion, stalemate). Provide clear run instructions."
            },
            {
                "agent_name": "delivery",
                "role_description": "Compile the final chess_game.py file and README with run instructions for the PR.",
                "depends_on": ["implementer", "tester"],
                "input_keys": ["implementer", "tester"],
                "read_files": [],
                "output_format": "text",
                "system_instruction": "You are a release engineer. Assemble the final deliverable files."
            }
        ]
    }


def make_agent_text(prompt: str, system: str) -> str:
    """Generate a rich text response for an agent execution call."""
    prompt_lower = prompt.lower()

    # ── Architect agent ───────────────────────────────────────────────────
    if "architect" in prompt_lower and ("design" in prompt_lower or "spec" in prompt_lower or "technical" in prompt_lower):
        return """# Chess Game Architecture Spec

## Board Representation
- 8x8 list of lists. Each cell is None or a tuple (color, piece_type).
- Colors: 'w' (white), 'b' (black). Pieces: 'K','Q','R','B','N','P'.

## Module Structure (single file: chess_game.py)
1. **Board class**: init, display, copy, get/set piece
2. **Move generation**: per-piece legal moves, pin/check filtering
3. **Game state**: check detection, checkmate, stalemate, 50-move draw
4. **Bot (HeuristicBot)**: Material eval + piece-square tables + minimax depth 3 with alpha-beta pruning
5. **CLI Game Loop**: display board, prompt user for algebraic notation, validate, execute, bot responds

## Bot Algorithm — NOT brute force
- Evaluation function: material values (P=100, N=320, B=330, R=500, Q=900, K=20000) + piece-square table bonuses
- Search: minimax with alpha-beta pruning, max depth 3 (searches ~few thousand nodes, not millions)
- Move ordering: captures first, then checks, then quiet moves — prunes aggressively
- This is a HEURISTIC approach: limited depth + evaluation function, not exhaustive search

## Move Format
- User inputs: "e2e4" (from-square to-square)
- Promotion: "e7e8q"
- Special moves: castling via king move "e1g1", en passant automatic

## Game Flow
1. Print board (Unicode pieces)
2. White (human) enters move
3. Validate move, apply
4. Check for game end
5. Black (bot) computes move via minimax
6. Apply, check for game end
7. Repeat
"""

    # ── Implementer agent ─────────────────────────────────────────────────
    if "implement" in prompt_lower or "chess_game" in prompt_lower or "write" in prompt_lower or "code" in prompt_lower:
        return _chess_implementation()

    # ── Tester agent ──────────────────────────────────────────────────────
    if "tester" in prompt_lower or "review" in prompt_lower or "qa" in prompt_lower or "verify" in prompt_lower or "test" in prompt_lower:
        return """# QA Review of chess_game.py

## Verification Results
- [PASS] Board initializes correctly with standard starting position
- [PASS] Pawn moves: single push, double push from rank 2/7, diagonal capture
- [PASS] Knight L-shaped moves with boundary checking
- [PASS] Bishop diagonal sliding with obstruction detection
- [PASS] Rook horizontal/vertical sliding with obstruction detection
- [PASS] Queen combines rook + bishop movement
- [PASS] King single-step movement
- [PASS] Castling: king-side and queen-side, blocked by check/pieces
- [PASS] En passant capture
- [PASS] Pawn promotion to queen (default) or specified piece
- [PASS] Check detection via attack map
- [PASS] Checkmate: king in check with no legal moves
- [PASS] Stalemate: king not in check but no legal moves
- [PASS] Bot uses depth-3 minimax with alpha-beta — NOT brute force
- [PASS] Bot evaluation uses material + piece-square tables

## Run Instructions
```bash
python chess_game.py
```
Enter moves in coordinate notation: `e2e4`, `g1f3`, etc.
For pawn promotion, append piece letter: `e7e8q`
Type `quit` to exit.

## Minor Notes
- Game handles invalid input gracefully with re-prompt
- Unicode piece display works in most modern terminals
- Bot responds in under 2 seconds at depth 3
"""

    # ── Delivery agent ────────────────────────────────────────────────────
    if "delivery" in prompt_lower or "deliver" in prompt_lower or "final" in prompt_lower or "assembl" in prompt_lower or "compile" in prompt_lower:
        return """# Delivery Summary

## Files to Deliver
1. **chess_game.py** — Complete terminal chess game with heuristic bot
2. **README.md** — Updated with chess game description and run instructions

## Commit Message
feat: add terminal chess game with heuristic AI bot

## PR Title
Add terminal chess game with heuristic AI opponent

## Notes
- Single self-contained Python file, no external dependencies
- Bot uses minimax (depth 3) with alpha-beta pruning and piece-square tables
- Supports full chess rules including castling, en passant, promotion
- Run with: python chess_game.py
"""

    # ── Generic fallback ──────────────────────────────────────────────────
    return f"Acknowledged. Task completed based on provided context and requirements. The implementation follows the specifications from upstream agents."


def make_delivery_plan(prompt: str) -> dict:
    return {
        "files": [
            {
                "path": "chess_game.py",
                "content": _chess_implementation()
            },
            {
                "path": "README.md",
                "content": "# Chess Game\\n\\nA terminal-based chess game where you play as White against a heuristic AI bot.\\n\\n## How to Play\\n\\n```bash\\npython chess_game.py\\n```\\n\\nEnter moves in coordinate notation: `e2e4`, `g1f3`, etc.\\nFor pawn promotion, append the piece letter: `e7e8q`\\nType `quit` to exit.\\n\\n## Bot Algorithm\\n\\nThe bot uses a depth-limited minimax search (depth 3) with alpha-beta pruning.\\nIt evaluates positions using material values and piece-square tables.\\nThis is a heuristic approach — not brute force.\\n"
            }
        ],
        "commit_message": "feat: add terminal chess game with heuristic AI bot",
        "pr_title": "Add terminal chess game with heuristic AI opponent"
    }


def make_review_result(prompt: str) -> dict:
    return {
        "approved": True,
        "issues": []
    }


def _chess_implementation() -> str:
    return r'''#!/usr/bin/env python3
"""Terminal Chess Game with Heuristic AI Bot.

Run:  python chess_game.py
Move: type coordinate notation like e2e4, g1f3
Quit: type 'quit'
"""

import copy
import sys

# ── Piece Constants ───────────────────────────────────────────────────────────
PIECES = {'K': 'King', 'Q': 'Queen', 'R': 'Rook', 'B': 'Bishop', 'N': 'Knight', 'P': 'Pawn'}
UNICODE = {
    ('w','K'): '\u2654', ('w','Q'): '\u2655', ('w','R'): '\u2656',
    ('w','B'): '\u2657', ('w','N'): '\u2658', ('w','P'): '\u2659',
    ('b','K'): '\u265a', ('b','Q'): '\u265b', ('b','R'): '\u265c',
    ('b','B'): '\u265d', ('b','N'): '\u265e', ('b','P'): '\u265f',
}

# Material values for evaluation
MATERIAL = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}

# Piece-square tables (from White's perspective; flipped for Black)
PST = {
    'P': [
        [ 0,  0,  0,  0,  0,  0,  0,  0],
        [50, 50, 50, 50, 50, 50, 50, 50],
        [10, 10, 20, 30, 30, 20, 10, 10],
        [ 5,  5, 10, 25, 25, 10,  5,  5],
        [ 0,  0,  0, 20, 20,  0,  0,  0],
        [ 5, -5,-10,  0,  0,-10, -5,  5],
        [ 5, 10, 10,-20,-20, 10, 10,  5],
        [ 0,  0,  0,  0,  0,  0,  0,  0],
    ],
    'N': [
        [-50,-40,-30,-30,-30,-30,-40,-50],
        [-40,-20,  0,  0,  0,  0,-20,-40],
        [-30,  0, 10, 15, 15, 10,  0,-30],
        [-30,  5, 15, 20, 20, 15,  5,-30],
        [-30,  0, 15, 20, 20, 15,  0,-30],
        [-30,  5, 10, 15, 15, 10,  5,-30],
        [-40,-20,  0,  5,  5,  0,-20,-40],
        [-50,-40,-30,-30,-30,-30,-40,-50],
    ],
    'B': [
        [-20,-10,-10,-10,-10,-10,-10,-20],
        [-10,  0,  0,  0,  0,  0,  0,-10],
        [-10,  0, 10, 10, 10, 10,  0,-10],
        [-10,  5,  5, 10, 10,  5,  5,-10],
        [-10,  0,  5, 10, 10,  5,  0,-10],
        [-10, 10,  5, 10, 10,  5, 10,-10],
        [-10,  5,  0,  0,  0,  0,  5,-10],
        [-20,-10,-10,-10,-10,-10,-10,-20],
    ],
    'R': [
        [ 0,  0,  0,  0,  0,  0,  0,  0],
        [ 5, 10, 10, 10, 10, 10, 10,  5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [ 0,  0,  0,  5,  5,  0,  0,  0],
    ],
    'Q': [
        [-20,-10,-10, -5, -5,-10,-10,-20],
        [-10,  0,  0,  0,  0,  0,  0,-10],
        [-10,  0,  5,  5,  5,  5,  0,-10],
        [ -5,  0,  5,  5,  5,  5,  0, -5],
        [  0,  0,  5,  5,  5,  5,  0, -5],
        [-10,  5,  5,  5,  5,  5,  0,-10],
        [-10,  0,  5,  0,  0,  0,  0,-10],
        [-20,-10,-10, -5, -5,-10,-10,-20],
    ],
    'K': [
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-20,-30,-30,-40,-40,-30,-30,-20],
        [-10,-20,-20,-20,-20,-20,-20,-10],
        [ 20, 20,  0,  0,  0,  0, 20, 20],
        [ 20, 30, 10,  0,  0, 10, 30, 20],
    ],
}


class Board:
    """8x8 chess board with full move generation and validation."""

    def __init__(self):
        self.grid = [[None]*8 for _ in range(8)]
        self.turn = 'w'
        self.castling = {'w': {'K': True, 'Q': True}, 'b': {'K': True, 'Q': True}}
        self.en_passant = None  # (row, col) of en-passant target square
        self.halfmove = 0
        self.fullmove = 1
        self._setup()

    def _setup(self):
        order = ['R','N','B','Q','K','B','N','R']
        for c in range(8):
            self.grid[0][c] = ('b', order[c])
            self.grid[1][c] = ('b', 'P')
            self.grid[6][c] = ('w', 'P')
            self.grid[7][c] = ('w', order[c])

    def copy(self):
        b = Board.__new__(Board)
        b.grid = [row[:] for row in self.grid]
        b.turn = self.turn
        b.castling = {c: dict(s) for c, s in self.castling.items()}
        b.en_passant = self.en_passant
        b.halfmove = self.halfmove
        b.fullmove = self.fullmove
        return b

    def get(self, r, c):
        if 0 <= r < 8 and 0 <= c < 8:
            return self.grid[r][c]
        return None

    def display(self):
        print("\n    a   b   c   d   e   f   g   h")
        print("  +---+---+---+---+---+---+---+---+")
        for r in range(8):
            rank = str(8 - r)
            row_str = rank + " |"
            for c in range(8):
                p = self.grid[r][c]
                if p:
                    sym = UNICODE.get(p, '?')
                    row_str += f" {sym} |"
                else:
                    row_str += "   |"
            print(row_str + " " + rank)
            print("  +---+---+---+---+---+---+---+---+")
        print("    a   b   c   d   e   f   g   h\n")

    def is_enemy(self, r, c, color):
        p = self.get(r, c)
        return p is not None and p[0] != color

    def is_empty(self, r, c):
        return 0 <= r < 8 and 0 <= c < 8 and self.grid[r][c] is None

    def find_king(self, color):
        for r in range(8):
            for c in range(8):
                p = self.grid[r][c]
                if p and p == (color, 'K'):
                    return (r, c)
        return None

    def is_attacked(self, r, c, by_color):
        """Check if square (r,c) is attacked by 'by_color'."""
        # Pawn attacks
        d = -1 if by_color == 'w' else 1
        for dc in [-1, 1]:
            nr, nc = r + d, c + dc
            p = self.get(nr, nc)
            if p and p == (by_color, 'P'):
                return True
        # Knight attacks
        for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            p = self.get(r+dr, c+dc)
            if p and p == (by_color, 'N'):
                return True
        # King attacks
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                p = self.get(r+dr, c+dc)
                if p and p == (by_color, 'K'):
                    return True
        # Sliding pieces (Rook/Queen for straights, Bishop/Queen for diags)
        for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
            nr, nc = r+dr, c+dc
            while 0 <= nr < 8 and 0 <= nc < 8:
                p = self.grid[nr][nc]
                if p:
                    if p[0] == by_color and p[1] in ('R', 'Q'):
                        return True
                    break
                nr += dr
                nc += dc
        for dr, dc in [(1,1),(1,-1),(-1,1),(-1,-1)]:
            nr, nc = r+dr, c+dc
            while 0 <= nr < 8 and 0 <= nc < 8:
                p = self.grid[nr][nc]
                if p:
                    if p[0] == by_color and p[1] in ('B', 'Q'):
                        return True
                    break
                nr += dr
                nc += dc
        return False

    def in_check(self, color):
        kpos = self.find_king(color)
        if not kpos:
            return False
        enemy = 'b' if color == 'w' else 'w'
        return self.is_attacked(kpos[0], kpos[1], enemy)

    def pseudo_moves(self, color):
        """Generate all pseudo-legal moves (may leave king in check)."""
        moves = []
        for r in range(8):
            for c in range(8):
                p = self.grid[r][c]
                if not p or p[0] != color:
                    continue
                piece = p[1]
                if piece == 'P':
                    moves.extend(self._pawn_moves(r, c, color))
                elif piece == 'N':
                    moves.extend(self._knight_moves(r, c, color))
                elif piece == 'B':
                    moves.extend(self._slide_moves(r, c, color, [(1,1),(1,-1),(-1,1),(-1,-1)]))
                elif piece == 'R':
                    moves.extend(self._slide_moves(r, c, color, [(0,1),(0,-1),(1,0),(-1,0)]))
                elif piece == 'Q':
                    moves.extend(self._slide_moves(r, c, color, [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]))
                elif piece == 'K':
                    moves.extend(self._king_moves(r, c, color))
        return moves

    def legal_moves(self, color=None):
        """Generate all legal moves for color (default: current turn)."""
        color = color or self.turn
        legal = []
        for move in self.pseudo_moves(color):
            b2 = self.copy()
            b2._apply_raw(move)
            if not b2.in_check(color):
                legal.append(move)
        return legal

    def _pawn_moves(self, r, c, color):
        moves = []
        d = -1 if color == 'w' else 1
        start_rank = 6 if color == 'w' else 1
        promo_rank = 0 if color == 'w' else 7
        # Forward
        if self.is_empty(r+d, c):
            if r+d == promo_rank:
                for pp in ['Q','R','B','N']:
                    moves.append((r, c, r+d, c, pp))
            else:
                moves.append((r, c, r+d, c, None))
                if r == start_rank and self.is_empty(r+2*d, c):
                    moves.append((r, c, r+2*d, c, None))
        # Captures
        for dc in [-1, 1]:
            nc = c + dc
            if 0 <= nc < 8:
                if self.is_enemy(r+d, nc, color):
                    if r+d == promo_rank:
                        for pp in ['Q','R','B','N']:
                            moves.append((r, c, r+d, nc, pp))
                    else:
                        moves.append((r, c, r+d, nc, None))
                elif self.en_passant and (r+d, nc) == self.en_passant:
                    moves.append((r, c, r+d, nc, 'ep'))
        return moves

    def _knight_moves(self, r, c, color):
        moves = []
        for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                p = self.grid[nr][nc]
                if not p or p[0] != color:
                    moves.append((r, c, nr, nc, None))
        return moves

    def _slide_moves(self, r, c, color, directions):
        moves = []
        for dr, dc in directions:
            nr, nc = r+dr, c+dc
            while 0 <= nr < 8 and 0 <= nc < 8:
                p = self.grid[nr][nc]
                if p:
                    if p[0] != color:
                        moves.append((r, c, nr, nc, None))
                    break
                moves.append((r, c, nr, nc, None))
                nr += dr
                nc += dc
        return moves

    def _king_moves(self, r, c, color):
        moves = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r+dr, c+dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    p = self.grid[nr][nc]
                    if not p or p[0] != color:
                        moves.append((r, c, nr, nc, None))
        # Castling
        enemy = 'b' if color == 'w' else 'w'
        if not self.in_check(color):
            # King-side
            if self.castling[color]['K']:
                if self.is_empty(r, c+1) and self.is_empty(r, c+2):
                    if not self.is_attacked(r, c+1, enemy) and not self.is_attacked(r, c+2, enemy):
                        moves.append((r, c, r, c+2, 'ck'))
            # Queen-side
            if self.castling[color]['Q']:
                if self.is_empty(r, c-1) and self.is_empty(r, c-2) and self.is_empty(r, c-3):
                    if not self.is_attacked(r, c-1, enemy) and not self.is_attacked(r, c-2, enemy):
                        moves.append((r, c, r, c-2, 'cq'))
        return moves

    def _apply_raw(self, move):
        """Apply move without legality check. Updates castling/en-passant state."""
        r1, c1, r2, c2, special = move
        piece = self.grid[r1][c1]
        if not piece:
            return
        color, ptype = piece

        # En passant capture
        if special == 'ep':
            self.grid[r1][c2] = None  # remove captured pawn
            self.grid[r2][c2] = piece
            self.grid[r1][c1] = None
            self.en_passant = None
            self.halfmove = 0
            return

        # Castling
        if special == 'ck':
            self.grid[r2][c2] = piece
            self.grid[r1][c1] = None
            self.grid[r1][c1+3], self.grid[r1][c1+1] = None, self.grid[r1][c1+3]
            self.castling[color] = {'K': False, 'Q': False}
            self.en_passant = None
            self.halfmove += 1
            return

        if special == 'cq':
            self.grid[r2][c2] = piece
            self.grid[r1][c1] = None
            self.grid[r1][c1-4], self.grid[r1][c1-1] = None, self.grid[r1][c1-4]
            self.castling[color] = {'K': False, 'Q': False}
            self.en_passant = None
            self.halfmove += 1
            return

        captured = self.grid[r2][c2]

        # Promotion
        if special in ('Q','R','B','N'):
            self.grid[r2][c2] = (color, special)
        else:
            self.grid[r2][c2] = piece
        self.grid[r1][c1] = None

        # Update en passant
        if ptype == 'P' and abs(r2 - r1) == 2:
            self.en_passant = ((r1 + r2) // 2, c1)
        else:
            self.en_passant = None

        # Update castling rights
        if ptype == 'K':
            self.castling[color] = {'K': False, 'Q': False}
        if ptype == 'R':
            if c1 == 0:
                self.castling[color]['Q'] = False
            elif c1 == 7:
                self.castling[color]['K'] = False

        # Halfmove clock
        if ptype == 'P' or captured:
            self.halfmove = 0
        else:
            self.halfmove += 1

    def make_move(self, move):
        """Apply a legal move and switch turn."""
        self._apply_raw(move)
        if self.turn == 'b':
            self.fullmove += 1
        self.turn = 'b' if self.turn == 'w' else 'w'

    def is_checkmate(self, color=None):
        color = color or self.turn
        return self.in_check(color) and len(self.legal_moves(color)) == 0

    def is_stalemate(self, color=None):
        color = color or self.turn
        return not self.in_check(color) and len(self.legal_moves(color)) == 0

    def is_draw(self):
        return self.halfmove >= 100 or self.is_stalemate()


# ── Heuristic Bot (minimax + alpha-beta, depth 3) ────────────────────────────

class HeuristicBot:
    """Chess bot using piece-square tables + material evaluation + minimax.

    Depth is limited to 3 plies with alpha-beta pruning.
    This is a HEURISTIC approach, NOT brute force.
    """

    def __init__(self, color='b', max_depth=3):
        self.color = color
        self.max_depth = max_depth

    def evaluate(self, board):
        """Evaluate board from White's perspective."""
        score = 0
        for r in range(8):
            for c in range(8):
                p = board.grid[r][c]
                if not p:
                    continue
                color, ptype = p
                val = MATERIAL[ptype]
                # Piece-square table bonus
                if ptype in PST:
                    if color == 'w':
                        val += PST[ptype][r][c]
                    else:
                        val += PST[ptype][7-r][c]
                if color == 'w':
                    score += val
                else:
                    score -= val
        return score

    def _order_moves(self, board, moves):
        """Simple move ordering: captures first for better pruning."""
        captures = []
        quiet = []
        for m in moves:
            if board.grid[m[2]][m[3]] is not None:
                captures.append(m)
            else:
                quiet.append(m)
        return captures + quiet

    def minimax(self, board, depth, alpha, beta, maximizing):
        if depth == 0 or board.is_checkmate() or board.is_stalemate():
            return self.evaluate(board), None

        moves = board.legal_moves()
        if not moves:
            if board.in_check(board.turn):
                return (-99999 if maximizing else 99999), None
            return 0, None

        moves = self._order_moves(board, moves)
        best_move = moves[0]

        if maximizing:
            max_eval = -999999
            for move in moves:
                b2 = board.copy()
                b2.make_move(move)
                val, _ = self.minimax(b2, depth - 1, alpha, beta, False)
                if val > max_eval:
                    max_eval = val
                    best_move = move
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = 999999
            for move in moves:
                b2 = board.copy()
                b2.make_move(move)
                val, _ = self.minimax(b2, depth - 1, alpha, beta, True)
                if val < min_eval:
                    min_eval = val
                    best_move = move
                beta = min(beta, val)
                if beta <= alpha:
                    break
            return min_eval, best_move

    def choose_move(self, board):
        maximizing = (self.color == 'w')
        _, move = self.minimax(board, self.max_depth, -999999, 999999, maximizing)
        return move


# ── CLI Helpers ───────────────────────────────────────────────────────────────

def parse_move(text):
    """Parse 'e2e4' or 'e7e8q' into (r1,c1,r2,c2,promo)."""
    text = text.strip().lower()
    if len(text) < 4:
        return None
    cols = 'abcdefgh'
    if text[0] not in cols or text[2] not in cols:
        return None
    try:
        c1 = cols.index(text[0])
        r1 = 8 - int(text[1])
        c2 = cols.index(text[2])
        r2 = 8 - int(text[3])
    except (ValueError, IndexError):
        return None
    promo = None
    if len(text) == 5:
        promo = text[4].upper()
        if promo not in ('Q','R','B','N'):
            return None
    return (r1, c1, r2, c2, promo)


def find_matching_move(parsed, legal):
    """Find the legal move matching parsed input."""
    r1, c1, r2, c2, promo = parsed
    for m in legal:
        if m[0] == r1 and m[1] == c1 and m[2] == r2 and m[3] == c2:
            if promo:
                if m[4] == promo:
                    return m
            else:
                if m[4] in (None, 'ep', 'ck', 'cq'):
                    return m
                if m[4] == 'Q':  # default promotion to queen
                    return m
        return None if False else None  # continue checking
    # Second pass: exact match
    for m in legal:
        if m[0] == r1 and m[1] == c1 and m[2] == r2 and m[3] == c2:
            if promo and m[4] == promo:
                return m
            if not promo and m[4] in (None, 'ep', 'ck', 'cq', 'Q'):
                return m
    return None


def move_to_str(move):
    cols = 'abcdefgh'
    r1, c1, r2, c2, sp = move
    s = f"{cols[c1]}{8-r1}{cols[c2]}{8-r2}"
    if sp in ('Q','R','B','N'):
        s += sp.lower()
    return s


# ── Main Game Loop ────────────────────────────────────────────────────────────

def main():
    board = Board()
    bot = HeuristicBot(color='b', max_depth=3)

    print("=" * 50)
    print("  TERMINAL CHESS")
    print("  You are White. Bot is Black.")
    print("  Enter moves: e2e4, g1f3, e7e8q (promotion)")
    print("  Type 'quit' to exit.")
    print("=" * 50)

    while True:
        board.display()

        if board.is_checkmate(board.turn):
            winner = "Black" if board.turn == 'w' else "White"
            print(f"Checkmate! {winner} wins!")
            break
        if board.is_draw():
            print("Draw!")
            break

        if board.turn == 'w':
            # Human turn
            if board.in_check('w'):
                print("  ** You are in check! **")
            while True:
                try:
                    inp = input("Your move: ").strip()
                except EOFError:
                    print("\nGoodbye!")
                    sys.exit(0)
                if inp.lower() == 'quit':
                    print("Goodbye!")
                    sys.exit(0)
                parsed = parse_move(inp)
                if not parsed:
                    print("Invalid format. Use e2e4 notation.")
                    continue
                legal = board.legal_moves('w')
                move = find_matching_move(parsed, legal)
                if not move:
                    print("Illegal move. Try again.")
                    continue
                board.make_move(move)
                print(f"  You played: {move_to_str(move)}")
                break
        else:
            # Bot turn
            print("  Bot is thinking...")
            move = bot.choose_move(board)
            if not move:
                if board.in_check('b'):
                    print("Checkmate! You win!")
                else:
                    print("Stalemate! Draw!")
                break
            board.make_move(move)
            print(f"  Bot played: {move_to_str(move)}")


if __name__ == "__main__":
    main()
'''


# ── Main loop ─────────────────────────────────────────────────────────────────

def respond(call_id, schema, prompt, system):
    """Craft response based on schema type and prompt content."""
    if schema == "WorkflowPlan":
        data = make_workflow_plan(prompt)
        return json.dumps(data, ensure_ascii=False)
    elif schema == "DeliveryPlan":
        data = make_delivery_plan(prompt)
        return json.dumps(data, ensure_ascii=False)
    elif schema == "ReviewResult":
        data = make_review_result(prompt)
        return json.dumps(data, ensure_ascii=False)
    else:
        # Free-text agent call
        return make_agent_text(prompt, system)


def main():
    print(f"[driver] Polling {MOCK_URL}/pending ...")
    print(f"[driver] Job: {JOB_ID or 'unknown'}")

    consecutive_empty = 0
    max_empty = 120  # ~2 min of empty polls

    while True:
        # Check job status
        status = job_status()
        if status:
            s = status.get("status", "")
            if s in ("completed", "failed"):
                print(f"\n[driver] Job {JOB_ID} → {s}")
                if status.get("error"):
                    print(f"[driver] Error: {status['error']}")
                if status.get("result"):
                    print(f"[driver] Result preview: {json.dumps(status['result'], ensure_ascii=False)[:500]}")
                break

        # Poll pending
        try:
            pending = get(f"{MOCK_URL}/pending")
        except Exception as e:
            print(f"[driver] Poll error: {e}")
            time.sleep(2)
            continue

        if not pending.get("pending"):
            consecutive_empty += 1
            if consecutive_empty >= max_empty:
                print("[driver] No prompts for 2 min — assuming done or stalled.")
                break
            time.sleep(1)
            continue

        consecutive_empty = 0
        call_id = pending["call_id"]
        schema = pending.get("schema") or "text"
        prompt = pending.get("prompt", "")
        system = pending.get("system", "")

        print(f"\n{'='*60}")
        print(f"[driver] Call #{call_id} | schema: {schema}")
        print(f"[driver] Prompt: {prompt[:200]}...")
        print(f"{'='*60}")

        answer = respond(call_id, schema, prompt, system)
        print(f"[driver] Responding ({len(answer)} chars)...")

        try:
            result = post(f"{MOCK_URL}/respond", {"response": answer})
            print(f"[driver] → {result}")
        except Exception as e:
            print(f"[driver] Respond error: {e}")

        time.sleep(0.5)

    # Final status
    status = job_status()
    if status:
        print(f"\n{'='*60}")
        print(f"[driver] FINAL STATUS: {json.dumps(status, ensure_ascii=False, indent=2)[:2000]}")
        print(f"{'='*60}")


if __name__ == "__main__":
    main()
