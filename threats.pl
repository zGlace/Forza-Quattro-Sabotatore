:- module(threats, [
    init_threat_windows/0,
    evaluate_saboteur/5,
    board_threat_stats/5,
    winning_moves/3,
    suicide_moves/5,
    setup_moves/6,
    safe_moves/7,
    is_directly_playable/2,
    center_column_weights/1
]).

:- use_module(bitboard).

% Heuristic based on Threat-Space Analysis (Victor Allis):
% Analysis of 153 4-cell tuples; detection of direct/delayed threats, forks, and support checks.

:- dynamic cached_window/5.

:- initialization(init_threat_windows).

% Weights for column control (priority given to central column 5)
center_column_weights([
    1-0, 2-1, 3-2, 4-3, 5-4, 6-3, 7-2, 8-1, 9-0
]).


% PRE-CALCULATION OF WINNING WINDOWS (4-CELL TUPLES)
init_threat_windows :-
    retractall(cached_window(_, _, _, _, _)),
    findall(w(Mask, B1, B2, B3, B4, Dir),
        generate_window(Mask, B1, B2, B3, B4, Dir),
        Windows),
    forall(
        nth1(Id, Windows, w(Mask, B1, B2, B3, B4, Dir)),
        assertz(cached_window(Id, Mask, [B1, B2, B3, B4], Dir, B1))
    ).

% generation of 4-cell tuples in the 4 directions (horizontal, vertical, diagonal /, diagonal \)
generate_window(Mask, B1, B2, B3, B4, horizontal) :-
    between(0, 7, R),
    between(1, 6, C),
    C1 is C, C2 is C + 1, C3 is C + 2, C4 is C + 3,
    coord_to_bit(R, C1, B1), coord_to_bit(R, C2, B2),
    coord_to_bit(R, C3, B3), coord_to_bit(R, C4, B4),
    Mask is (1 << B1) \/ (1 << B2) \/ (1 << B3) \/ (1 << B4).

generate_window(Mask, B1, B2, B3, B4, vertical) :-
    between(1, 9, C),
    between(0, 4, R),
    R1 is R, R2 is R + 1, R3 is R + 2, R4 is R + 3,
    coord_to_bit(R1, C, B1), coord_to_bit(R2, C, B2),
    coord_to_bit(R3, C, B3), coord_to_bit(R4, C, B4),
    Mask is (1 << B1) \/ (1 << B2) \/ (1 << B3) \/ (1 << B4).

generate_window(Mask, B1, B2, B3, B4, diag_asc) :-
    between(0, 4, R),
    between(1, 6, C),
    R1 is R,     C1 is C,
    R2 is R + 1, C2 is C + 1,
    R3 is R + 2, C3 is C + 2,
    R4 is R + 3, C4 is C + 3,
    coord_to_bit(R1, C1, B1), coord_to_bit(R2, C2, B2),
    coord_to_bit(R3, C3, B3), coord_to_bit(R4, C4, B4),
    Mask is (1 << B1) \/ (1 << B2) \/ (1 << B3) \/ (1 << B4).

generate_window(Mask, B1, B2, B3, B4, diag_desc) :-
    between(3, 7, R),
    between(1, 6, C),
    R1 is R,     C1 is C,
    R2 is R - 1, C2 is C + 1,
    R3 is R - 2, C3 is C + 2,
    R4 is R - 3, C4 is C + 3,
    coord_to_bit(R1, C1, B1), coord_to_bit(R2, C2, B2),
    coord_to_bit(R3, C3, B3), coord_to_bit(R4, C4, B4),
    Mask is (1 << B1) \/ (1 << B2) \/ (1 << B3) \/ (1 << B4).

% verifies if a cell is immediately playable (at the bottom or with support present)
is_directly_playable(BitIndex, Mask) :-
    Row is BitIndex mod 9,
    ( Row =:= 0 ->
        true
    ;   BelowBit is BitIndex - 1,
        (Mask /\ (1 << BelowBit)) =\= 0
    ).


% SCANNING AND CLASSIFICATION OF THE 153 TUPLES
scan_all_windows(BoardP1, BoardP2, Mask,
                 Blocked, DirP1, DirP2, DelP1, DelP2, Open2P1, Open2P2) :-
    findall(WinMask, cached_window(_, WinMask, _, _, _), Windows),
    scan_loop(Windows, BoardP1, BoardP2, Mask,
              0, 0, 0, 0, 0, 0, 0,
              Blocked, DirP1, DirP2, DelP1, DelP2, Open2P1, Open2P2).

scan_loop([], _B1, _B2, _M,
          Blk, D1, D2, Del1, Del2, Op1, Op2,
          Blk, D1, D2, Del1, Del2, Op1, Op2).
scan_loop([WinMask|Rest], BoardP1, BoardP2, Mask,
          AccBlk, AccD1, AccD2, AccDel1, AccDel2, AccOp1, AccOp2,
          Blk, D1, D2, Del1, Del2, Op1, Op2) :-
    N1 is popcount(BoardP1 /\ WinMask),
    N2 is popcount(BoardP2 /\ WinMask),
    ( N1 > 0, N2 > 0 ->
        % Locked tuple (contains pieces from both players)
        NewBlk is AccBlk + 1,
        NewD1 = AccD1, NewD2 = AccD2,
        NewDel1 = AccDel1, NewDel2 = AccDel2,
        NewOp1 = AccOp1, NewOp2 = AccOp2
    ; N1 == 3, N2 == 0 ->
        % Threat P1 (direct or delayed)
        NewBlk = AccBlk,
        MissingMask is WinMask xor (BoardP1 /\ WinMask),
        MissingBit is msb(MissingMask),
        ( is_directly_playable(MissingBit, Mask) ->
            NewD1 is AccD1 + 1, NewDel1 = AccDel1
        ;   NewD1 = AccD1, NewDel1 is AccDel1 + 1
        ),
        NewD2 = AccD2, NewDel2 = AccDel2,
        NewOp1 = AccOp1, NewOp2 = AccOp2
    ; N2 == 3, N1 == 0 ->
        % Threat P2 (direct or delayed)
        NewBlk = AccBlk,
        MissingMask is WinMask xor (BoardP2 /\ WinMask),
        MissingBit is msb(MissingMask),
        ( is_directly_playable(MissingBit, Mask) ->
            NewD2 is AccD2 + 1, NewDel2 = AccDel2
        ;   NewD2 = AccD2, NewDel2 is AccDel2 + 1
        ),
        NewD1 = AccD1, NewDel1 = AccDel1,
        NewOp1 = AccOp1, NewOp2 = AccOp2
    ; N1 == 2, N2 == 0 ->
        % Open window for P1
        NewBlk = AccBlk,
        NewD1 = AccD1, NewD2 = AccD2,
        NewDel1 = AccDel1, NewDel2 = AccDel2,
        NewOp1 is AccOp1 + 1, NewOp2 = AccOp2
    ; N2 == 2, N1 == 0 ->
        % Open window for P2
        NewBlk = AccBlk,
        NewD1 = AccD1, NewD2 = AccD2,
        NewDel1 = AccDel1, NewDel2 = AccDel2,
        NewOp1 = AccOp1, NewOp2 is AccOp2 + 1
    ;   NewBlk = AccBlk,
        NewD1 = AccD1, NewD2 = AccD2,
        NewDel1 = AccDel1, NewDel2 = AccDel2,
        NewOp1 = AccOp1, NewOp2 = AccOp2
    ),
    scan_loop(Rest, BoardP1, BoardP2, Mask,
              NewBlk, NewD1, NewD2, NewDel1, NewDel2, NewOp1, NewOp2,
              Blk, D1, D2, Del1, Del2, Op1, Op2).


% DETAILED ANALYSIS OF DELAYED THREATS, SUPPORTS, AND FORKS

% Extract unique completions, vertical distance, and necessary supports
color_threat_features(Board, OtherBoard, Mask,
                      UniqueDirect, UniqueDelayed, SupportUrgency, LinkedSupports,
                      Delayed) :-
    findall(Threat,
        ( cached_window(_, WinMask, _, _, _),
          N is popcount(Board /\ WinMask),
          N =:= 3,
          (OtherBoard /\ WinMask) =:= 0,
          MissingMask is WinMask xor (Board /\ WinMask),
          MissingBit is msb(MissingMask),
          ( is_directly_playable(MissingBit, Mask) ->
              Threat = direct(MissingBit)
          ; support_info(MissingBit, Mask, Distance, SupportMask),
            Threat = delayed(MissingBit, Distance, SupportMask)
          )
        ),
        Threats),
    findall(Bit, member(direct(Bit), Threats), DirectBits0),
    sort(DirectBits0, DirectBits),
    length(DirectBits, UniqueDirect),
    findall(delayed(Bit, Distance, SupportMask),
            member(delayed(Bit, Distance, SupportMask), Threats),
            Delayed0),
    sort(Delayed0, Delayed),
    length(Delayed, UniqueDelayed),
    support_urgency(Delayed, SupportUrgency),
    linked_support_pairs(Delayed, LinkedSupports).

% Calculates distance from bottom/top and mask of necessary support cells
support_info(BitIndex, Mask, Distance, SupportMask) :-
    bit_to_coord(BitIndex, Row, Col),
    column_mask(Col, ColumnMask),
    Height is popcount(Mask /\ ColumnMask),
    Distance is Row - Height,
    Distance > 0,
    support_mask(Height, Row, Col, 0, SupportMask).

support_mask(CurrentRow, TargetRow, _Col, Acc, Acc) :-
    CurrentRow >= TargetRow,
    !.
support_mask(CurrentRow, TargetRow, Col, Acc, SupportMask) :-
    Bit is (Col - 1) * 9 + CurrentRow,
    NextAcc is Acc \/ (1 << Bit),
    NextRow is CurrentRow + 1,
    support_mask(NextRow, TargetRow, Col, NextAcc, SupportMask).

% Weighs the urgency of delayed threats (higher if closer to the top of the column)
support_urgency([], 0).
support_urgency([delayed(_, Distance, _)|Rest], Urgency) :-
    support_urgency(Rest, TailUrgency),
    CurrentUrgency is max(1, 8 - Distance),
    Urgency is CurrentUrgency + TailUrgency.

% Counts pairs of delayed threats that share support cells
linked_support_pairs([], 0).
linked_support_pairs([delayed(Bit, _, SupportMask)|Rest], Count) :-
    findall(1,
        ( member(delayed(OtherBit, _, OtherSupportMask), Rest),
          Bit =\= OtherBit,
          (SupportMask /\ OtherSupportMask) =\= 0
        ),
        Links),
    length(Links, Here),
    linked_support_pairs(Rest, Tail),
    Count is Here + Tail.

pair_count(N, Count) :-
    ( N >= 2 -> Count is (N * (N - 1)) // 2 ; Count = 0 ).

% Detects moves that transform two open windows into two distinct completions (forks)
fork_setup_count(Board, OtherBoard, Mask, Count) :-
    findall(CandidateBit-CompletionBit,
        ( cached_window(_, WinMask, _, _, _),
          N is popcount(Board /\ WinMask),
          N =:= 2,
          (OtherBoard /\ WinMask) =:= 0,
          EmptyMask is WinMask xor (Board /\ WinMask),
          FirstBit is lsb(EmptyMask),
          FirstMask is 1 << FirstBit,
          SecondMask is EmptyMask xor FirstMask,
          SecondBit is msb(SecondMask),
          ( CandidateBit = FirstBit, CompletionBit = SecondBit
          ; CandidateBit = SecondBit, CompletionBit = FirstBit
          ),
          is_directly_playable(CandidateBit, Mask),
          CandidateMask is 1 << CandidateBit,
          \+ win_after_drop(Board, CandidateMask),
          NextMask is Mask \/ CandidateMask,
          is_directly_playable(CompletionBit, NextMask)
        ),
        SetupPairs0),
    sort(SetupPairs0, SetupPairs),
    findall(CandidateBit,
        ( member(CandidateBit-_, SetupPairs),
          findall(CompletionBit,
                  member(CandidateBit-CompletionBit, SetupPairs),
                  CompletionBits0),
          sort(CompletionBits0, CompletionBits),
          length(CompletionBits, CompletionCount),
          CompletionCount >= 2
        ),
        ForkBits0),
    sort(ForkBits0, ForkBits),
    length(ForkBits, Count).

% Aggregates threat space features for both players
threat_space_features(BoardP1, BoardP2, Mask, Features) :-
    color_threat_features(BoardP1, BoardP2, Mask,
                          UniqueDirectP1, UniqueDelayedP1, SupportUrgencyP1, LinkedP1,
                          DelayedP1),
    color_threat_features(BoardP2, BoardP1, Mask,
                          UniqueDirectP2, UniqueDelayedP2, SupportUrgencyP2, LinkedP2,
                          DelayedP2),
    pair_count(UniqueDirectP1, DoublePairsP1),
    pair_count(UniqueDirectP2, DoublePairsP2),
    fork_setup_count(BoardP1, BoardP2, Mask, ForkMovesP1),
    fork_setup_count(BoardP2, BoardP1, Mask, ForkMovesP2),
    Features = threat_features{
        unique_direct_p1: UniqueDirectP1,
        unique_direct_p2: UniqueDirectP2,
        unique_delayed_p1: UniqueDelayedP1,
        unique_delayed_p2: UniqueDelayedP2,
        double_threat_pairs_p1: DoublePairsP1,
        double_threat_pairs_p2: DoublePairsP2,
        fork_setup_moves_p1: ForkMovesP1,
        fork_setup_moves_p2: ForkMovesP2,
        support_urgency_p1: SupportUrgencyP1,
        support_urgency_p2: SupportUrgencyP2,
        linked_supports_p1: LinkedP1,
        linked_supports_p2: LinkedP2,
        delayed_details_p1: DelayedP1,
        delayed_details_p2: DelayedP2
    }.

% Urgency multiplier based on the temporal proximity of the player's phase
phase_urgency_multiplier(none, _HumanPhase, 2, -1) :- !.
phase_urgency_multiplier(turn(CurrentPhase, _, _, _), HumanPhase, Multiplier, Distance) :-
    Distance is (HumanPhase - CurrentPhase + 4) mod 4,
    Multiplier is 4 - Distance.

% Verifies if filling the column would place the final cell exactly in the human phase
phase_controlled_delayed(_Delayed, none, _HumanPhase, 0, 0) :- !.
phase_controlled_delayed([], _Turn, _HumanPhase, 0, 0).
phase_controlled_delayed([delayed(_, Distance, _)|Rest],
                         turn(CurrentPhase, _, _, _), HumanPhase,
                         Count, Urgency) :-
    LandingPhase is ((CurrentPhase - 1 + Distance) mod 4) + 1,
    phase_controlled_delayed(Rest, turn(CurrentPhase, _, _, _), HumanPhase,
                             TailCount, TailUrgency),
    ( LandingPhase =:= HumanPhase ->
        CurrentUrgency is max(1, 8 - Distance),
        Count is TailCount + 1,
        Urgency is TailUrgency + CurrentUrgency
    ;   Count = TailCount,
        Urgency = TailUrgency
    ).


% EURISTIC EVALUATION FOR THE SABOTEUR
evaluate_saboteur(BoardP1, BoardP2, Mask, Turn, Score) :-
    scan_all_windows(BoardP1, BoardP2, Mask,
                     Blocked, DirP1, DirP2, DelP1, DelP2, Open2P1, Open2P2),
    eval_center(BoardP1, BoardP2, CenterP1, CenterP2),
    threat_space_features(BoardP1, BoardP2, Mask, Features),
    phase_urgency_multiplier(Turn, 1, DirectMultiplierP1, _TurnsToP1),
    phase_urgency_multiplier(Turn, 3, DirectMultiplierP2, _TurnsToP2),
    phase_controlled_delayed(Features.delayed_details_p1, Turn, 1,
                             _ControlledDelayedP1, ControlledUrgencyP1),
    phase_controlled_delayed(Features.delayed_details_p2, Turn, 3,
                             _ControlledDelayedP2, ControlledUrgencyP2),

    % weights for the linear combination of threats
    BlockedTuplesWeight   = 35,
    DirectThreatWeight    = 425,
    DelayedThreatWeight   = 140,
    OpenTuplesWeight      = 25,
    DoubleThreatWeight    = 1250,
    ForkSetupWeight       = 350,
    SupportUrgencyWeight  = 35,
    LinkedSupportWeight   = 120,
    PhaseControlWeight    = 90,
    MaxHumanThreatWeight  = 50,
    CenterControlWeight   = 10,

    BlockedScore is Blocked * BlockedTuplesWeight,
    DirectPenalty is ((DirP1 * DirectMultiplierP1) +
                      (DirP2 * DirectMultiplierP2)) * DirectThreatWeight,
    DelayedPenalty is (DelP1 + DelP2) * DelayedThreatWeight,
    Open2Penalty is (Open2P1 + Open2P2) * OpenTuplesWeight,
    DoublePenalty is ((Features.double_threat_pairs_p1 * DirectMultiplierP1) +
                      (Features.double_threat_pairs_p2 * DirectMultiplierP2)) * DoubleThreatWeight,
    ForkPenalty is ((Features.fork_setup_moves_p1 * DirectMultiplierP1) +
                    (Features.fork_setup_moves_p2 * DirectMultiplierP2)) * ForkSetupWeight,
    SupportPenalty is (Features.support_urgency_p1 +
                       Features.support_urgency_p2) * SupportUrgencyWeight,
    LinkedPenalty is (Features.linked_supports_p1 +
                      Features.linked_supports_p2) * LinkedSupportWeight,
    PhaseControlPenalty is (ControlledUrgencyP1 + ControlledUrgencyP2) * PhaseControlWeight,

    ThreatP1 is (DirP1 * DirectMultiplierP1) + DelP1 + Open2P1,
    ThreatP2 is (DirP2 * DirectMultiplierP2) + DelP2 + Open2P2,
    MaxHumanThreat is max(ThreatP1, ThreatP2) * MaxHumanThreatWeight,
    CenterHumanPenalty is (CenterP1 + CenterP2) * CenterControlWeight,

    RawScore is BlockedScore - DirectPenalty - DelayedPenalty - Open2Penalty -
                DoublePenalty - ForkPenalty - SupportPenalty - LinkedPenalty -
                PhaseControlPenalty - MaxHumanThreat - CenterHumanPenalty,
    Score is max(-90000, min(90000, RawScore)).

% Control of pieces on the central columns
eval_center(BoardP1, BoardP2, CenterP1, CenterP2) :-
    center_column_weights(CWs),
    eval_center_loop(CWs, BoardP1, BoardP2, 0, 0, CenterP1, CenterP2).

eval_center_loop([], _B1, _B2, CP1, CP2, CP1, CP2).
eval_center_loop([Col-Weight|Rest], BoardP1, BoardP2, Acc1, Acc2, CP1, CP2) :-
    column_mask(Col, CMask),
    Count1 is popcount(BoardP1 /\ CMask),
    Count2 is popcount(BoardP2 /\ CMask),
    NewAcc1 is Acc1 + (Count1 * Weight),
    NewAcc2 is Acc2 + (Count2 * Weight),
    eval_center_loop(Rest, BoardP1, BoardP2, NewAcc1, NewAcc2, CP1, CP2).


% STATISTICS OF THREAT-SPACE FOR USER INTERFACE AND TELEMETRY 
board_threat_stats(BoardP1, BoardP2, Mask, Turn, Stats) :-
    scan_all_windows(BoardP1, BoardP2, Mask,
                     Blocked, DirP1, DirP2, DelP1, DelP2, Open2P1, Open2P2),
    threat_space_features(BoardP1, BoardP2, Mask, Features),
    phase_urgency_multiplier(Turn, 1, DirectMultiplierP1, TurnsToP1),
    phase_urgency_multiplier(Turn, 3, DirectMultiplierP2, TurnsToP2),
    phase_controlled_delayed(Features.delayed_details_p1, Turn, 1,
                             ControlledDelayedP1, ControlledUrgencyP1),
    phase_controlled_delayed(Features.delayed_details_p2, Turn, 3,
                             ControlledDelayedP2, ControlledUrgencyP2),
    Stats = stats{
        blocked_tuples: Blocked,
        direct_threats_p1: DirP1,
        direct_threats_p2: DirP2,
        delayed_threats_p1: DelP1,
        delayed_threats_p2: DelP2,
        open_2_p1: Open2P1,
        open_2_p2: Open2P2,
        unique_direct_p1: Features.unique_direct_p1,
        unique_direct_p2: Features.unique_direct_p2,
        unique_delayed_p1: Features.unique_delayed_p1,
        unique_delayed_p2: Features.unique_delayed_p2,
        double_threat_pairs_p1: Features.double_threat_pairs_p1,
        double_threat_pairs_p2: Features.double_threat_pairs_p2,
        fork_setup_moves_p1: Features.fork_setup_moves_p1,
        fork_setup_moves_p2: Features.fork_setup_moves_p2,
        support_urgency_p1: Features.support_urgency_p1,
        support_urgency_p2: Features.support_urgency_p2,
        linked_supports_p1: Features.linked_supports_p1,
        linked_supports_p2: Features.linked_supports_p2,
        turns_until_p1: TurnsToP1,
        turns_until_p2: TurnsToP2,
        direct_multiplier_p1: DirectMultiplierP1,
        direct_multiplier_p2: DirectMultiplierP2,
        phase_controlled_delayed_p1: ControlledDelayedP1,
        phase_controlled_delayed_p2: ControlledDelayedP2,
        phase_controlled_urgency_p1: ControlledUrgencyP1,
        phase_controlled_urgency_p2: ControlledUrgencyP2
    }.


% RECOGNITION OF WINNING MOVES, SUICIDE AND SETUP MOVES 

% Moves that immediately create a line of four
winning_moves(Board, Mask, WinCols) :-
    valid_moves(Mask, Moves),
    findall(Col,
        ( member(Col, Moves),
          can_play(Mask, Col),
          Bottom is 1 << ((Col - 1) * 9),
          NewMask is Mask \/ (Mask + Bottom),
          MoveBit is NewMask xor Mask,
          win_after_drop(Board, MoveBit)
        ),
        WinCols).

% Suicide moves: immediately grant a win to the opponent
suicide_moves(BoardP1, _BoardP2, Mask, 1, SuicideCols) :-
    winning_moves(BoardP1, Mask, SuicideCols).
suicide_moves(_BoardP1, BoardP2, Mask, 2, SuicideCols) :-
    winning_moves(BoardP2, Mask, SuicideCols).

% Setup moves: create a winning support for the opponent in the cell above
setup_moves(BoardP1, BoardP2, Mask, CurrentPiece, OppPiece, SetupCols) :-
    valid_moves(Mask, Moves),
    findall(Col,
        ( member(Col, Moves),
          drop_piece(BoardP1, BoardP2, Mask, Col, CurrentPiece,
                     NextB1, NextB2, _NextMask, MoveBit),
          BitIndex is msb(MoveBit),
          Row is BitIndex mod 9,
          Row < 7,
          ( OppPiece == 1 -> OppBoard = NextB1 ; OppBoard = NextB2 ),
          AboveBit is BitIndex + 1,
          win_after_drop(OppBoard, 1 << AboveBit)
        ),
        SetupCols).

% Filter suicide and setup moves from the candidate moves
safe_moves(Moves, BoardP1, BoardP2, Mask, CurrentPiece, OppPiece, SafeMoves) :-
    suicide_moves(BoardP1, BoardP2, Mask, CurrentPiece, Suicides),
    setup_moves(BoardP1, BoardP2, Mask, CurrentPiece, OppPiece, Setups),
    append(Suicides, Setups, BadMoves),
    list_to_set(BadMoves, UniqueBad),
    exclude_members(Moves, UniqueBad, Filtered),
    ( Filtered = [] ->
        exclude_members(Moves, Suicides, NonSuicide),
        ( NonSuicide = [] -> SafeMoves = Moves ; SafeMoves = NonSuicide )
    ;   SafeMoves = Filtered
    ).

exclude_members([], _Bad, []).
exclude_members([X|Xs], Bad, Ys) :-
    ( memberchk(X, Bad) ->
        exclude_members(Xs, Bad, Ys)
    ;   Ys = [X|Rest],
        exclude_members(Xs, Bad, Rest)
    ).
