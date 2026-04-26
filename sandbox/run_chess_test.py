"""
End-to-end test of the monolithic auto-sdlc pipeline (legacy/app_old.py).

Copilot acts as the LLM — pre-scripted responses for every agent call.
Git operations and GitHub API calls are mocked; output saved to disk.

Prompt: "create a chess game for me in a python file which i can run in a
terminal. i want to be able to play against a bot but you cant program
the bot to brute force its way to a checkmate. You can program the bot
with some sort of algorithm if you like or in any other way but no brute force."
"""

import os, sys, json, pathlib, types, shutil, time, threading

# ── 1. Set dummy env vars BEFORE importing app_old.py ────────────────────────
os.environ.setdefault("GITHUB_TOKEN", "ghp_dummy_token_for_test")
os.environ.setdefault("WEBHOOK_SECRET", "dummy_secret")
os.environ.setdefault("GEMINI_API_KEY", "dummy_key_not_used")
os.environ.setdefault("DEFAULT_LLM_PROVIDER", "gemini")

# ── 2. Import the monolithic app ─────────────────────────────────────────────
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "legacy"))
import app_old  # noqa: E402

# ── 3. Pre-scripted LLM responses ────────────────────────────────────────────
# Each entry: (description, response_text)

USER_GOAL = (
    "create a chess game for me in a python file which i can run in a terminal. "
    "i want to be able to play against a bot but you cant program the bot to brute "
    "force its way to a checkmate. You can program the bot with some sort of "
    "algorithm if you like or in any other way but no brute force."
)

# ── WorkflowPlan (planning phase) ────────────────────────────────────────────
PLAN_RESPONSE = json.dumps({
    "team_name": "chess-game-team",
    "agents": [
        {
            "agent_name": "game_architect",
            "role_description": (
                "Design the chess game architecture: board representation (8x8 array), "
                "piece encoding, move validation rules for all 6 piece types, "
                "check/checkmate detection algorithm, and the bot strategy. "
                "The bot must NOT use brute force — design it with piece-square tables "
                "for positional evaluation combined with minimax search at a fixed, "
                "shallow depth (3 plies). Output a detailed design document."
            ),
            "depends_on": [],
            "input_keys": ["initial_goal", "repo_context"],
            "read_files": [],
            "output_format": "text"
        },
        {
            "agent_name": "chess_implementer",
            "role_description": (
                "Implement the complete chess game in a single Python file chess.py. "
                "Include: Board class, full move validation for all pieces, "
                "check/checkmate/stalemate detection, castling, en passant, pawn promotion, "
                "the bot AI using minimax + alpha-beta pruning with piece-square tables "
                "(NOT brute force), and a terminal game loop with Unicode display."
            ),
            "depends_on": ["game_architect"],
            "input_keys": ["game_architect"],
            "read_files": [],
            "output_format": "text"
        },
        {
            "agent_name": "tester",
            "role_description": (
                "Review the chess implementation for correctness: verify the move validation "
                "logic, check detection, bot behavior, and game loop flow. "
                "Report any issues found."
            ),
            "depends_on": ["chess_implementer"],
            "input_keys": ["chess_implementer"],
            "read_files": [],
            "output_format": "text"
        }
    ]
})

# ── Agent artifacts (DAG execution phase) ────────────────────────────────────
ARCHITECT_ARTIFACT = """\
# Chess Game Architecture Design

## Board Representation
- 8x8 list-of-lists, each cell is a string: "wp" = white pawn, "bK" = black king, ".." = empty
- Piece chars: K(king), Q(queen), R(rook), B(bishop), N(knight), P(pawn)
- Color prefix: 'w' or 'b'

## Move Validation
- Each piece type has a move generator returning list of (row,col) destinations
- Pawn: forward 1 (or 2 from start), diagonal capture, en passant
- Knight: L-shape jumps, can jump over pieces
- Bishop: diagonal sliding
- Rook: horizontal/vertical sliding
- Queen: bishop + rook combined
- King: one square any direction + castling

## Check / Checkmate / Stalemate
- is_in_check(color): check if any opponent piece attacks the king
- is_checkmate(color): in check AND no legal moves
- is_stalemate(color): NOT in check AND no legal moves
- A move is legal only if it doesn't leave own king in check

## Bot Strategy (NO BRUTE FORCE)
- Evaluation function: material value + piece-square table bonuses
- Material: P=100, N=320, B=330, R=500, Q=900, K=20000
- Piece-square tables: 8x8 bonus arrays for each piece type (encourage center control, king safety)
- Search: minimax with alpha-beta pruning, FIXED depth = 3
- This is NOT brute force because:
  1. Depth is fixed and shallow (only 3 moves ahead)
  2. Alpha-beta prunes vast majority of branches
  3. Evaluation uses heuristic position scoring, not exhaustive endgame search

## Terminal UI
- Unicode chess pieces: ♔♕♖♗♘♙♚♛♜♝♞♟
- Algebraic notation input: e.g. "e2e4" or "e2 e4"
- Board displayed with rank/file labels
- Color-coded squares (if terminal supports it, else simple text)

## Game Loop
1. Display board
2. If human's turn: prompt for move, validate, apply
3. If bot's turn: run minimax, apply best move, display
4. Check for check/checkmate/stalemate after each move
5. Handle resignation (player types 'quit')
"""

# The full chess game implementation
CHESS_PY_CONTENT = r'''#!/usr/bin/env python3
"""
Terminal Chess Game — play against a bot that uses minimax + piece-square tables.
Run: python chess.py

The bot does NOT brute-force. It uses:
  - Material evaluation (standard piece values)
  - Piece-square tables (positional bonuses)
  - Minimax with alpha-beta pruning at fixed depth 3
"""

import copy
import sys

# ═══════════════════════════════════════════════════════════════════════════════
# Piece encoding:  "wp" = white pawn, "bQ" = black queen, ".." = empty
# ═══════════════════════════════════════════════════════════════════════════════

EMPTY = ".."

UNICODE_PIECES = {
    "wK": "\u2654", "wQ": "\u2655", "wR": "\u2656", "wB": "\u2657", "wN": "\u2658", "wP": "\u2659",
    "bK": "\u265a", "bQ": "\u265b", "bR": "\u265c", "bB": "\u265d", "bN": "\u265e", "bP": "\u265f",
}

PIECE_VALUES = {"P": 100, "N": 320, "B": 330, "R": 500, "Q": 900, "K": 20000}

# ═══════════════════════════════════════════════════════════════════════════════
# Piece-Square Tables (from white's perspective; mirrored for black)
# Higher values = better squares for that piece
# ═══════════════════════════════════════════════════════════════════════════════

PST_PAWN = [
    [  0,  0,  0,  0,  0,  0,  0,  0],
    [ 50, 50, 50, 50, 50, 50, 50, 50],
    [ 10, 10, 20, 30, 30, 20, 10, 10],
    [  5,  5, 10, 25, 25, 10,  5,  5],
    [  0,  0,  0, 20, 20,  0,  0,  0],
    [  5, -5,-10,  0,  0,-10, -5,  5],
    [  5, 10, 10,-20,-20, 10, 10,  5],
    [  0,  0,  0,  0,  0,  0,  0,  0],
]

PST_KNIGHT = [
    [-50,-40,-30,-30,-30,-30,-40,-50],
    [-40,-20,  0,  0,  0,  0,-20,-40],
    [-30,  0, 10, 15, 15, 10,  0,-30],
    [-30,  5, 15, 20, 20, 15,  5,-30],
    [-30,  0, 15, 20, 20, 15,  0,-30],
    [-30,  5, 10, 15, 15, 10,  5,-30],
    [-40,-20,  0,  5,  5,  0,-20,-40],
    [-50,-40,-30,-30,-30,-30,-40,-50],
]

PST_BISHOP = [
    [-20,-10,-10,-10,-10,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0, 10, 10, 10, 10,  0,-10],
    [-10,  5,  5, 10, 10,  5,  5,-10],
    [-10,  0,  5, 10, 10,  5,  0,-10],
    [-10, 10, 10, 10, 10, 10, 10,-10],
    [-10,  5,  0,  0,  0,  0,  5,-10],
    [-20,-10,-10,-10,-10,-10,-10,-20],
]

PST_ROOK = [
    [  0,  0,  0,  0,  0,  0,  0,  0],
    [  5, 10, 10, 10, 10, 10, 10,  5],
    [ -5,  0,  0,  0,  0,  0,  0, -5],
    [ -5,  0,  0,  0,  0,  0,  0, -5],
    [ -5,  0,  0,  0,  0,  0,  0, -5],
    [ -5,  0,  0,  0,  0,  0,  0, -5],
    [ -5,  0,  0,  0,  0,  0,  0, -5],
    [  0,  0,  0,  5,  5,  0,  0,  0],
]

PST_QUEEN = [
    [-20,-10,-10, -5, -5,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5,  5,  5,  5,  0,-10],
    [ -5,  0,  5,  5,  5,  5,  0, -5],
    [  0,  0,  5,  5,  5,  5,  0, -5],
    [-10,  5,  5,  5,  5,  5,  0,-10],
    [-10,  0,  5,  0,  0,  0,  0,-10],
    [-20,-10,-10, -5, -5,-10,-10,-20],
]

PST_KING_MIDDLE = [
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-20,-30,-30,-40,-40,-30,-30,-20],
    [-10,-20,-20,-20,-20,-20,-20,-10],
    [ 20, 20,  0,  0,  0,  0, 20, 20],
    [ 20, 30, 10,  0,  0, 10, 30, 20],
]

PST = {"P": PST_PAWN, "N": PST_KNIGHT, "B": PST_BISHOP, "R": PST_ROOK, "Q": PST_QUEEN, "K": PST_KING_MIDDLE}


def pst_value(piece_type, color, row, col):
    """Get piece-square table bonus for a piece at (row, col)."""
    table = PST.get(piece_type)
    if table is None:
        return 0
    if color == "w":
        return table[row][col]
    else:
        return table[7 - row][col]


# ═══════════════════════════════════════════════════════════════════════════════
# Board Class
# ═══════════════════════════════════════════════════════════════════════════════

class Board:
    def __init__(self):
        self.grid = [[EMPTY] * 8 for _ in range(8)]
        self.turn = "w"  # 'w' or 'b'
        self.castling_rights = {"wK": True, "wQ": True, "bK": True, "bQ": True}
        self.en_passant_target = None  # (row, col) or None
        self.move_history = []
        self._setup_initial_position()

    def _setup_initial_position(self):
        # Black pieces (top)
        back_rank = ["R", "N", "B", "Q", "K", "B", "N", "R"]
        for c in range(8):
            self.grid[0][c] = "b" + back_rank[c]
            self.grid[1][c] = "bP"
            self.grid[6][c] = "wP"
            self.grid[7][c] = "w" + back_rank[c]

    def at(self, r, c):
        if 0 <= r < 8 and 0 <= c < 8:
            return self.grid[r][c]
        return None

    def color_at(self, r, c):
        p = self.at(r, c)
        if p and p != EMPTY:
            return p[0]
        return None

    def piece_type_at(self, r, c):
        p = self.at(r, c)
        if p and p != EMPTY:
            return p[1]
        return None

    def copy(self):
        b = Board.__new__(Board)
        b.grid = [row[:] for row in self.grid]
        b.turn = self.turn
        b.castling_rights = dict(self.castling_rights)
        b.en_passant_target = self.en_passant_target
        b.move_history = list(self.move_history)
        return b

    # ── Display ───────────────────────────────────────────────────────────
    def display(self):
        print()
        print("    a   b   c   d   e   f   g   h")
        print("  +---+---+---+---+---+---+---+---+")
        for r in range(8):
            rank_num = 8 - r
            row_str = f"{rank_num} |"
            for c in range(8):
                piece = self.grid[r][c]
                if piece == EMPTY:
                    cell = " . "
                else:
                    symbol = UNICODE_PIECES.get(piece, piece)
                    cell = f" {symbol} "
                row_str += cell + "|"
            print(row_str + f" {rank_num}")
            print("  +---+---+---+---+---+---+---+---+")
        print("    a   b   c   d   e   f   g   h")
        print()

    # ── Move Generation ───────────────────────────────────────────────────
    def _pseudo_legal_moves(self, color):
        """Generate all pseudo-legal moves (may leave king in check)."""
        moves = []
        for r in range(8):
            for c in range(8):
                if self.color_at(r, c) == color:
                    pt = self.piece_type_at(r, c)
                    if pt == "P":
                        moves.extend(self._pawn_moves(r, c, color))
                    elif pt == "N":
                        moves.extend(self._knight_moves(r, c, color))
                    elif pt == "B":
                        moves.extend(self._sliding_moves(r, c, color, [(-1,-1),(-1,1),(1,-1),(1,1)]))
                    elif pt == "R":
                        moves.extend(self._sliding_moves(r, c, color, [(-1,0),(1,0),(0,-1),(0,1)]))
                    elif pt == "Q":
                        moves.extend(self._sliding_moves(r, c, color, [(-1,-1),(-1,1),(1,-1),(1,1),(-1,0),(1,0),(0,-1),(0,1)]))
                    elif pt == "K":
                        moves.extend(self._king_moves(r, c, color))
        return moves

    def _pawn_moves(self, r, c, color):
        moves = []
        direction = -1 if color == "w" else 1
        start_row = 6 if color == "w" else 1
        promo_row = 0 if color == "w" else 7

        # Forward one
        nr = r + direction
        if 0 <= nr < 8 and self.grid[nr][c] == EMPTY:
            if nr == promo_row:
                for promo in ["Q", "R", "B", "N"]:
                    moves.append((r, c, nr, c, promo))
            else:
                moves.append((r, c, nr, c, None))
            # Forward two from start
            if r == start_row:
                nr2 = r + 2 * direction
                if self.grid[nr2][c] == EMPTY:
                    moves.append((r, c, nr2, c, None))

        # Captures (diagonal)
        for dc in [-1, 1]:
            nc = c + dc
            nr = r + direction
            if 0 <= nr < 8 and 0 <= nc < 8:
                target = self.color_at(nr, nc)
                if target and target != color:
                    if nr == promo_row:
                        for promo in ["Q", "R", "B", "N"]:
                            moves.append((r, c, nr, nc, promo))
                    else:
                        moves.append((r, c, nr, nc, None))

        # En passant
        if self.en_passant_target:
            ep_r, ep_c = self.en_passant_target
            if r + direction == ep_r and abs(c - ep_c) == 1:
                moves.append((r, c, ep_r, ep_c, None))

        return moves

    def _knight_moves(self, r, c, color):
        moves = []
        for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                if self.color_at(nr, nc) != color:
                    moves.append((r, c, nr, nc, None))
        return moves

    def _sliding_moves(self, r, c, color, directions):
        moves = []
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 8 and 0 <= nc < 8:
                target_color = self.color_at(nr, nc)
                if target_color == color:
                    break
                moves.append((r, c, nr, nc, None))
                if target_color is not None:
                    break  # captured opponent piece, can't go further
                nr += dr
                nc += dc
        return moves

    def _king_moves(self, r, c, color):
        moves = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8 and self.color_at(nr, nc) != color:
                    moves.append((r, c, nr, nc, None))

        # Castling
        if color == "w" and r == 7 and c == 4:
            if self.castling_rights["wK"] and self.grid[7][5] == EMPTY and self.grid[7][6] == EMPTY and self.grid[7][7] == "wR":
                if not self._is_square_attacked(7, 4, "b") and not self._is_square_attacked(7, 5, "b") and not self._is_square_attacked(7, 6, "b"):
                    moves.append((7, 4, 7, 6, None))
            if self.castling_rights["wQ"] and self.grid[7][3] == EMPTY and self.grid[7][2] == EMPTY and self.grid[7][1] == EMPTY and self.grid[7][0] == "wR":
                if not self._is_square_attacked(7, 4, "b") and not self._is_square_attacked(7, 3, "b") and not self._is_square_attacked(7, 2, "b"):
                    moves.append((7, 4, 7, 2, None))
        elif color == "b" and r == 0 and c == 4:
            if self.castling_rights["bK"] and self.grid[0][5] == EMPTY and self.grid[0][6] == EMPTY and self.grid[0][7] == "bR":
                if not self._is_square_attacked(0, 4, "w") and not self._is_square_attacked(0, 5, "w") and not self._is_square_attacked(0, 6, "w"):
                    moves.append((0, 4, 0, 6, None))
            if self.castling_rights["bQ"] and self.grid[0][3] == EMPTY and self.grid[0][2] == EMPTY and self.grid[0][1] == EMPTY and self.grid[0][0] == "bR":
                if not self._is_square_attacked(0, 4, "w") and not self._is_square_attacked(0, 3, "w") and not self._is_square_attacked(0, 2, "w"):
                    moves.append((0, 4, 0, 2, None))
        return moves

    def _is_square_attacked(self, r, c, by_color):
        """Check if square (r,c) is attacked by any piece of by_color."""
        # Knight attacks
        for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and self.grid[nr][nc] == by_color + "N":
                return True
        # Pawn attacks
        pawn_dir = 1 if by_color == "w" else -1
        for dc in [-1, 1]:
            nr, nc = r + pawn_dir, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and self.grid[nr][nc] == by_color + "P":
                return True
        # King attacks
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8 and self.grid[nr][nc] == by_color + "K":
                    return True
        # Sliding attacks (bishop/queen diagonals, rook/queen straights)
        for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 8 and 0 <= nc < 8:
                p = self.grid[nr][nc]
                if p != EMPTY:
                    if p == by_color + "B" or p == by_color + "Q":
                        return True
                    break
                nr += dr; nc += dc
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 8 and 0 <= nc < 8:
                p = self.grid[nr][nc]
                if p != EMPTY:
                    if p == by_color + "R" or p == by_color + "Q":
                        return True
                    break
                nr += dr; nc += dc
        return False

    # ── Legal Move Filtering ──────────────────────────────────────────────
    def legal_moves(self, color=None):
        """Return only moves that don't leave own king in check."""
        color = color or self.turn
        legal = []
        for move in self._pseudo_legal_moves(color):
            test = self.copy()
            test._apply_move_unchecked(move)
            if not test.is_in_check(color):
                legal.append(move)
        return legal

    def is_in_check(self, color):
        """Is the given color's king currently in check?"""
        king = color + "K"
        for r in range(8):
            for c in range(8):
                if self.grid[r][c] == king:
                    opp = "b" if color == "w" else "w"
                    return self._is_square_attacked(r, c, opp)
        return False

    def is_checkmate(self, color):
        return self.is_in_check(color) and len(self.legal_moves(color)) == 0

    def is_stalemate(self, color):
        return not self.is_in_check(color) and len(self.legal_moves(color)) == 0

    # ── Move Application ──────────────────────────────────────────────────
    def _apply_move_unchecked(self, move):
        """Apply move without legality check. Used internally."""
        fr, fc, tr, tc, promo = move
        piece = self.grid[fr][fc]
        color = piece[0]
        pt = piece[1]

        # En passant capture
        if pt == "P" and (tr, tc) == self.en_passant_target:
            cap_row = fr  # captured pawn is on same rank as moving pawn
            self.grid[cap_row][tc] = EMPTY

        # Update en passant target
        if pt == "P" and abs(fr - tr) == 2:
            self.en_passant_target = ((fr + tr) // 2, fc)
        else:
            self.en_passant_target = None

        # Castling — move the rook too
        if pt == "K":
            if fc == 4 and tc == 6:  # Kingside
                self.grid[fr][5] = self.grid[fr][7]
                self.grid[fr][7] = EMPTY
            elif fc == 4 and tc == 2:  # Queenside
                self.grid[fr][3] = self.grid[fr][0]
                self.grid[fr][0] = EMPTY

        # Update castling rights
        if pt == "K":
            self.castling_rights[color + "K"] = False
            self.castling_rights[color + "Q"] = False
        if pt == "R":
            if fr == 7 and fc == 0: self.castling_rights["wQ"] = False
            if fr == 7 and fc == 7: self.castling_rights["wK"] = False
            if fr == 0 and fc == 0: self.castling_rights["bQ"] = False
            if fr == 0 and fc == 7: self.castling_rights["bK"] = False

        # Move the piece
        if promo:
            self.grid[tr][tc] = color + promo
        else:
            self.grid[tr][tc] = piece
        self.grid[fr][fc] = EMPTY

    def make_move(self, move):
        """Apply a legal move and switch turns."""
        self._apply_move_unchecked(move)
        notation = self._move_to_algebraic(move)
        self.move_history.append(notation)
        self.turn = "b" if self.turn == "w" else "w"

    def _move_to_algebraic(self, move):
        fr, fc, tr, tc, promo = move
        s = chr(fc + ord('a')) + str(8 - fr) + chr(tc + ord('a')) + str(8 - tr)
        if promo:
            s += promo.lower()
        return s


# ═══════════════════════════════════════════════════════════════════════════════
# Bot AI — Minimax with Alpha-Beta Pruning (NOT brute force)
# ═══════════════════════════════════════════════════════════════════════════════

BOT_DEPTH = 3  # Fixed shallow depth — NOT brute force

def evaluate_board(board):
    """Evaluate board position from white's perspective.

    Uses material counting + piece-square table bonuses.
    This is a heuristic evaluation, not exhaustive search.
    """
    score = 0
    for r in range(8):
        for c in range(8):
            piece = board.grid[r][c]
            if piece == EMPTY:
                continue
            color = piece[0]
            pt = piece[1]
            value = PIECE_VALUES.get(pt, 0) + pst_value(pt, color, r, c)
            if color == "w":
                score += value
            else:
                score -= value
    return score


def minimax(board, depth, alpha, beta, maximizing):
    """Minimax search with alpha-beta pruning.

    - depth: remaining search depth (fixed at BOT_DEPTH=3)
    - alpha/beta: pruning bounds
    - maximizing: True if white's turn in search tree

    NOT brute force: search is bounded by depth limit and
    alpha-beta eliminates most branches.
    """
    color = "w" if maximizing else "b"

    if depth == 0:
        return evaluate_board(board), None

    moves = board.legal_moves(color)
    if not moves:
        if board.is_in_check(color):
            # Checkmate: very bad for the side in check
            return (-99999 if maximizing else 99999), None
        return 0, None  # Stalemate

    best_move = moves[0]

    if maximizing:
        max_eval = -999999
        for move in moves:
            child = board.copy()
            child._apply_move_unchecked(move)
            child.turn = "b"
            eval_score, _ = minimax(child, depth - 1, alpha, beta, False)
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break  # Alpha-beta prune
        return max_eval, best_move
    else:
        min_eval = 999999
        for move in moves:
            child = board.copy()
            child._apply_move_unchecked(move)
            child.turn = "w"
            eval_score, _ = minimax(child, depth - 1, alpha, beta, True)
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:
                break  # Alpha-beta prune
        return min_eval, best_move


def bot_choose_move(board):
    """Have the bot pick its move using minimax search."""
    maximizing = (board.turn == "w")
    _, move = minimax(board, BOT_DEPTH, -999999, 999999, maximizing)
    return move


# ═══════════════════════════════════════════════════════════════════════════════
# Input Parsing
# ═══════════════════════════════════════════════════════════════════════════════

def parse_move_input(text, board):
    """Parse algebraic notation like 'e2e4' or 'e2 e4' or 'e7e8q' (promotion)."""
    text = text.strip().lower().replace(" ", "")
    if len(text) < 4 or len(text) > 5:
        return None
    try:
        fc = ord(text[0]) - ord('a')
        fr = 8 - int(text[1])
        tc = ord(text[2]) - ord('a')
        tr = 8 - int(text[3])
        promo = text[4].upper() if len(text) == 5 else None
    except (ValueError, IndexError):
        return None

    if not (0 <= fr < 8 and 0 <= fc < 8 and 0 <= tr < 8 and 0 <= tc < 8):
        return None

    # Match against legal moves
    for move in board.legal_moves():
        mfr, mfc, mtr, mtc, mpromo = move
        if mfr == fr and mfc == fc and mtr == tr and mtc == tc:
            if mpromo and promo:
                if mpromo == promo:
                    return move
            elif mpromo and not promo:
                # Default to queen promotion
                return (mfr, mfc, mtr, mtc, "Q")
            elif not mpromo:
                return move
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# Game Loop
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    board = Board()
    human_color = "w"
    bot_color = "b"

    print("=" * 50)
    print("   TERMINAL CHESS — You vs. Bot")
    print("=" * 50)
    print(f"You play as White ({UNICODE_PIECES['wK']})")
    print(f"Bot plays as Black ({UNICODE_PIECES['bK']})")
    print("Enter moves as: e2e4, d7d5, e1g1 (castling)")
    print("Pawn promotion: e7e8q (append piece letter)")
    print("Type 'quit' to resign, 'moves' to see legal moves")
    print("=" * 50)

    while True:
        board.display()
        current = board.turn

        # Check game-ending conditions
        if board.is_checkmate(current):
            winner = "Black (Bot)" if current == "w" else "White (You)"
            print(f"CHECKMATE! {winner} wins!")
            break
        if board.is_stalemate(current):
            print("STALEMATE! The game is a draw.")
            break
        if board.is_in_check(current):
            who = "You are" if current == human_color else "Bot is"
            print(f"  >>> {who} in CHECK! <<<")

        if current == human_color:
            # Human's turn
            while True:
                try:
                    user_input = input(f"Your move ({board.turn}): ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\nGame ended.")
                    return
                if user_input.lower() == "quit":
                    print("You resigned. Bot wins!")
                    return
                if user_input.lower() == "moves":
                    legal = board.legal_moves()
                    move_strs = [board._move_to_algebraic(m) for m in legal]
                    print(f"Legal moves ({len(legal)}): {', '.join(move_strs)}")
                    continue
                move = parse_move_input(user_input, board)
                if move is None:
                    print("Invalid move. Use format like 'e2e4'. Type 'moves' to see legal moves.")
                    continue
                break
            board.make_move(move)
            print(f"  You played: {board.move_history[-1]}")
        else:
            # Bot's turn
            print("  Bot is thinking...")
            move = bot_choose_move(board)
            if move is None:
                print("Bot has no legal moves!")
                break
            board.make_move(move)
            print(f"  Bot played: {board.move_history[-1]}")

    print(f"\nGame over. Moves: {', '.join(board.move_history)}")


if __name__ == "__main__":
    main()
'''

IMPLEMENTER_ARTIFACT = f"""\
# Chess Game Implementation

Here is the complete, self-contained Python chess game. It includes:
- Full board representation with all standard chess pieces
- Legal move generation for all piece types (including castling, en passant, pawn promotion)
- Check, checkmate, and stalemate detection
- Bot AI using minimax with alpha-beta pruning at fixed depth 3 (NOT brute force)
- Piece-square tables for positional evaluation (center control, king safety, etc.)
- Terminal display with Unicode chess pieces
- Algebraic notation input (e.g., e2e4, d7d5)
- Game loop with 'quit' and 'moves' commands

The file is chess.py and can be run directly with: python chess.py

Technical details of the bot:
- Material values: P=100, N=320, B=330, R=500, Q=900, K=20000
- Piece-square tables give positional bonuses (e.g., knights are worth more in the center)
- Minimax with alpha-beta pruning searches only 3 moves ahead (fixed depth)
- Alpha-beta pruning eliminates most branches so it's efficient, not brute force
- The bot evaluates ~1000-5000 positions per move, not millions

The complete source code is below:

```python
{CHESS_PY_CONTENT}
```
"""

TESTER_ARTIFACT = """\
# Chess Implementation Review

## Findings
After reviewing the chess implementation, here are my observations:

### Correct:
1. Board representation is standard 8x8 grid — OK
2. All 6 piece types have correct move generation (pawn, knight, bishop, rook, queen, king)
3. Special moves implemented: castling (both sides), en passant, pawn promotion
4. Check detection uses square-attack checking — correct approach
5. Checkmate = in check + no legal moves — correct
6. Stalemate = not in check + no legal moves — correct
7. Bot uses minimax with alpha-beta pruning at depth 3 — NOT brute force ✓
8. Piece-square tables provide positional evaluation — good heuristic
9. Legal move filtering correctly prevents moves that leave king in check
10. Move input parsing handles algebraic notation correctly

### Potential Issues:
- No draw by repetition or 50-move rule — acceptable for a simple terminal game
- No opening book for the bot — OK, the user didn't request this
- Castling rights correctly updated when rooks/kings move

### Verdict:
The implementation is complete, correct, and runnable. The bot uses heuristic evaluation
with bounded depth search, which is explicitly NOT brute force. Ready for delivery.
"""

# ── DeliveryPlan (synthesis phase) ────────────────────────────────────────────
DELIVERY_RESPONSE = json.dumps({
    "files": [
        {
            "path": "chess.py",
            "content": CHESS_PY_CONTENT
        }
    ],
    "commit_message": "feat: add terminal chess game with AI opponent using minimax + piece-square tables",
    "pr_title": "Add terminal chess game with bot opponent"
})

# ── ReviewResult (review phase) ──────────────────────────────────────────────
REVIEW_RESPONSE = json.dumps({
    "approved": True,
    "issues": []
})


# ── 4. Build the response queue ──────────────────────────────────────────────
# The pipeline calls in order:
#   1. sync_generate_and_parse(planner, ..., WorkflowPlan)  -> PLAN
#   2. sync_generate_with_retry(executor, ...) per agent     -> artifacts
#   3. sync_generate_and_parse(executor, ..., DeliveryPlan)  -> delivery
#   4. sync_generate_and_parse(reviewer, ..., ReviewResult)  -> review

call_log = []
call_counter = {"n": 0}

# Map of expected calls and their responses
def make_response_object(text):
    """Create a fake Gemini response that extract_text() can handle."""
    class FakePart:
        def __init__(self, t): self.text = t
    class FakeContent:
        def __init__(self, t): self.parts = [FakePart(t)]
    class FakeCandidate:
        def __init__(self, t): self.content = FakeContent(t)
    class FakeResponse:
        def __init__(self, t): self.candidates = [FakeCandidate(t)]
    return FakeResponse(text)


class MockModel:
    """Mock LLM that returns pre-scripted responses based on prompt analysis."""
    def __init__(self, role_name):
        self.role_name = role_name
        self.model_name = "mock-copilot-agent"
        self.system_instruction = f"Mock {role_name}"

    def generate_content(self, prompt, generation_config=None):
        n = call_counter["n"]
        call_counter["n"] += 1

        prompt_str = str(prompt)[:500]
        config = generation_config or {}
        schema = config.get("response_schema")

        # Detect what kind of call this is
        if schema and hasattr(schema, '__name__'):
            schema_name = schema.__name__
        else:
            schema_name = None

        # Route to correct response
        if schema_name == "WorkflowPlan":
            response_text = PLAN_RESPONSE
            call_type = "PLAN (WorkflowPlan)"
        elif schema_name == "DeliveryPlan":
            response_text = DELIVERY_RESPONSE
            call_type = "DELIVERY (DeliveryPlan)"
        elif schema_name == "ReviewResult":
            response_text = REVIEW_RESPONSE
            call_type = "REVIEW (ReviewResult)"
        elif "Role: Design the chess game architecture" in prompt_str or "game_architect" in prompt_str[:100]:
            response_text = ARCHITECT_ARTIFACT
            call_type = "AGENT: game_architect"
        elif "Role: Review the chess" in prompt_str or ("tester" in prompt_str[:80] and "Role:" in prompt_str):
            response_text = TESTER_ARTIFACT
            call_type = "AGENT: tester"
        elif "Role: Implement the complete chess" in prompt_str or "chess_implementer" in prompt_str[:100]:
            response_text = IMPLEMENTER_ARTIFACT
            call_type = "AGENT: chess_implementer"
        else:
            # Fallback: return a safe response
            response_text = json.dumps({"status": "ok", "message": "acknowledged"})
            call_type = f"UNKNOWN ({self.role_name})"

        log_entry = f"  LLM Call #{n}: [{call_type}] via {self.role_name}"
        call_log.append(log_entry)
        print(log_entry)

        return make_response_object(response_text)


# ── 5. Monkey-patch everything ───────────────────────────────────────────────

# Patch create_models to return mocks
_original_create_models = app_old.create_models
def mock_create_models(provider="gemini", ollama_model="", ollama_base_url=""):
    print(f"  [MOCK] create_models(provider={provider})")
    return (
        MockModel("planner"),
        MockModel("executor"),
        MockModel("reviewer"),
        MockModel("fixer"),
    )
app_old.create_models = mock_create_models

# Patch _create_model for per-agent custom models
_original_create_model = app_old._create_model
def mock_create_model(provider, system_instruction, ollama_model="", ollama_base_url=""):
    return MockModel(f"custom({system_instruction[:40]}...)")
app_old._create_model = mock_create_model

# Patch run_git to skip all git operations
class FakeGitResult:
    def __init__(self, stdout="", stderr=""):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = 0

def mock_run_git(*args, cwd=None, timeout=120):
    cmd = " ".join(str(a) for a in args)
    print(f"  [MOCK] git {cmd[:80]}")

    if "clone" in args:
        # Create the workspace directory (simulates clone)
        if len(args) >= 2:
            dest = args[-1]
            workspace_path = pathlib.Path(dest)
            workspace_path.mkdir(parents=True, exist_ok=True)
            # Create a minimal repo structure
            (workspace_path / "README.md").write_text(
                "# silver-pancake\nA test repository.\n", encoding="utf-8"
            )
            (workspace_path / "requirements.txt").write_text("", encoding="utf-8")
            print(f"  [MOCK] Created workspace at {workspace_path}")
    elif "diff" in args and "--cached" in args:
        return FakeGitResult(stdout="chess.py | 400 +++\n 1 file changed, 400 insertions(+)")
    elif "push" in args:
        print("  [MOCK] Skipping git push (test mode)")
    return FakeGitResult()

app_old.run_git = mock_run_git

# Patch github_api_request to skip PR creation
def mock_github_api_request(method, url, payload=None):
    print(f"  [MOCK] GitHub API: {method} {url[:60]}")
    return {"html_url": "https://github.com/test/test/pull/999 (MOCK)"}
app_old.github_api_request = mock_github_api_request

# Override BASE_WORKSPACE to use local temp dir
LOCAL_WORKSPACE = pathlib.Path(__file__).resolve().parent / "test_workspace"
if LOCAL_WORKSPACE.exists():
    _pre_rmtree = shutil.rmtree
    _pre_rmtree(LOCAL_WORKSPACE)
LOCAL_WORKSPACE.mkdir(parents=True, exist_ok=True)
app_old.BASE_WORKSPACE = LOCAL_WORKSPACE

# Prevent the finally block from cleaning up so we can inspect output
def mock_rmtree(path, **kwargs):
    print(f"  [MOCK] Skipping cleanup of {path}")
shutil.rmtree = mock_rmtree

# ── 6. Run the pipeline ─────────────────────────────────────────────────────

def main():
    job_id = "chess_test_01"
    app_old.create_job(job_id, USER_GOAL)

    print("=" * 70)
    print("  AUTO-SDLC PIPELINE TEST — Copilot as LLM Backend")
    print("=" * 70)
    print(f"  Job ID:  {job_id}")
    print(f"  Goal:    {USER_GOAL[:80]}...")
    print(f"  Workspace: {LOCAL_WORKSPACE}")
    print("=" * 70)
    print()

    start = time.time()

    # Run the full sync pipeline
    app_old._sync_generation_pipeline(
        job_id=job_id,
        user_goal=USER_GOAL,
        llm_provider="gemini",
        review_cycles=2,
    )

    elapsed = time.time() - start

    # ── Report Results ────────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("  PIPELINE COMPLETE")
    print("=" * 70)
    print(f"  Duration: {elapsed:.1f}s")
    print(f"  LLM calls: {call_counter['n']}")
    print()

    # Get job status
    job = app_old._jobs.get(job_id, {})
    print(f"  Status:  {job.get('status', 'unknown')}")
    print(f"  Step:    {job.get('current_step', 'unknown')}")
    if job.get("result"):
        print(f"  Result:  {job['result']}")
    if job.get("error"):
        print(f"  Error:   {job['error'][:300]}")
    print()

    # Show agent states
    if job.get("agent_states"):
        print("  Agent States:")
        for name, state in job["agent_states"].items():
            print(f"    {name}: {state}")
        print()

    # Show events
    if job.get("events"):
        print(f"  Events ({len(job['events'])}):")
        for evt in job["events"][-20:]:
            evt_type = evt.get("type", "?")
            agent = evt.get("agent", "")
            msg = evt.get("error", evt.get("reason", ""))
            ts = time.strftime("%H:%M:%S", time.localtime(evt["t"] / 1000))
            extra = f" [{agent}]" if agent else ""
            extra += f" — {msg[:80]}" if msg else ""
            print(f"    [{ts}] {evt_type}{extra}")
        print()

    # Show LLM call log
    print("  LLM Call Log:")
    for entry in call_log:
        print(f"  {entry}")
    print()

    # Check if output files exist
    output_dir = LOCAL_WORKSPACE
    run_dir = output_dir / f"run-{job_id}"
    if run_dir.exists():
        chess_file = run_dir / "chess.py"
        if chess_file.exists():
            content = chess_file.read_text(encoding="utf-8")
            print(f"  OUTPUT: chess.py written ({len(content)} chars)")
            print(f"  Location: {chess_file}")

            # Copy to sandbox for easy access
            dest = pathlib.Path(__file__).resolve().parent / "chess_output.py"
            dest.write_text(content, encoding="utf-8")
            print(f"  Also copied to: {dest}")
        else:
            print("  WARNING: chess.py was not written to workspace")
            # List what IS in the workspace
            for p in run_dir.rglob("*"):
                if p.is_file():
                    print(f"    Found: {p.relative_to(run_dir)}")
    else:
        print(f"  WARNING: Run directory {run_dir} does not exist")
        # Check artifacts
        artifacts_dir = output_dir / f"artifacts-{job_id}"
        if artifacts_dir.exists():
            print(f"  Artifacts dir exists: {artifacts_dir}")
            for p in artifacts_dir.glob("*"):
                size = p.stat().st_size
                print(f"    {p.name} ({size} bytes)")

    print()
    print("=" * 70)
    print("  TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
