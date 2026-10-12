:- module(ai, [
    ai_move/6,
    ai_move/7,
    ai_move/8,
    set_ai_difficulty/1,
    get_ai_difficulty/1,
    difficulty_depth/2,
    next_turn/2,
    is_max_node/1,
    is_min_node/1,
    tromp_order/1
]).

:- use_module(bitboard).
:- use_module(threats).
:- use_module(library(random)).

% AI Decision Engine: Paranoid Minimax with Alpha-Beta Pruning, Table of transpositions,
% dynamic ordering, and quiescence search.
% AI turns (phases 2 and 4) = MAX nodes; human turns (phases 1 and 3) = MIN nodes.

:- dynamic current_ai_difficulty/1.
:- dynamic tt_entry/8.


% DIFFICULTY AND DEPTH CONFIGURATION
current_ai_difficulty(m).

difficulty_depth(e, 3).
difficulty_depth(m, 4).
difficulty_depth(h, 5).
difficulty_depth(x, 6).

set_ai_difficulty(Level) :-
    must_be(atom, Level),
    member(Level, [e, m, h, x]),
    retractall(current_ai_difficulty(_)),
    asserta(current_ai_difficulty(Level)).

get_ai_difficulty(Level) :-
    ( current_ai_difficulty(Level) -> true ; Level = m ).

% Tromp's static ordering: priority from the center towards the edges
tromp_order([5, 4, 6, 3, 7, 2, 8, 1, 9]).


% SHIFT CYCLE (R-G-G-R SEQUENCE) AND NODE CLASSIFICATION
next_turn(turn(1, 1, human, 1),        turn(2, saboteur, ai, 2)).
next_turn(turn(2, saboteur, ai, 2),   turn(3, 2, human, 2)).
next_turn(turn(3, 2, human, 2),        turn(4, saboteur, ai, 1)).
next_turn(turn(4, saboteur, ai, 1),   turn(1, 1, human, 1)).

is_max_node(turn(2, _, ai, _)).
is_max_node(turn(4, _, ai, _)).

is_min_node(turn(1, _, human, _)).
is_min_node(turn(3, _, human, _)).


% AI MOVE CALCULATION (COORDINATION AND TELEMETRY)
ai_move(BoardP1, BoardP2, Mask, Turn, BestCol, InfoDict) :-
    get_ai_difficulty(Level),
    difficulty_depth(Level, Depth),
    ai_move(BoardP1, BoardP2, Mask, Turn, Level, Depth, BestCol, InfoDict).

ai_move(BoardP1, BoardP2, Mask, Turn, Depth, BestCol, InfoDict) :-
    get_ai_difficulty(Level),
    ai_move(BoardP1, BoardP2, Mask, Turn, Level, Depth, BestCol, InfoDict).

ai_move(BoardP1, BoardP2, Mask, Turn, Level, Depth, BestCol, InfoDict) :-
    must_be(atom, Level),
    memberchk(Level, [e, m, h, x]),
    must_be(integer, Depth),
    Depth > 0,
    get_time(T0),
    nb_setval(ai_node_count, 0),
    nb_setval(ai_tt_hits, 0),
    nb_setval(ai_q_node_count, 0),
    reset_transposition_table,
    valid_moves(Mask, Moves),
    Moves \= [],

    Turn = turn(_Phase, saboteur, ai, CurrentPiece),
    next_turn(Turn, NextTurn),
    NextTurn = turn(_NextPhase, _NextPid, human, NextHumanPiece),

    % Forced block filter: blocks opponent's immediate-win threats.
    OppPiece is 3 - CurrentPiece,
    ( OppPiece == 1 -> OppBoard = BoardP1 ; OppBoard = BoardP2 ),
    winning_moves(OppBoard, Mask, ImmediateHumanWins),
    intersect_lists(Moves, ImmediateHumanWins, BlockMoves),

    select_move(Level, BoardP1, BoardP2, Mask, Turn, NextHumanPiece, Depth,
                Moves, BlockMoves, BestCol, BestScore),

    get_time(T1),
    TimeMs is round((T1 - T0) * 1000),
    nb_getval(ai_node_count, NodeCount),
    nb_getval(ai_tt_hits, TTHits),
    nb_getval(ai_q_node_count, QuiescenceNodes),

    drop_piece(BoardP1, BoardP2, Mask, BestCol, CurrentPiece,
               PostB1, PostB2, PostM, _),
    board_threat_stats(PostB1, PostB2, PostM, NextTurn, ThreatStats),
    reset_transposition_table,

    InfoDict = info{
        score: BestScore,
        nodes: NodeCount,
        tt_hits: TTHits,
        quiescence_nodes: QuiescenceNodes,
        time_ms: TimeMs,
        depth: Depth,
        difficulty: Level,
        threats: ThreatStats
    }.


% MOVE SELECTION BY DIFFICULTY LEVEL

% Hard ('h') and Extreme ('x'): deterministic choice (iterative deepening)
select_move(Level, BoardP1, BoardP2, Mask, Turn, NextHumanPiece, Depth,
            Moves, BlockMoves, BestCol, BestScore) :-
    ( Level == h ; Level == x ),
    !,
    Turn = turn(_, _, _, Piece),
    ( BlockMoves \= [] ->
        suicide_moves(BoardP1, BoardP2, Mask, Piece, Suicides),
        exclude_lists(BlockMoves, Suicides, SafeBlocks),
        ( SafeBlocks = [] -> Candidates = BlockMoves ; Candidates = SafeBlocks ),
        iterative_best_move(Candidates, BoardP1, BoardP2, Mask, Turn, Depth,
                            BestScore, BestCol)
    ;   safe_moves(Moves, BoardP1, BoardP2, Mask, Piece, NextHumanPiece, SafeCand),
        ( SafeCand = [] ->
            Moves = [BestCol|_], BestScore = 0
        ;   iterative_best_move(SafeCand, BoardP1, BoardP2, Mask, Turn, Depth,
                                BestScore, BestCol)
        )
    ).

% Medium ('m'): deterministic forced block or random choice among the top 3
select_move(m, BoardP1, BoardP2, Mask, Turn, NextHumanPiece, Depth,
            Moves, BlockMoves, BestCol, BestScore) :-
    Turn = turn(_, _, _, Piece),
    ( BlockMoves \= [] ->
        suicide_moves(BoardP1, BoardP2, Mask, Piece, Suicides),
        exclude_lists(BlockMoves, Suicides, SafeBlocks),
        ( SafeBlocks = [] -> Candidates = BlockMoves ; Candidates = SafeBlocks ),
        rank_moves(Candidates, BoardP1, BoardP2, Mask, Turn, Depth, Ranked),
        Ranked = [(BestScore, BestCol)|_]
    ;   safe_moves(Moves, BoardP1, BoardP2, Mask, Piece, NextHumanPiece, SafeCand),
        rank_moves(SafeCand, BoardP1, BoardP2, Mask, Turn, Depth, Ranked),
        ( Ranked = [] ->
            Moves = [BestCol|_], BestScore = 0
        ;   take_n(3, Ranked, Top3),
            random_member((BestScore, BestCol), Top3)
        )
    ).

% Easy ('e'): random pool from the top 5 (including any forced blocks)
select_move(e, BoardP1, BoardP2, Mask, Turn, _NextHumanPiece, Depth,
            Moves, BlockMoves, BestCol, BestScore) :-
    rank_moves(Moves, BoardP1, BoardP2, Mask, Turn, Depth, Ranked),
    ( Ranked = [] ->
        Moves = [BestCol|_], BestScore = 0
    ;   take_n(5, Ranked, Top5),
        findall((Score, Col),
            ( member(Col, BlockMoves), member((Score, Col), Ranked) ),
            ForcedPairs),
        append(ForcedPairs, Top5, Combined),
        list_to_set(Combined, Pool),
        random_member((BestScore, BestCol), Pool)
    ).


% EVALUATION AND ORDERING OF MOVES AT THE ROOT
rank_moves(Moves, BoardP1, BoardP2, Mask, Turn, Depth, RankedDesc) :-
    order_moves_dynamic(Moves, BoardP1, BoardP2, Mask, Turn, OrderedMoves),
    Turn = turn(_, _, _, Piece),
    next_turn(Turn, NextTurn),
    D1 is Depth - 1,
    findall(NegScore-(Score, Col),
        ( member(Col, OrderedMoves),
          inc_node_count,
          drop_piece(BoardP1, BoardP2, Mask, Col, Piece, NB1, NB2, NM, MoveBit),
          ( Piece == 1 -> CheckB = NB1 ; CheckB = NB2 ),
          ( win_after_drop(CheckB, MoveBit) ->
              Score is -100000 - Depth
          ; board_full(NM) ->
              Score = 100000
          ;   paranoid_ab(NB1, NB2, NM, NextTurn, D1, -1000000, 1000000, Score)
          ),
          NegScore is -Score
        ),
        Pairs),
    keysort(Pairs, SortedPairs),
    findall((Score, Col), member(_-(Score, Col), SortedPairs), RankedDesc).


% ITERATIVE DEEPENING AND ROOT SEARCH
iterative_best_move(Moves, BoardP1, BoardP2, Mask, Turn, MaxDepth,
                    BestScore, BestCol) :-
    iterative_best_loop(1, MaxDepth, Moves, BoardP1, BoardP2, Mask, Turn,
                        none, 0, BestCol, BestScore).

iterative_best_loop(Depth, MaxDepth, Moves, BoardP1, BoardP2, Mask, Turn,
                    Preferred, _PreviousScore, BestCol, BestScore) :-
    order_moves_dynamic(Moves, BoardP1, BoardP2, Mask, Turn, DynamicOrder),
    prefer_move(Preferred, DynamicOrder, Ordered),
    root_best_search(Ordered, BoardP1, BoardP2, Mask, Turn, Depth,
                     -1000000, none, IterScore, IterCol),
    ( Depth >= MaxDepth ->
        BestCol = IterCol,
        BestScore = IterScore
    ;   NextDepth is Depth + 1,
        iterative_best_loop(NextDepth, MaxDepth, Moves,
                            BoardP1, BoardP2, Mask, Turn,
                            IterCol, IterScore, BestCol, BestScore)
    ).

prefer_move(none, Moves, Moves) :- !.
prefer_move(Preferred, Moves, [Preferred|Rest]) :-
    select(Preferred, Moves, Rest),
    !.
prefer_move(_Preferred, Moves, Moves).

root_best_search([], _B1, _B2, _Mask, _Turn, _Depth,
                 BestScore, BestCol, BestScore, BestCol).
root_best_search([Col|Rest], BoardP1, BoardP2, Mask, Turn, Depth,
                 CurrentBest, CurrentCol, BestScore, BestCol) :-
    Turn = turn(_, _, _, Piece),
    inc_node_count,
    drop_piece(BoardP1, BoardP2, Mask, Col, Piece, NB1, NB2, NM, MoveBit),
    next_turn(Turn, NextTurn),
    ( Piece == 1 -> CheckB = NB1 ; CheckB = NB2 ),
    ( win_after_drop(CheckB, MoveBit) ->
        Score is -100000 - Depth
    ; board_full(NM) ->
        Score = 100000
    ; ChildDepth is Depth - 1,
      paranoid_ab(NB1, NB2, NM, NextTurn, ChildDepth,
                  CurrentBest, 1000000, Score)
    ),
    ( Score > CurrentBest ->
        NextBest = Score,
        NextCol = Col
    ;   NextBest = CurrentBest,
        NextCol = CurrentCol
    ),
    root_best_search(Rest, BoardP1, BoardP2, Mask, Turn, Depth,
                     NextBest, NextCol, BestScore, BestCol).

% Static center-priority ordering (John Tromp)
order_moves_tromp(Moves, Ordered) :-
    tromp_order(Order),
    findall(C, (member(C, Order), member(C, Moves)), CenterMoves),
    findall(C, (member(C, Moves), \+ member(C, CenterMoves)), Rest),
    append(CenterMoves, Rest, Ordered).

% Dynamic ordering: prioritized terminal nodes and central heuristic
order_moves_dynamic(Moves, BoardP1, BoardP2, Mask, Turn, Ordered) :-
    findall(Key-Col,
        ( member(Col, Moves),
          move_order_key(BoardP1, BoardP2, Mask, Turn, Col, Key)
        ),
        KeyedMoves),
    keysort(KeyedMoves, Sorted),
    findall(Col, member(_-Col, Sorted), Ordered).

move_order_key(BoardP1, BoardP2, Mask, Turn, Col, Key) :-
    Turn = turn(_, _, _, Piece),
    drop_piece(BoardP1, BoardP2, Mask, Col, Piece,
               NextB1, NextB2, NextMask, MoveBit),
    ( Piece == 1 -> NextBoard = NextB1 ; NextBoard = NextB2 ),
    ( win_after_drop(NextBoard, MoveBit) -> Terminal = win
    ; board_full(NextMask) -> Terminal = full
    ; Terminal = quiet
    ),
    terminal_priority(Turn, Terminal, Priority),
    tromp_order(Order),
    nth1(CenterRank, Order, Col),
    Key is Priority * 10 + CenterRank.

terminal_priority(Turn, win, 0) :- is_min_node(Turn), !.
terminal_priority(Turn, full, 0) :- is_max_node(Turn), !.
terminal_priority(_Turn, quiet, 1) :- !.
terminal_priority(Turn, win, 2) :- is_max_node(Turn), !.
terminal_priority(Turn, full, 2) :- is_min_node(Turn), !.

% Telemetry meters
inc_node_count :-
    ( nb_current(ai_node_count, NC) ->
        NC1 is NC + 1,
        nb_setval(ai_node_count, NC1)
    ; nb_setval(ai_node_count, 1)
    ).

inc_tt_hit :-
    ( nb_current(ai_tt_hits, Hits) ->
        NextHits is Hits + 1,
        nb_setval(ai_tt_hits, NextHits)
    ; nb_setval(ai_tt_hits, 1)
    ).

inc_quiescence_node :-
    ( nb_current(ai_q_node_count, Count) ->
        NextCount is Count + 1,
        nb_setval(ai_q_node_count, NextCount)
    ; nb_setval(ai_q_node_count, 1)
    ).

% TRANSPOSITION TABLE (THREAD-SAFE)
reset_transposition_table :-
    thread_self(Thread),
    retractall(tt_entry(Thread, _, _, _, _, _, _, _)).

tt_lookup(BoardP1, BoardP2, Mask, Turn, Depth, Alpha, Beta,
          SearchAlpha, SearchBeta, Result) :-
    thread_self(Thread),
    Turn = turn(Phase, _, _, _),
    ( tt_entry(Thread, BoardP1, BoardP2, Mask, Phase, Depth, Flag, StoredValue) ->
        inc_tt_hit,
        apply_tt_entry(Flag, StoredValue, Alpha, Beta,
                       SearchAlpha, SearchBeta, Result)
    ;   SearchAlpha = Alpha,
        SearchBeta = Beta,
        Result = search
    ).

apply_tt_entry(exact, Value, Alpha, Beta, Alpha, Beta, value(Value)) :- !.
apply_tt_entry(lower, Value, Alpha, Beta, SearchAlpha, Beta, Result) :-
    !,
    SearchAlpha is max(Alpha, Value),
    ( SearchAlpha >= Beta -> Result = value(Value) ; Result = search ).
apply_tt_entry(upper, Value, Alpha, Beta, Alpha, SearchBeta, Result) :-
    SearchBeta is min(Beta, Value),
    ( SearchBeta =< Alpha -> Result = value(Value) ; Result = search ).

tt_store(BoardP1, BoardP2, Mask, Turn, Depth, Alpha, Beta, Value) :-
    ( Value =< Alpha -> Flag = upper
    ; Value >= Beta -> Flag = lower
    ; Flag = exact
    ),
    thread_self(Thread),
    Turn = turn(Phase, _, _, _),
    retractall(tt_entry(Thread, BoardP1, BoardP2, Mask, Phase, Depth, _, _)),
    assertz(tt_entry(Thread, BoardP1, BoardP2, Mask, Phase, Depth, Flag, Value)).

% PARANOID MINIMAX WITH ALPHA-BETA PRUNING
paranoid_ab(BoardP1, BoardP2, Mask, Turn, Depth, Alpha, Beta, Value) :-
    tt_lookup(BoardP1, BoardP2, Mask, Turn, Depth, Alpha, Beta,
              SearchAlpha, SearchBeta, Result),
    ( Result = value(CachedValue) ->
        inc_node_count,
        Value = CachedValue
    ;   paranoid_ab_uncached(BoardP1, BoardP2, Mask, Turn, Depth,
                            SearchAlpha, SearchBeta, ComputedValue),
        tt_store(BoardP1, BoardP2, Mask, Turn, Depth,
                 SearchAlpha, SearchBeta, ComputedValue),
        Value = ComputedValue
    ).

% Depth 0: tactical scope regarding immediate threats
paranoid_ab_uncached(BoardP1, BoardP2, Mask, Turn, 0, Alpha, Beta, Value) :-
    !,
    quiescence(BoardP1, BoardP2, Mask, Turn, 2, Alpha, Beta, Value).

% MAX Node (Saboteur Turn, phases 2 and 4)
paranoid_ab_uncached(BoardP1, BoardP2, Mask, Turn, Depth, Alpha, Beta, Value) :-
    is_max_node(Turn),
    !,
    inc_node_count,
    valid_moves(Mask, Moves),
    ( Moves == [] ->
        Value = 100000
    ;   order_moves_dynamic(Moves, BoardP1, BoardP2, Mask, Turn, Ordered),
        max_search(Ordered, BoardP1, BoardP2, Mask, Turn, Depth,
                   Alpha, Beta, -1000000, Value)
    ).

% MIN Node (Human Turn, phases 1 and 3 - Paranoid Coalition)
paranoid_ab_uncached(BoardP1, BoardP2, Mask, Turn, Depth, Alpha, Beta, Value) :-
    is_min_node(Turn),
    !,
    inc_node_count,
    valid_moves(Mask, Moves),
    ( Moves == [] ->
        Value = 100000
    ;   order_moves_dynamic(Moves, BoardP1, BoardP2, Mask, Turn, Ordered),
        min_search(Ordered, BoardP1, BoardP2, Mask, Turn, Depth,
                   Alpha, Beta, 1000000, Value)
    ).


% SEARCH FOR QUIESCENCE (TACTICAL EXTENSION BEYOND THE HORIZON)
quiescence(BoardP1, BoardP2, Mask, Turn, 0, _Alpha, _Beta, Value) :-
    !,
    inc_node_count,
    inc_quiescence_node,
    evaluate_saboteur(BoardP1, BoardP2, Mask, Turn, Value).
quiescence(BoardP1, BoardP2, Mask, Turn, Budget, Alpha, Beta, Value) :-
    inc_node_count,
    inc_quiescence_node,
    valid_moves(Mask, Moves),
    ( Moves == [] ->
        Value = 100000
    ; forcing_moves(BoardP1, BoardP2, Mask, Turn, Moves, ForcingMoves),
      ( ForcingMoves == [] ->
          evaluate_saboteur(BoardP1, BoardP2, Mask, Turn, Value)
      ; order_moves_dynamic(ForcingMoves, BoardP1, BoardP2, Mask, Turn, Ordered),
        ( is_max_node(Turn) ->
            qmax_search(Ordered, BoardP1, BoardP2, Mask, Turn, Budget,
                        Alpha, Beta, -1000000, Value)
        ;   qmin_search(Ordered, BoardP1, BoardP2, Mask, Turn, Budget,
                        Alpha, Beta, 1000000, Value)
        )
      )
    ).

% Identify forced moves (immediate wins, blocks, or mandatory moves).
forcing_moves(BoardP1, BoardP2, Mask, Turn, Moves, ForcingMoves) :-
    Turn = turn(_, _, _, Piece),
    ( is_min_node(Turn) ->
        ( Piece == 1 -> CurrentBoard = BoardP1 ; CurrentBoard = BoardP2 ),
        winning_moves(CurrentBoard, Mask, Wins),
        intersect_lists(Moves, Wins, ForcingMoves)
    ; is_max_node(Turn) ->
        OppPiece is 3 - Piece,
        ( OppPiece == 1 -> OppBoard = BoardP1 ; OppBoard = BoardP2 ),
        winning_moves(OppBoard, Mask, OppWins),
        intersect_lists(Moves, OppWins, Blocks),
        ( Blocks \= [] ->
            ForcingMoves = Blocks
        ; suicide_moves(BoardP1, BoardP2, Mask, Piece, Suicides),
          exclude_lists(Moves, Suicides, SafeMoves),
          ( SafeMoves == [], Moves \= [] -> ForcingMoves = Moves
          ; ForcingMoves = []
          )
        )
    ).


% QUIESCENCE EXPLORATION (Q-MAX AND Q-MIN)
qmax_search([], _B1, _B2, _M, _Turn, _Budget, _Alpha, _Beta, Current, Current).
qmax_search([Col|Rest], BoardP1, BoardP2, Mask, Turn, Budget,
            Alpha, Beta, CurrentMax, BestVal) :-
    Turn = turn(_, _, _, Piece),
    drop_piece(BoardP1, BoardP2, Mask, Col, Piece, NB1, NB2, NM, MoveBit),
    next_turn(Turn, NextTurn),
    ( Piece == 1 -> CheckB = NB1 ; CheckB = NB2 ),
    ( win_after_drop(CheckB, MoveBit) ->
        ChildVal is -100000 - Budget
    ; board_full(NM) ->
        ChildVal = 100000
    ; NextBudget is Budget - 1,
      quiescence(NB1, NB2, NM, NextTurn, NextBudget, Alpha, Beta, ChildVal)
    ),
    NewMax is max(CurrentMax, ChildVal),
    NewAlpha is max(Alpha, NewMax),
    ( NewAlpha >= Beta -> BestVal = NewMax
    ; qmax_search(Rest, BoardP1, BoardP2, Mask, Turn, Budget,
                  NewAlpha, Beta, NewMax, BestVal)
    ).

qmin_search([], _B1, _B2, _M, _Turn, _Budget, _Alpha, _Beta, Current, Current).
qmin_search([Col|Rest], BoardP1, BoardP2, Mask, Turn, Budget,
            Alpha, Beta, CurrentMin, BestVal) :-
    Turn = turn(_, _, _, Piece),
    drop_piece(BoardP1, BoardP2, Mask, Col, Piece, NB1, NB2, NM, MoveBit),
    next_turn(Turn, NextTurn),
    ( Piece == 1 -> CheckB = NB1 ; CheckB = NB2 ),
    ( win_after_drop(CheckB, MoveBit) ->
        ChildVal is -100000 - Budget
    ; board_full(NM) ->
        ChildVal = 100000
    ; NextBudget is Budget - 1,
      quiescence(NB1, NB2, NM, NextTurn, NextBudget, Alpha, Beta, ChildVal)
    ),
    NewMin is min(CurrentMin, ChildVal),
    NewBeta is min(Beta, NewMin),
    ( NewBeta =< Alpha -> BestVal = NewMin
    ; qmin_search(Rest, BoardP1, BoardP2, Mask, Turn, Budget,
                  Alpha, NewBeta, NewMin, BestVal)
    ).


% EXPLORATION OF MAX NODES WITH BETA PRUNING
max_search([], _B1, _B2, _M, _Turn, _Depth, _Alpha, _Beta, CurrentMax, CurrentMax).
max_search([Col|Rest], BoardP1, BoardP2, Mask, Turn, Depth, Alpha, Beta, CurrentMax, BestVal) :-
    Turn = turn(_, _, _, Piece),
    drop_piece(BoardP1, BoardP2, Mask, Col, Piece, NB1, NB2, NM, MoveBit),
    next_turn(Turn, NextTurn),
    ( Piece == 1 -> CheckB = NB1 ; CheckB = NB2 ),
    ( win_after_drop(CheckB, MoveBit) ->
        ChildVal is -100000 - Depth
    ; board_full(NM) ->
        ChildVal = 100000
    ; D1 is Depth - 1,
      paranoid_ab(NB1, NB2, NM, NextTurn, D1, Alpha, Beta, ChildVal)
    ),
    NewMax is max(CurrentMax, ChildVal),
    NewAlpha is max(Alpha, NewMax),
    ( NewAlpha >= Beta ->
        BestVal = NewMax
    ; max_search(Rest, BoardP1, BoardP2, Mask, Turn, Depth, NewAlpha, Beta, NewMax, BestVal)
    ).


%  MIN NODE EXPLORATION WITH ALPHA PRUNING
min_search([], _B1, _B2, _M, _Turn, _Depth, _Alpha, _Beta, CurrentMin, CurrentMin).
min_search([Col|Rest], BoardP1, BoardP2, Mask, Turn, Depth, Alpha, Beta, CurrentMin, BestVal) :-
    Turn = turn(_, _, _, Piece),
    drop_piece(BoardP1, BoardP2, Mask, Col, Piece, NB1, NB2, NM, MoveBit),
    next_turn(Turn, NextTurn),
    ( Piece == 1 -> CheckB = NB1 ; CheckB = NB2 ),
    ( win_after_drop(CheckB, MoveBit) ->
        ChildVal is -100000 - Depth
    ; board_full(NM) ->
        ChildVal = 100000
    ; D1 is Depth - 1,
      paranoid_ab(NB1, NB2, NM, NextTurn, D1, Alpha, Beta, ChildVal)
    ),
    NewMin is min(CurrentMin, ChildVal),
    NewBeta is min(Beta, NewMin),
    ( NewBeta =< Alpha ->
        BestVal = NewMin
    ; min_search(Rest, BoardP1, BoardP2, Mask, Turn, Depth, Alpha, NewBeta, NewMin, BestVal)
    ).


% AUXILIARY FUNCTIONS FOR LISTS
take_n(N, List, Prefix) :-
    ( N =< 0 -> Prefix = []
    ; length(List, L),
      M is min(N, L),
      length(Prefix, M),
      append(Prefix, _, List)
    ).

intersect_lists([], _, []).
intersect_lists([X|Xs], Ys, [X|Rest]) :-
    memberchk(X, Ys), !,
    intersect_lists(Xs, Ys, Rest).
intersect_lists([_|Xs], Ys, Rest) :-
    intersect_lists(Xs, Ys, Rest).

exclude_lists([], _, []).
exclude_lists([X|Xs], Bad, Ys) :-
    ( memberchk(X, Bad) ->
        exclude_lists(Xs, Bad, Ys)
    ;   Ys = [X|Rest],
        exclude_lists(Xs, Bad, Rest)
    ).
