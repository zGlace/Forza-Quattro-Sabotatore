"""
Automated test suite: 81-bit bitboard verification, Allis windows,
shift cycle, and Minimax decision engine.
"""

import sys
import os
import time

try:
    import janus_swi as janus
except ImportError:
    try:
        import janus  # type: ignore
    except ImportError:
        print("[ERRORE] Libreria janus-swi non trovata.")
        sys.exit(1)


def run_tests():
    print("=" * 70)
    print("  SUITE DI TEST AUTOMATIZZATA - FORZA 4 SABOTATORE")
    print("=" * 70)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    prolog_path = os.path.join(base_dir, "engine.pl").replace("\\", "/")

    print(f"[*] Caricamento engine SWI-Prolog: {prolog_path}")
    janus.consult(prolog_path)
    print("[+] Engine caricato con successo.\n")

    passed: int = 0
    total: int = 0

    def assert_test(name, condition, extra=""):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  [PASS] {name} {extra}")
        else:
            print(f"  [FAIL] {name} {extra}")


    # TESTS 1–7: BITBOARD, O(1) ALIGNMENTS, AND SENTINEL BITS
    res = janus.query_once("bitboard:rows(R), bitboard:cols(C), bitboard:total_cells(T)")
    assert_test("Dimensioni Scacchiera", res['R'] == 8 and res['C'] == 9 and res['T'] == 72,
                f"(Righe: {res['R']}, Colonne: {res['C']}, Totale: {res['T']})")

    res_w = janus.query_once("aggregate_all(count, threats:cached_window(_, _, _, _, _), WCount)")
    assert_test("Finestre Vincenti di Allis", res_w['WCount'] == 153,
                f"({res_w['WCount']} finestre precalcolate: 48H, 45V, 30D/, 30D\\)")

    q_vert = ("bitboard:empty_board(B0, _, M0), "
              "bitboard:drop_piece(B0, 0, M0, 1, 1, B1, _, M1, _), "
              "bitboard:drop_piece(B1, 0, M1, 1, 1, B2, _, M2, _), "
              "bitboard:drop_piece(B2, 0, M2, 1, 1, B3, _, M3, _), "
              "bitboard:drop_piece(B3, 0, M3, 1, 1, B4, _, _, _), "
              "bitboard:check_win(B4)")
    res_vert = janus.query_once(q_vert)
    assert_test("Vittoria Verticale in O(1)", res_vert is not None and len(res_vert) > 0)

    q_horiz = ("bitboard:empty_board(B0, _, M0), "
               "bitboard:drop_piece(B0, 0, M0, 1, 1, B1, _, M1, _), "
               "bitboard:drop_piece(B1, 0, M1, 2, 1, B2, _, M2, _), "
               "bitboard:drop_piece(B2, 0, M2, 3, 1, B3, _, M3, _), "
               "bitboard:drop_piece(B3, 0, M3, 4, 1, B4, _, _, _), "
               "bitboard:check_win(B4)")
    res_horiz = janus.query_once(q_horiz)
    assert_test("Vittoria Orizzontale in O(1)", res_horiz is not None and len(res_horiz) > 0)

    q_diag_asc = ("bitboard:empty_board(B0, _, M0), "
                  "bitboard:drop_piece(B0, 0, M0, 1, 1, B1, _, M1, _), "
                  "bitboard:drop_piece(B1, 0, M1, 2, 2, B2, _, M2, _), "
                  "bitboard:drop_piece(B2, 0, M2, 2, 1, B3, _, M3, _), "
                  "bitboard:drop_piece(B3, 0, M3, 3, 2, B4, _, M4, _), "
                  "bitboard:drop_piece(B4, 0, M4, 3, 2, B5, _, M5, _), "
                  "bitboard:drop_piece(B5, 0, M5, 3, 1, B6, _, M6, _), "
                  "bitboard:drop_piece(B6, 0, M6, 4, 2, B7, _, M7, _), "
                  "bitboard:drop_piece(B7, 0, M7, 4, 2, B8, _, M8, _), "
                  "bitboard:drop_piece(B8, 0, M8, 4, 2, B9, _, M9, _), "
                  "bitboard:drop_piece(B9, 0, M9, 4, 1, B10, _, _, _), "
                  "bitboard:check_win(B10)")
    res_diag_asc = janus.query_once(q_diag_asc)
    assert_test("Vittoria Diagonale Ascendente (/) in O(1)", res_diag_asc is not None and len(res_diag_asc) > 0)

    q_sentinel = ("bitboard:coord_to_bit(7, 1, BitTop1), "
                  "bitboard:coord_to_bit(0, 2, BitBot2), "
                  "Board is (1 << BitTop1) \\/ (1 << BitBot2), "
                  "(\\+ bitboard:check_win(Board))")
    res_sentinel = janus.query_once(q_sentinel)
    assert_test("Isolamento Sentinella a 9-bit", res_sentinel is not None and len(res_sentinel) > 0,
                "(nessun falso wrap-around orizzontale/diagonale)")

    q_fill = ("bitboard:column_mask(1, M8), "
              "(\\+ bitboard:can_play(M8, 1))")
    res_fill = janus.query_once(q_fill)
    assert_test("Saturazione Colonna a 8 Pedine", res_fill is not None and len(res_fill) > 0,
                "(9ª mossa correttamente rifiutata)")


    # TESTS 8–9: GAME INITIALIZATION AND 4-PHASE CYCLE (R-G-G-R)
    state0 = janus.query_once("engine:init_game(m, S)")['S']
    matrix = state0['matrix']
    assert_test("Inizializzazione Stato & Matrice 8x9",
                len(matrix) == 8 and len(matrix[0]) == 9 and state0['status'] == 'ongoing',
                f"({len(matrix)} righe x {len(matrix[0])} colonne)")

    s1 = janus.query_once("engine:play_move(5, S_in, S_out)", {'S_in': state0})['S_out']
    phase2_ok = (s1['phase'] == 2 and s1['player_kind'] == 'ai' and s1['piece'] == 2)
    s2 = janus.query_once("engine:play_move(5, S_in, S_out)", {'S_in': s1})['S_out']
    phase3_ok = (s2['phase'] == 3 and s2['player_kind'] == 'human' and s2['piece'] == 2)
    s3 = janus.query_once("engine:play_move(6, S_in, S_out)", {'S_in': s2})['S_out']
    phase4_ok = (s3['phase'] == 4 and s3['player_kind'] == 'ai' and s3['piece'] == 1)
    s4 = janus.query_once("engine:play_move(6, S_in, S_out)", {'S_in': s3})['S_out']
    phase1_ok = (s4['phase'] == 1 and s4['player_kind'] == 'human' and s4['piece'] == 1)
    assert_test("Ciclo Turni a 4 Fasi (R-G-G-R)",
                phase2_ok and phase3_ok and phase4_ok and phase1_ok,
                f"(F1:P1-R -> F2:IA-G -> F3:P2-G -> F4:IA-R -> F1:P1-R)")


    # TESTS 10–12: AI MOVE AND FORCED BLOCK FILTERING
    t0 = time.time()
    res_ai = janus.query_once("engine:get_ai_move(S_in, BestCol, Info)", {'S_in': s1})
    elapsed_ms = round((time.time() - t0) * 1000)
    best_col = res_ai['BestCol']
    info = res_ai['Info']
    assert_test("Calcolo Mossa IA Sabotatore (Fase 2, Giallo)",
                1 <= best_col <= 9 and info['nodes'] > 0,
                f"(Scelta: Col {best_col}, Nodi: {info['nodes']}, Tempo: {elapsed_ms} ms)")

    # state with immediate threat of P1 in column 3
    q_threat_p1 = ("bitboard:empty_board(B1_0, B2, M0), "
                   "bitboard:drop_piece(B1_0, B2, M0, 3, 1, B1_1, _, M1, _), "
                   "bitboard:drop_piece(B1_1, B2, M1, 3, 1, B1_2, _, M2, _), "
                   "bitboard:drop_piece(B1_2, B2, M2, 3, 1, B1_3, _, M3, _), "
                   "threats:winning_moves(B1_3, M3, WinsP1)")
    wins_p1 = janus.query_once(q_threat_p1)['WinsP1']
    s_block_p1 = {
        'board_p1': janus.query_once(q_threat_p1)['B1_3'],
        'board_p2': 0,
        'mask': janus.query_once(q_threat_p1)['M3'],
        'phase': 2,
        'player_id': 0,
        'player_kind': 'ai',
        'piece': 2,
        'moves': 3,
        'difficulty': 'h',
        'status': 'ongoing',
        'winner': 0
    }
    ai_block_p1 = janus.query_once("engine:get_ai_move(S, Col, _)", {'S': s_block_p1})['Col']
    assert_test("Filtro Mosse Forzate Fase 2 (IA Giallo blocca Rosso)",
                wins_p1 == [3] and ai_block_p1 == 3,
                f"(Minaccia P1 col: {wins_p1}, Mossa IA: Col {ai_block_p1})")

    # state with immediate threat of P2 in column 7
    q_threat_p2 = ("bitboard:empty_board(B1, B2_0, M0), "
                   "bitboard:drop_piece(B1, B2_0, M0, 7, 2, _, B2_1, M1, _), "
                   "bitboard:drop_piece(B1, B2_1, M1, 7, 2, _, B2_2, M2, _), "
                   "bitboard:drop_piece(B1, B2_2, M2, 7, 2, _, B2_3, M3, _), "
                   "threats:winning_moves(B2_3, M3, WinsP2)")
    wins_p2 = janus.query_once(q_threat_p2)['WinsP2']
    s_block_p2 = {
        'board_p1': 0,
        'board_p2': janus.query_once(q_threat_p2)['B2_3'],
        'mask': janus.query_once(q_threat_p2)['M3'],
        'phase': 4,
        'player_id': 0,
        'player_kind': 'ai',
        'piece': 1,
        'moves': 3,
        'difficulty': 'h',
        'status': 'ongoing',
        'winner': 0
    }
    ai_block_p2 = janus.query_once("engine:get_ai_move(S, Col, _)", {'S': s_block_p2})['Col']
    assert_test("Filtro Mosse Forzate Fase 4 (IA Rosso blocca Giallo)",
                wins_p2 == [7] and ai_block_p2 == 7,
                f"(Minaccia P2 col: {wins_p2}, Mossa IA: Col {ai_block_p2})")


    # TESTS 13-16: THREAR-SPACE THREAT HEURISTIC (DOUBLE THREATS, FOLKS, AND TEMPORAL CONTROL)
    q_double = ("bitboard:empty_board(B0, B2, M0), "
                "bitboard:drop_piece(B0, B2, M0, 2, 1, B1, _, M1, _), "
                "bitboard:drop_piece(B1, B2, M1, 3, 1, B3, _, M3, _), "
                "bitboard:drop_piece(B3, B2, M3, 4, 1, B4, _, M4, _), "
                "threats:board_threat_stats(B4, B2, M4, Stats)")
    double_stats = janus.query_once(q_double)['Stats']
    assert_test("Riconoscimento Doppia Minaccia P1",
                double_stats['unique_direct_p1'] == 2 and
                double_stats['double_threat_pairs_p1'] == 1,
                f"(completamenti: {double_stats['unique_direct_p1']}, "
                f"coppie: {double_stats['double_threat_pairs_p1']})")

    q_fork = ("bitboard:empty_board(B0, B2, M0), "
              "bitboard:drop_piece(B0, B2, M0, 2, 1, B2a, _, M2, _), "
              "bitboard:drop_piece(B2a, B2, M2, 4, 1, B4, _, M4, _), "
              "threats:board_threat_stats(B4, B2, M4, Stats)")
    fork_stats = janus.query_once(q_fork)['Stats']
    assert_test("Riconoscimento Mossa Fork P1",
                fork_stats['fork_setup_moves_p1'] >= 1,
                f"({fork_stats['fork_setup_moves_p1']} mosse fork rilevate)")

    q_phase_direct = ("bitboard:empty_board(B0, B2, M0), "
                      "bitboard:drop_piece(B0, B2, M0, 2, 1, B1, _, M1, _), "
                      "bitboard:drop_piece(B1, B2, M1, 3, 1, B3, _, M3, _), "
                      "bitboard:drop_piece(B3, B2, M3, 4, 1, B4, _, M4, _), "
                      "threats:evaluate_saboteur(B4, B2, M4, turn(1,1,human,1), ScoreNow), "
                      "threats:evaluate_saboteur(B4, B2, M4, turn(2,saboteur,ai,2), ScoreLater)")
    phase_direct = janus.query_once(q_phase_direct)
    assert_test("Urgenza Minaccia Dipendente dalla Fase",
                phase_direct['ScoreNow'] < phase_direct['ScoreLater'],
                f"(fase P1: {phase_direct['ScoreNow']}, fase IA-G: {phase_direct['ScoreLater']})")

    q_phase_delayed = ("bitboard:empty_board(R0, Y0, M0), "
                       "bitboard:drop_piece(R0, Y0, M0, 2, 2, R1, Y1, M1, _), "
                       "bitboard:drop_piece(R1, Y1, M1, 2, 1, R2, Y2, M2, _), "
                       "bitboard:drop_piece(R2, Y2, M2, 3, 1, R3, Y3, M3, _), "
                       "bitboard:drop_piece(R3, Y3, M3, 3, 1, R4, Y4, M4, _), "
                       "bitboard:drop_piece(R4, Y4, M4, 4, 2, R5, Y5, M5, _), "
                       "bitboard:drop_piece(R5, Y5, M5, 4, 1, R6, Y6, M6, _), "
                       "threats:board_threat_stats(R6, Y6, M6, turn(4,saboteur,ai,1), StatsF4), "
                       "threats:board_threat_stats(R6, Y6, M6, turn(1,1,human,1), StatsF1), "
                       "threats:evaluate_saboteur(R6, Y6, M6, turn(4,saboteur,ai,1), ScoreF4), "
                       "threats:evaluate_saboteur(R6, Y6, M6, turn(1,1,human,1), ScoreF1)")
    phase_delayed = janus.query_once(q_phase_delayed)
    controlled_f4 = phase_delayed['StatsF4']['phase_controlled_delayed_p1']
    controlled_f1 = phase_delayed['StatsF1']['phase_controlled_delayed_p1']
    assert_test("Controllo Temporale Minacce Sospese R-G-G-R",
                controlled_f4 > controlled_f1 and
                phase_delayed['ScoreF4'] < phase_delayed['ScoreF1'],
                f"(controllate F4/F1: {controlled_f4}/{controlled_f1}, "
                f"score: {phase_delayed['ScoreF4']}/{phase_delayed['ScoreF1']})")


    # TESTS 17-20: MINIMAX SEARCH, TRANSPOSITIONS, AND TACTICAL EXTENSIONS 
    janus.query_once("ai:set_ai_difficulty(x)")
    state_easy = dict(s1)
    state_easy['difficulty'] = 'e'
    state_difficulty_result = janus.query_once(
        "engine:get_ai_move(S, Col, Info)", {'S': state_easy})
    global_level = janus.query_once("ai:get_ai_difficulty(Level)")['Level']
    state_info = state_difficulty_result['Info']
    assert_test("Difficoltà Isolata nello Stato",
                global_level == 'x' and
                state_info['difficulty'] == 'e' and
                state_info['depth'] == 3,
                f"(globale: {global_level}, stato: {state_info['difficulty']}, "
                f"profondità: {state_info['depth']})")

    assert_test("Trasposizioni ed Estensioni Tattiche Attive",
                info['tt_hits'] > 0 and info['quiescence_nodes'] > 0,
                f"(TT hit: {info['tt_hits']}, quiescenza: {info['quiescence_nodes']})")

    q_horizon = ("bitboard:empty_board(B0, B2, M0), "
                 "bitboard:drop_piece(B0, B2, M0, 2, 1, B1, _, M1, _), "
                 "bitboard:drop_piece(B1, B2, M1, 3, 1, B3, _, M3, _), "
                 "bitboard:drop_piece(B3, B2, M3, 4, 1, B4, _, M4, _), "
                 "ai:reset_transposition_table, "
                 "ai:paranoid_ab(B4, B2, M4, turn(1,1,human,1), "
                 "0, -1000000, 1000000, Value)")
    horizon_value = janus.query_once(q_horizon)['Value']
    assert_test("Estensione Oltre l'Orizzonte",
                horizon_value < -100000,
                f"(valore terminale esteso: {horizon_value})")

    q_ordering = ("bitboard:empty_board(B0, B2, M0), "
                  "bitboard:drop_piece(B0, B2, M0, 2, 1, B1, _, M1, _), "
                  "bitboard:drop_piece(B1, B2, M1, 3, 1, B3, _, M3, _), "
                  "bitboard:drop_piece(B3, B2, M3, 4, 1, B4, _, M4, _), "
                  "bitboard:valid_moves(M4, Moves), "
                  "ai:order_moves_dynamic(Moves, B4, B2, M4, "
                  "turn(1,1,human,1), Ordered)")
    ordered_moves = janus.query_once(q_ordering)['Ordered']
    assert_test("Ordinamento Dinamico Mosse Terminali",
                ordered_moves[0] in (1, 5),
                f"(ordine: {ordered_moves})")

    print("\n" + "=" * 70)
    perc = round(passed / total * 100) if total > 0 else 0
    print(f"  RISULTATO TEST: {passed} / {total} superati con successo ({perc}%)")
    print("=" * 70)

    return passed == total


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
