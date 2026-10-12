:- module(engine, [
    init_game/2,
    play_move/3,
    get_ai_move/3,
    set_difficulty/3,
    get_valid_moves/2,
    get_threat_stats/4,
    turn_info/4
]).

:- use_module(bitboard).
:- use_module(threats).
:- use_module(ai).

% Main module: SWI-Prolog interface for Python (Janus) and state management.

% Turn cycle with 4 phases (R-G-G-R): P1 (Rosso), IA Sabotatore (Giallo), P2 (Giallo), IA Sabotatore (Rosso)
turn_info(1, 1, human, 1).
turn_info(2, 0, ai,    2).
turn_info(3, 2, human, 2).
turn_info(4, 0, ai,    1).


% INITIALIZATION OF THE GAME 
init_game(Difficulty, StateDict) :-
    set_ai_difficulty(Difficulty),
    empty_board(B1, B2, Mask),
    Phase = 1,
    turn_info(Phase, Pid, Kind, Piece),
    board_to_matrix(B1, B2, Matrix),
    InitialTurn = turn(Phase, Pid, Kind, Piece),
    board_threat_stats(B1, B2, Mask, InitialTurn, ThreatStats),
    valid_moves(Mask, ValidCols),
    StateDict = state{
        board_p1: B1,
        board_p2: B2,
        mask: Mask,
        phase: Phase,
        player_id: Pid,
        player_kind: Kind,
        piece: Piece,
        moves: 0,
        difficulty: Difficulty,
        status: 'ongoing',
        winner: 0,
        matrix: Matrix,
        valid_moves: ValidCols,
        threat_stats: ThreatStats
    }.


% EXECUTION OF MOVE AND STATE TRANSITION
play_move(Col, StateIn, StateOut) :-
    StateIn.status == 'ongoing',
    Col >= 1, Col =< 9,
    can_play(StateIn.mask, Col),
    Piece = StateIn.piece,
    drop_piece(StateIn.board_p1, StateIn.board_p2, StateIn.mask,
               Col, Piece,
               NewB1, NewB2, NewMask, MoveBit),

    NewMoves is StateIn.moves + 1,
    board_to_matrix(NewB1, NewB2, NewMatrix),
    valid_moves(NewMask, NewValidCols),
    % Verifies win conditions or board fullness
    ( check_win(NewB1) ->
        Status = 'game_over',
        Winner = 1,
        NextPhase = StateIn.phase,
        turn_info(NextPhase, NextPid, NextKind, NextPiece)
    ; check_win(NewB2) ->
        Status = 'game_over',
        Winner = 2,
        NextPhase = StateIn.phase,
        turn_info(NextPhase, NextPid, NextKind, NextPiece)
    ; ( NewMoves =:= 72 ; NewValidCols == [] ) ->
        Status = 'game_over',
        Winner = 0,
        NextPhase = StateIn.phase,
        turn_info(NextPhase, NextPid, NextKind, NextPiece)
    ;   Status = 'ongoing',
        Winner = 0,
        NextPhase is (StateIn.phase mod 4) + 1,
        turn_info(NextPhase, NextPid, NextKind, NextPiece)
    ),

    NextTurn = turn(NextPhase, NextPid, NextKind, NextPiece),
    board_threat_stats(NewB1, NewB2, NewMask, NextTurn, NewThreatStats),

    StateOut = state{
        board_p1: NewB1,
        board_p2: NewB2,
        mask: NewMask,
        phase: NextPhase,
        player_id: NextPid,
        player_kind: NextKind,
        piece: NextPiece,
        moves: NewMoves,
        difficulty: StateIn.difficulty,
        status: Status,
        winner: Winner,
        matrix: NewMatrix,
        valid_moves: NewValidCols,
        threat_stats: NewThreatStats,
        last_move_col: Col,
        last_move_bit: MoveBit
    }.


% CALCULATION OF AI MOVE AND DIFFICULTY CHANGE
get_ai_move(StateIn, BestCol, InfoDict) :-
    StateIn.status == 'ongoing',
    Difficulty = StateIn.difficulty,
    difficulty_depth(Difficulty, Depth),
    Turn = turn(StateIn.phase, saboteur, ai, StateIn.piece),
    ai_move(StateIn.board_p1, StateIn.board_p2, StateIn.mask,
            Turn, Difficulty, Depth, BestCol, InfoDict).

set_difficulty(Difficulty, StateIn, StateOut) :-
    set_ai_difficulty(Difficulty),
    StateOut = StateIn.put(difficulty, Difficulty).


% UTILITY PREDICATES 
get_valid_moves(Mask, Moves) :-
    valid_moves(Mask, Moves).

get_threat_stats(BoardP1, BoardP2, Mask, ThreatStats) :-
    board_threat_stats(BoardP1, BoardP2, Mask, ThreatStats).
