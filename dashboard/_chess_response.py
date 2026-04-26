#!/usr/bin/env python3
"""Terminal Chess Game - Human (White) vs Heuristic Bot (Black)

Run: python chess.py
Enter moves in algebraic notation: e2e4, d7d5, etc.
Type 'quit' to exit, 'moves' to see legal moves.
"""

import copy
import random

# ── Piece encoding ────────────────────────────────────────────────────────────
# Uppercase = White, lowercase = Black, '.' = empty

INITIAL_BOARD = [
    ['r','n','b','q','k','b','n','r'],
    ['p','p','p','p','p','p','p','p'],
    ['.','.','.','.','.','.','.','.'],
    ['.','.','.','.','.','.','.','.'],
    ['.','.','.','.','.','.','.','.'],
    ['.','.','.','.','.','.','.','.'],
    ['P','P','P','P','P','P','P','P'],
    ['R','N','B','Q','K','B','N','R'],
]

PIECE_VALUES = {'P':100,'N':320,'B':330,'R':500,'Q':900,'K':0,
                'p':100,'n':320,'b':330,'r':500,'q':900,'k':0}

# ── Piece-Square Tables (from White's perspective; flipped for Black) ─────────
PAWN_TABLE = [
    [  0,  0,  0,  0,  0,  0,  0,  0],
    [ 50, 50, 50, 50, 50, 50, 50, 50],
    [ 10, 10, 20, 30, 30, 20, 10, 10],
    [  5,  5, 10, 25, 25, 10,  5,  5],
    [  0,  0,  0, 20, 20,  0,  0,  0],
    [  5, -5,-10,  0,  0,-10, -5,  5],
    [  5, 10, 10,-20,-20, 10, 10,  5],
    [  0,  0,  0,  0,  0,  0,  0,  0],
]

KNIGHT_TABLE = [
    [-50,-40,-30,-30,-30,-30,-40,-50],
    [-40,-20,  0,  0,  0,  0,-20,-40],
    [-30,  0, 10, 15, 15, 10,  0,-30],
    [-30,  5, 15, 20, 20, 15,  5,-30],
    [-30,  0, 15, 20, 20, 15,  0,-30],
    [-30,  5, 10, 15, 15, 10,  5,-30],
    [-40,-20,  0,  5,  5,  0,-20,-40],
    [-50,-40,-30,-30,-30,-30,-40,-50],
]

BISHOP_TABLE = [
    [-20,-10,-10,-10,-10,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0, 10, 10, 10, 10,  0,-10],
    [-10,  5,  5, 10, 10,  5,  5,-10],
    [-10,  0,  5, 10, 10,  5,  0,-10],
    [-10, 10, 10, 10, 10, 10, 10,-10],
    [-10,  5,  0,  0,  0,  0,  5,-10],
    [-20,-10,-10,-10,-10,-10,-10,-20],
]

ROOK_TABLE = [
    [  0,  0,  0,  0,  0,  0,  0,  0],
    [  5, 10, 10, 10, 10, 10, 10,  5],
    [ -5,  0,  0,  0,  0,  0,  0, -5],
    [ -5,  0,  0,  0,  0,  0,  0, -5],
    [ -5,  0,  0,  0,  0,  0,  0, -5],
    [ -5,  0,  0,  0,  0,  0,  0, -5],
    [ -5,  0,  0,  0,  0,  0,  0, -5],
    [  0,  0,  0,  5,  5,  0,  0,  0],
]

QUEEN_TABLE = [
    [-20,-10,-10, -5, -5,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5,  5,  5,  5,  0,-10],
    [ -5,  0,  5,  5,  5,  5,  0, -5],
    [  0,  0,  5,  5,  5,  5,  0, -5],
    [-10,  5,  5,  5,  5,  5,  0,-10],
    [-10,  0,  5,  0,  0,  0,  0,-10],
    [-20,-10,-10, -5, -5,-10,-10,-20],
]

KING_TABLE = [
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-20,-30,-30,-40,-40,-30,-30,-20],
    [-10,-20,-20,-20,-20,-20,-20,-10],
    [ 20, 20,  0,  0,  0,  0, 20, 20],
    [ 20, 30, 10,  0,  0, 10, 30, 20],
]

PST = {
    'P': PAWN_TABLE, 'N': KNIGHT_TABLE, 'B': BISHOP_TABLE,
    'R': ROOK_TABLE, 'Q': QUEEN_TABLE, 'K': KING_TABLE,
}


def piece_color(piece):
    if piece == '.':
        return None
    return 'white' if piece.isupper() else 'black'


def opponent(color):
    return 'black' if color == 'white' else 'white'


# ── Coordinate helpers ────────────────────────────────────────────────────────

def to_algebraic(row, col):
    return chr(col + ord('a')) + str(8 - row)


def from_algebraic(s):
    col = ord(s[0]) - ord('a')
    row = 8 - int(s[1])
    return row, col


def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8


# ── Game State ────────────────────────────────────────────────────────────────

class GameState:
    def __init__(self):
        self.board = [row[:] for row in INITIAL_BOARD]
        self.turn = 'white'
        self.castling = {'K': True, 'Q': True, 'k': True, 'q': True}
        self.en_passant = None  # (row, col) target square
        self.halfmove = 0
        self.history = []

    def copy(self):
        gs = GameState.__new__(GameState)
        gs.board = [row[:] for row in self.board]
        gs.turn = self.turn
        gs.castling = dict(self.castling)
        gs.en_passant = self.en_passant
        gs.halfmove = self.halfmove
        gs.history = list(self.history)
        return gs


# ── Move generation ───────────────────────────────────────────────────────────

def pseudo_legal_moves(board, color, en_passant=None):
    """Generate all pseudo-legal moves (may leave own king in check)."""
    moves = []
    forward = -1 if color == 'white' else 1
    start_row = 6 if color == 'white' else 1
    promo_row = 0 if color == 'white' else 7

    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece_color(piece) != color:
                continue
            pt = piece.upper()

            if pt == 'P':
                # Forward 1
                nr = r + forward
                if in_bounds(nr, c) and board[nr][c] == '.':
                    if nr == promo_row:
                        for promo in ('Q','R','B','N'):
                            moves.append((r, c, nr, c, promo))
                    else:
                        moves.append((r, c, nr, c, None))
                    # Forward 2 from start
                    nr2 = r + 2 * forward
                    if r == start_row and board[nr2][c] == '.':
                        moves.append((r, c, nr2, c, None))
                # Diagonal captures
                for dc in (-1, 1):
                    nc = c + dc
                    nr = r + forward
                    if not in_bounds(nr, nc):
                        continue
                    target = board[nr][nc]
                    if target != '.' and piece_color(target) != color:
                        if nr == promo_row:
                            for promo in ('Q','R','B','N'):
                                moves.append((r, c, nr, nc, promo))
                        else:
                            moves.append((r, c, nr, nc, None))
                    # En passant
                    if en_passant and (nr, nc) == en_passant:
                        moves.append((r, c, nr, nc, 'ep'))

            elif pt == 'N':
                for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),
                                (1,-2),(1,2),(2,-1),(2,1)]:
                    nr, nc = r+dr, c+dc
                    if in_bounds(nr, nc) and piece_color(board[nr][nc]) != color:
                        moves.append((r, c, nr, nc, None))

            elif pt == 'B':
                for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
                    nr, nc = r+dr, c+dc
                    while in_bounds(nr, nc):
                        if board[nr][nc] == '.':
                            moves.append((r, c, nr, nc, None))
                        elif piece_color(board[nr][nc]) != color:
                            moves.append((r, c, nr, nc, None))
                            break
                        else:
                            break
                        nr += dr
                        nc += dc

            elif pt == 'R':
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r+dr, c+dc
                    while in_bounds(nr, nc):
                        if board[nr][nc] == '.':
                            moves.append((r, c, nr, nc, None))
                        elif piece_color(board[nr][nc]) != color:
                            moves.append((r, c, nr, nc, None))
                            break
                        else:
                            break
                        nr += dr
                        nc += dc

            elif pt == 'Q':
                for dr, dc in [(-1,-1),(-1,0),(-1,1),(0,-1),
                                (0,1),(1,-1),(1,0),(1,1)]:
                    nr, nc = r+dr, c+dc
                    while in_bounds(nr, nc):
                        if board[nr][nc] == '.':
                            moves.append((r, c, nr, nc, None))
                        elif piece_color(board[nr][nc]) != color:
                            moves.append((r, c, nr, nc, None))
                            break
                        else:
                            break
                        nr += dr
                        nc += dc

            elif pt == 'K':
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r+dr, c+dc
                        if in_bounds(nr, nc) and piece_color(board[nr][nc]) != color:
                            moves.append((r, c, nr, nc, None))

    return moves


def is_square_attacked(board, row, col, by_color):
    """Check if square (row,col) is attacked by any piece of by_color."""
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece_color(piece) != by_color:
                continue
            pt = piece.upper()
            dr, dc = row - r, col - c

            if pt == 'P':
                fwd = -1 if by_color == 'white' else 1
                if dr == fwd and abs(dc) == 1:
                    return True

            elif pt == 'N':
                if (abs(dr), abs(dc)) in ((1,2),(2,1)):
                    return True

            elif pt == 'K':
                if abs(dr) <= 1 and abs(dc) <= 1 and (dr, dc) != (0, 0):
                    return True

            elif pt == 'B':
                if abs(dr) == abs(dc) and dr != 0:
                    sr = 1 if dr > 0 else -1
                    sc = 1 if dc > 0 else -1
                    cr, cc = r + sr, c + sc
                    blocked = False
                    while (cr, cc) != (row, col):
                        if board[cr][cc] != '.':
                            blocked = True
                            break
                        cr += sr
                        cc += sc
                    if not blocked:
                        return True

            elif pt == 'R':
                if (dr == 0 or dc == 0) and (dr, dc) != (0, 0):
                    sr = (1 if dr > 0 else -1) if dr != 0 else 0
                    sc = (1 if dc > 0 else -1) if dc != 0 else 0
                    cr, cc = r + sr, c + sc
                    blocked = False
                    while (cr, cc) != (row, col):
                        if board[cr][cc] != '.':
                            blocked = True
                            break
                        cr += sr
                        cc += sc
                    if not blocked:
                        return True

            elif pt == 'Q':
                if dr == 0 or dc == 0 or abs(dr) == abs(dc):
                    if (dr, dc) != (0, 0):
                        sr = (1 if dr > 0 else -1) if dr != 0 else 0
                        sc = (1 if dc > 0 else -1) if dc != 0 else 0
                        cr, cc = r + sr, c + sc
                        blocked = False
                        while (cr, cc) != (row, col):
                            if board[cr][cc] != '.':
                                blocked = True
                                break
                            cr += sr
                            cc += sc
                        if not blocked:
                            return True
    return False


def find_king(board, color):
    king = 'K' if color == 'white' else 'k'
    for r in range(8):
        for c in range(8):
            if board[r][c] == king:
                return r, c
    return None


def is_in_check(board, color):
    pos = find_king(board, color)
    if pos is None:
        return True
    return is_square_attacked(board, pos[0], pos[1], opponent(color))


def apply_move(state, move):
    """Apply move and return new GameState. Does NOT validate legality."""
    r1, c1, r2, c2, special = move
    ns = state.copy()
    board = ns.board
    piece = board[r1][c1]
    captured = board[r2][c2]
    color = piece_color(piece)

    # Reset or increment halfmove clock
    if piece.upper() == 'P' or captured != '.':
        ns.halfmove = 0
    else:
        ns.halfmove += 1

    # En passant capture
    if special == 'ep':
        board[r1][c2] = '.'  # remove captured pawn
        board[r2][c2] = piece
        board[r1][c1] = '.'
        ns.en_passant = None
        ns.history.append(move)
        ns.turn = opponent(color)
        return ns

    # Move the piece
    board[r2][c2] = piece
    board[r1][c1] = '.'

    # Pawn promotion
    if special in ('Q','R','B','N'):
        promo_piece = special if color == 'white' else special.lower()
        board[r2][c2] = promo_piece

    # En passant target
    ns.en_passant = None
    if piece.upper() == 'P' and abs(r2 - r1) == 2:
        ns.en_passant = ((r1 + r2) // 2, c1)

    # Castling
    if piece.upper() == 'K':
        if color == 'white':
            ns.castling['K'] = False
            ns.castling['Q'] = False
        else:
            ns.castling['k'] = False
            ns.castling['q'] = False
        # Move rook for castling
        if abs(c2 - c1) == 2:
            if c2 > c1:  # kingside
                board[r1][5] = board[r1][7]
                board[r1][7] = '.'
            else:  # queenside
                board[r1][3] = board[r1][0]
                board[r1][0] = '.'

    # Update castling rights on rook moves/captures
    if piece.upper() == 'R':
        if color == 'white':
            if (r1, c1) == (7, 7): ns.castling['K'] = False
            if (r1, c1) == (7, 0): ns.castling['Q'] = False
        else:
            if (r1, c1) == (0, 7): ns.castling['k'] = False
            if (r1, c1) == (0, 0): ns.castling['q'] = False
    # Rook captured
    if (r2, c2) == (7, 7): ns.castling['K'] = False
    if (r2, c2) == (7, 0): ns.castling['Q'] = False
    if (r2, c2) == (0, 7): ns.castling['k'] = False
    if (r2, c2) == (0, 0): ns.castling['q'] = False

    ns.history.append(move)
    ns.turn = opponent(color)
    return ns


def get_legal_moves(state, color=None):
    """Return list of legal moves for the given color."""
    if color is None:
        color = state.turn
    pseudo = pseudo_legal_moves(state.board, color, state.en_passant)
    legal = []

    # Add castling moves
    king_pos = find_king(state.board, color)
    if king_pos:
        kr, kc = king_pos
        opp = opponent(color)
        if not is_in_check(state.board, color):
            # Kingside
            ks_key = 'K' if color == 'white' else 'k'
            if state.castling[ks_key]:
                if (state.board[kr][5] == '.' and state.board[kr][6] == '.'
                    and not is_square_attacked(state.board, kr, 5, opp)
                    and not is_square_attacked(state.board, kr, 6, opp)):
                    pseudo.append((kr, kc, kr, kc+2, None))
            # Queenside
            qs_key = 'Q' if color == 'white' else 'q'
            if state.castling[qs_key]:
                if (state.board[kr][3] == '.' and state.board[kr][2] == '.'
                    and state.board[kr][1] == '.'
                    and not is_square_attacked(state.board, kr, 3, opp)
                    and not is_square_attacked(state.board, kr, 2, opp)):
                    pseudo.append((kr, kc, kr, kc-2, None))

    for move in pseudo:
        ns = apply_move(state, move)
        if not is_in_check(ns.board, color):
            legal.append(move)

    return legal


# ── Board display ─────────────────────────────────────────────────────────────

PIECE_SYMBOLS = {
    'K': '\u2654', 'Q': '\u2655', 'R': '\u2656', 'B': '\u2657', 'N': '\u2658', 'P': '\u2659',
    'k': '\u265a', 'q': '\u265b', 'r': '\u265c', 'b': '\u265d', 'n': '\u265e', 'p': '\u265f',
    '.': '.',
}


def display_board(board, use_unicode=True):
    print()
    print("  a b c d e f g h")
    print("  ----------------")
    for r in range(8):
        rank = 8 - r
        row_str = ""
        for c in range(8):
            p = board[r][c]
            if use_unicode and p in PIECE_SYMBOLS:
                row_str += PIECE_SYMBOLS[p] + " "
            else:
                row_str += p + " "
        print(f"{rank}|{row_str}|{rank}")
    print("  ----------------")
    print("  a b c d e f g h")
    print()


# ── Bot AI (heuristic, NO brute force) ───────────────────────────────────────

def get_pst_value(piece, row, col):
    """Get piece-square table value for a piece at (row, col)."""
    pt = piece.upper()
    if pt not in PST:
        return 0
    table = PST[pt]
    if piece.isupper():  # White
        return table[row][col]
    else:  # Black - flip the table vertically
        return table[7 - row][col]


def evaluate_board(board):
    """Evaluate board from White's perspective. Positive = White advantage."""
    score = 0
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece == '.':
                continue
            val = PIECE_VALUES.get(piece.upper(), 0)
            pst = get_pst_value(piece, r, c)
            if piece.isupper():
                score += val + pst
            else:
                score -= val + pst
    return score


def bot_choose_move(state):
    """Bot picks the best move using single-ply heuristic evaluation.
    NO minimax, NO deep search, NO brute force.
    Just: evaluate each legal move's resulting position and pick the best."""
    legal = get_legal_moves(state, 'black')
    if not legal:
        return None

    best_score = float('inf')  # Bot is black, wants LOWEST score (most negative for white)
    best_moves = []

    for move in legal:
        ns = apply_move(state, move)
        score = evaluate_board(ns.board)
        if score < best_score:
            best_score = score
            best_moves = [move]
        elif score == best_score:
            best_moves.append(move)

    # Break ties randomly for variety
    return random.choice(best_moves)


# ── Main game loop ────────────────────────────────────────────────────────────

def format_move(move):
    r1, c1, r2, c2, special = move
    base = to_algebraic(r1, c1) + to_algebraic(r2, c2)
    if special in ('Q','R','B','N'):
        base += special.lower()
    return base


def main():
    state = GameState()
    print("=" * 40)
    print("  TERMINAL CHESS")
    print("  Human (White) vs Bot (Black)")
    print("=" * 40)
    print("Enter moves like: e2e4")
    print("Commands: 'quit', 'moves' (show legal moves)")
    print()

    while True:
        display_board(state.board)

        # Check game-over conditions
        legal = get_legal_moves(state)
        in_check = is_in_check(state.board, state.turn)

        if not legal:
            if in_check:
                winner = opponent(state.turn)
                print(f"CHECKMATE! {winner.capitalize()} wins!")
            else:
                print("STALEMATE! It's a draw.")
            break

        if state.halfmove >= 100:
            print("Draw by 50-move rule!")
            break

        if in_check:
            print(f"  ** {state.turn.capitalize()} is in CHECK! **")

        if state.turn == 'white':
            # Human turn
            while True:
                cmd = input(f"White's move: ").strip().lower()
                if cmd == 'quit':
                    print("Thanks for playing!")
                    return
                if cmd == 'moves':
                    print("Legal moves:", ", ".join(format_move(m) for m in legal))
                    continue
                if len(cmd) < 4 or len(cmd) > 5:
                    print("Invalid format. Use e.g. 'e2e4' or 'e7e8q' for promotion.")
                    continue
                try:
                    fr, fc = from_algebraic(cmd[0:2])
                    tr, tc = from_algebraic(cmd[2:4])
                except (ValueError, IndexError):
                    print("Invalid square. Use a-h for file, 1-8 for rank.")
                    continue

                promo = None
                if len(cmd) == 5:
                    promo = cmd[4].upper()
                    if promo not in ('Q','R','B','N'):
                        print("Invalid promotion piece. Use q, r, b, or n.")
                        continue

                # Find matching legal move
                matched = None
                for m in legal:
                    r1, c1, r2, c2, sp = m
                    if (r1, c1, r2, c2) == (fr, fc, tr, tc):
                        if promo and sp in ('Q','R','B','N'):
                            if sp == promo:
                                matched = m
                                break
                        elif promo is None:
                            if sp not in ('Q','R','B','N'):
                                matched = m
                                break
                        else:
                            matched = m
                            break

                if matched is None:
                    print("Illegal move. Type 'moves' to see legal moves.")
                    continue

                state = apply_move(state, matched)
                print(f"  White plays: {format_move(matched)}")
                break
        else:
            # Bot turn
            print("  Bot is thinking...")
            move = bot_choose_move(state)
            if move is None:
                continue  # will be caught by game-over check above
            state = apply_move(state, move)
            print(f"  Bot plays: {format_move(move)}")

    print("\nGame over!")


if __name__ == "__main__":
    main()
