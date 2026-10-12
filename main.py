"""
Entry point: initialization of SWI-Prolog runtime (Janus) and Pygame GUI.
"""

import sys
import os

# Import of the Python-Prolog bridge (Janus)
try:
    import janus_swi as janus
except ImportError:
    try:
        import janus  # type: ignore
    except ImportError:
        print("[ERRORE CRITICO] Il modulo 'janus-swi' non e' installato o non e' reperibile.")
        print("Esegui: pip install janus-swi")
        sys.exit(1)

from gui import ConnectFourGUI


class PrologEngineWrapper:
    """Interface to the SWI-Prolog engine via Janus."""

    def __init__(self, prolog_file="engine.pl"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        prolog_path = os.path.join(base_dir, prolog_file).replace("\\", "/")
        print(f"[*] Caricamento motore logico SWI-Prolog: {prolog_path}")
        try:
            janus.consult(prolog_path)
            print("[+] Modulo engine.pl caricato con successo in Janus!")
        except Exception as e:
            print(f"[!] Errore durante il caricamento di {prolog_path}: {e}")
            sys.exit(1)

    def init_game(self, difficulty='m'):
        """Create a new game state at the specified difficulty level."""
        query_str = f"engine:init_game({difficulty}, State)"
        res = janus.query_once(query_str)
        if not res or 'State' not in res:
            raise RuntimeError("Impossibile inizializzare lo stato della partita.")
        return res['State']

    def play_move(self, col, state_in):
        """Execute a move in the selected column (1..9)."""
        res = janus.query_once("engine:play_move(Col, S_in, S_out)", {
            'Col': int(col),
            'S_in': state_in
        })
        if not res or 'S_out' not in res:
            raise RuntimeError(f"Mossa fallita in colonna {col}")
        return res['S_out']

    def get_ai_move(self, state_in):
        """Request the move computed by the AI and related statistics."""
        res = janus.query_once("engine:get_ai_move(S_in, BestCol, Info)", {
            'S_in': state_in
        })
        if not res or 'BestCol' not in res:
            raise RuntimeError("Calcolo mossa IA fallito.")
        return int(res['BestCol']), res.get('Info', {})

    def set_difficulty(self, difficulty, state_in):
        """Update AI difficulty level (e, m, h, x)."""
        res = janus.query_once(f"engine:set_difficulty({difficulty}, S_in, S_out)", {
            'S_in': state_in
        })
        if res and 'S_out' in res:
            return res['S_out']
        return state_in


def main():
    print("=" * 70)
    print("  FORZA QUATTRO - SABOTATORE")
    print("  Candigliota Michele & Gismondi Alexander")
    print("=" * 70)

    engine = PrologEngineWrapper("engine.pl")
    app = ConnectFourGUI(engine)
    app.run()


if __name__ == "__main__":
    main()
