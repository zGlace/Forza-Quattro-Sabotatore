:- module(bitboard, [
    cols/1,
    rows/1,
    total_cells/1,
    empty_board/3,
    bottom_mask/2,
    top_mask/2,
    sentinel_mask/2,
    column_mask/2,
    all_sentinels_mask/1,
    can_play/2,
    valid_moves/2,
    drop_piece/9,
    check_win/1,
    win_after_drop/2,
    board_full/1,
    board_pieces_count/2,
    bit_to_coord/3,
    coord_to_bit/3,
    board_to_matrix/3
]).

% 81-bit bitboard (John Tromp method): 9 columns with a 9-bit stride (8 cells + 1 sentinel bit set to 0).


% DIMENSIONS AND INITIAL STATE
cols(9).
rows(8).
total_cells(72).
empty_board(0, 0, 0).

% COLUMN MASKS (1..9)
bottom_mask(Col, Mask) :-
    Col >= 1, Col =< 9,
    Mask is 1 << ((Col - 1) * 9).

top_mask(Col, Mask) :-
    Col >= 1, Col =< 9,
    Mask is 1 << ((Col - 1) * 9 + 7).

sentinel_mask(Col, Mask) :-
    Col >= 1, Col =< 9,
    Mask is 1 << ((Col - 1) * 9 + 8).

column_mask(Col, Mask) :-
    Col >= 1, Col =< 9,
    Mask is 255 << ((Col - 1) * 9).

all_sentinels_mask(Mask) :-
    Mask is (1 << 8)  \/ (1 << 17) \/ (1 << 26) \/ (1 << 35) \/
            (1 << 44) \/ (1 << 53) \/ (1 << 62) \/ (1 << 71) \/ (1 << 80).


% VALIDITY AND EXECUTION OF MOVES IN O(1)
can_play(Mask, Col) :-
    Col >= 1, Col =< 9,
    Top is 1 << ((Col - 1) * 9 + 7),
    (Mask /\ Top) =:= 0.

valid_moves(Mask, Moves) :-
    findall(C, (between(1, 9, C), can_play(Mask, C)), Moves).

% Drop piece in O(1) via binary addition
drop_piece(BoardP1, BoardP2, Mask, Col, Piece, NewBoardP1, NewBoardP2, NewMask, MoveBit) :-
    can_play(Mask, Col),
    Bottom is 1 << ((Col - 1) * 9),
    NewMask is Mask \/ (Mask + Bottom),
    MoveBit is NewMask xor Mask,
    ( Piece == 1 ->
        NewBoardP1 is BoardP1 \/ MoveBit,
        NewBoardP2 = BoardP2
    ; Piece == 2 ->
        NewBoardP1 = BoardP1,
        NewBoardP2 is BoardP2 \/ MoveBit
    ).


% RECOGNITION OF 4-IN-A-ROW (BITWISE SHIFTS IN 4 DIRECTIONS)
check_win(Board) :-
    ( check_dir(Board, 1) -> true   % Vertical
    ; check_dir(Board, 9) -> true   % Horizontal
    ; check_dir(Board, 10) -> true  % Diagonal /
    ; check_dir(Board, 8)           % Diagonal \
    ).

check_dir(Board, Shift) :-
    M is Board /\ (Board >> Shift),
    Shift2 is 2 * Shift,
    Win is M /\ (M >> Shift2),
    Win =\= 0.

win_after_drop(Board, MoveBit) :-
    NewBoard is Board \/ MoveBit,
    check_win(NewBoard).


% STATE AND PIECES COUNT
board_full(Mask) :-
    (Mask /\ (1 << 7))  =\= 0,
    (Mask /\ (1 << 16)) =\= 0,
    (Mask /\ (1 << 25)) =\= 0,
    (Mask /\ (1 << 34)) =\= 0,
    (Mask /\ (1 << 43)) =\= 0,
    (Mask /\ (1 << 52)) =\= 0,
    (Mask /\ (1 << 61)) =\= 0,
    (Mask /\ (1 << 70)) =\= 0,
    (Mask /\ (1 << 79)) =\= 0.

board_pieces_count(Mask, Count) :-
    Count is popcount(Mask).


% CONVERSIONS OF COORDINATES (Row 0..7, Col 1..9) AND MATRIX
coord_to_bit(Row, Col, Bit) :-
    between(0, 7, Row),
    between(1, 9, Col),
    Bit is (Col - 1) * 9 + Row.

bit_to_coord(Bit, Row, Col) :-
    Col is (Bit // 9) + 1,
    Row is Bit mod 9.

% Generates an 8x9 matrix from top to bottom (0=empty, 1=Red, 2=Yellow)
board_to_matrix(BoardP1, BoardP2, Matrix) :-
    findall(RowList,
        ( between(0, 7, R_inv),
          Row is 7 - R_inv,
          findall(Val,
              ( between(1, 9, Col),
                Bit is (Col - 1) * 9 + Row,
                Mask is 1 << Bit,
                ( (BoardP1 /\ Mask) =\= 0 -> Val = 1
                ; (BoardP2 /\ Mask) =\= 0 -> Val = 2
                ; Val = 0
                )
              ),
              RowList)
        ),
        Matrix).
