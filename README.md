# Forza Quattro - Sabotatore / Connect Four - Saboteur

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![SWI-Prolog](https://img.shields.io/badge/SWI--Prolog-9.0%2B-red.svg)](https://www.swi-prolog.org/)
[![Pygame](https://img.shields.io/badge/Pygame-2.5%2B-green.svg)](https://www.pygame.org/)
[![Janus](https://img.shields.io/badge/Bridge-Janus--SWI-orange.svg)](https://github.com/SWI-Prolog/packages-swipy)

---

## English

A modern, strategic variant of **Connect Four** featuring an 8×9 board and an adversarial **Saboteur AI**. 
The project combines a high-performance **SWI-Prolog** logic and search engine with an interactive **Python / Pygame** graphical user interface, connected seamlessly via the **Janus** C-level bridge.

### Key Features

- **Expanded 8×9 Grid**: 8 rows and 9 columns (72 cells total) for deeper tactical gameplay compared to classic 6×7 Connect Four.
- **Unique "Saboteur" Turn Mechanics**: A 4-phase turn cycle where the AI acts as an unpredictable third party, playing on both sides to disrupt players.
- **81-Bit Bitboard Engine (John Tromp Method)**: High-speed bitwise operations in SWI-Prolog for $O(1)$ alignment checks, gravity drops, and win verification.
- **Threat-Space Analysis (Victor Allis Heuristic)**: Evaluation of 153 pre-computed 4-cell windows to detect direct threats, delayed threats, support dependencies, and forks.
- **Paranoid Minimax with Alpha-Beta Pruning**: Includes transposition tables, static/dynamic move ordering, and quiescence search.
- **Polished Pygame GUI (1260×830)**: Modern dark UI, smooth piece drop animations, column hover ghosts, live threat telemetry, and interactive modals.
- **Comprehensive Automated Test Suite**: Built-in verification for bitboard operations, threat detectors, state transitions, and AI decision quality.

---

### Game Rules & The Saboteur Mechanic

Instead of standard alternating turns, the game follows an asymmetric **4-phase cycle (`Red - Yellow - Yellow - Red`)**:

| Phase | Player | Role | Piece Color |
| :---: | :---: | :---: | :---: |
| **1** | Player 1 (Human) | Regular Move | **Red** |
| **2** | Saboteur (AI) | Sabotage / Defense | **Yellow** |
| **3** | Player 2 (Human) | Regular Move | **Yellow** |
| **4** | Saboteur (AI) | Sabotage / Defense | **Red** |

The **Saboteur AI** plays using the color of the *next* human opponent:
- In Phase 2, the AI drops a **Yellow** piece to block Player 1 or advance Player 2's position.
- In Phase 4, the AI drops a **Red** piece to block Player 2 or advance Player 1's position.
- The first entity to connect **4 consecutive pieces** of their color (horizontally, vertically, or diagonally) wins the game.

---

### Architecture & Technical Implementation

```
┌──────────────────────────────────────────────┐
│             Pygame GUI (gui.py)              │
│       Rendering, Animations, Dashboard       │
└──────────────────────┬───────────────────────┘
                       │ Janus (C-Bridge)
┌──────────────────────▼───────────────────────┐
│          SWI-Prolog Core (engine.pl)         │
│ ┌──────────────────┬───────────────────────┐ │
│ │ bitboard.pl      │ threats.pl            │ │
│ │ 81-bit bitboards │ Allis Threat Analysis │ │
│ └──────────────────┼───────────────────────┘ │
│ │ ai.pl                                    │ │
│ │ Paranoid Minimax + Alpha-Beta + TT       │ │
│ └──────────────────────────────────────────┘ │
└──────────────────────────────────────────────┘
```

1. **Bitboard Representation (`bitboard.pl`)**:
   - Each player's board and the occupancy mask are stored as 81-bit integers (9 columns × 9 bits: 8 playable rows + 1 sentinel bit).
   - Fast win detection using directional bit shifts:
     - Vertical: `>> 1`
     - Horizontal: `>> 9`
     - Diagonal `/`: `>> 10`
     - Diagonal `\`: `>> 8`
2. **Threat-Space Evaluation (`threats.pl`)**:
   - 153 pre-compiled 4-cell winning tuples.
   - Evaluates direct wins, unplayable/delayed threats, parity control, and central column preference (`Col 5`).
3. **AI Search Engine (`ai.pl`)**:
   - **Paranoid Minimax**: AI turns (phases 2 and 4) are MAX nodes; human turns (phases 1 and 3) are MIN nodes.
   - **Alpha-Beta Pruning & Transposition Table**: Dynamic caching of analyzed positions and heuristic evaluations.
   - **Difficulty Presets**:
     - **Easy (`e`)**: Depth 3
     - **Medium (`m`)**: Depth 4 *(Default)*
     - **Hard (`h`)**: Depth 5
     - **Expert (`x`)**: Depth 6

---

### Prerequisites & Installation

#### 1. System Requirements
- **Python 3.10+**
- **SWI-Prolog 9.0+** (ensure SWI-Prolog is added to your system `PATH`)

#### 2. Install Python Dependencies
```bash
pip install pygame janus-swi
```

> **Note for Windows users**: Ensure that SWI-Prolog architecture (x64) matches your Python installation (x64).

---

### Running the Project

#### Start the Game:
```bash
python main.py
```

#### Run Automated Test Suite:
```bash
python test_system.py
```

---

### Project Structure

```
.
├── main.py          # Entry point & Janus Prolog wrapper
├── gui.py           # Pygame 1260x830 graphical interface
├── engine.pl        # Top-level Prolog engine & state transitions
├── ai.pl            # Minimax search, alpha-beta, transposition table
├── bitboard.pl      # 81-bit bitboard logic, shifts, and win checks
├── threats.pl       # Victor Allis threat-space analysis heuristic
└── test_system.py   # Automated verification suite
```

---
---

## Italiano

Una variante moderna e strategica di **Forza Quattro** su una griglia espansa **8×9**, caratterizzata dalla presenza di una **IA Sabotatore**.
Il progetto integra un motore logico e decisionale in **SWI-Prolog** con un'interfaccia grafica interattiva in **Python / Pygame**, comunicando a livello nativo tramite la libreria **Janus**.

### Caratteristiche Principali

- **Griglia Espansa 8×9**: 8 righe e 9 colonne (72 celle complessive) per una profondità tattica superiore al classico Forza 4 (6×7).
- **Meccanica a 4 Fasi del "Sabotatore"**: Ciclo a quattro turni in cui l'IA agisce da terzo incomodo, giocando con entrambi i colori per scombinare i piani dei giocatori umani.
- **Rappresentazione a Bitboard a 81-bit (Metodo John Tromp)**: Operazioni bitwise in SWI-Prolog ad alte prestazioni con controlli di allineamento, caduta per gravità e vittoria in $O(1)$.
- **Analisi dello Spazio delle Minacce (Euristica di Victor Allis)**: 153 tuple/finestre di 4 celle precalcolate per individuare minacce dirette, ritardate, forchette e dipendenze di supporto.
- **Minimax Paranoico con Potatura Alpha-Beta**: Include tabelle di trasposizione, ordinamento dinamico delle mosse e quiescence search.
- **Interfaccia Grafica Pygame (1260×830 px)**: Tema dark moderno, animazioni fluide di caduta delle pedine, preview semitrasparente (ghost piece), telemetria delle minacce in tempo reale e modali interattive.
- **Suite di Test Automatizzata**: Script di verifica integrato per testare bitboard, rilevamento minacce, transizioni di stato ed euristiche IA.

---

### Regole del Gioco e Ciclo del Sabotatore

La partita non si svolge con un'alternanza binaria, bensì con un **ciclo asimmetrico a 4 fasi (`Rosso - Giallo - Giallo - Rosso`)**:

| Fase | Giocatore | Tipo di Mossa | Colore Pedina |
| :---: | :---: | :---: | :---: |
| **1** | Giocatore 1 (Umano) | Mossa regolare | **Rosso** |
| **2** | Sabotatore (IA) | Sabotaggio / Difesa | **Giallo** |
| **3** | Giocatore 2 (Umano) | Mossa regolare | **Giallo** |
| **4** | Sabotatore (IA) | Sabotaggio / Difesa | **Rosso** |

Il **Sabotatore** interviene utilizzando la pedina dell'avversario successivo:
- Nella Fase 2, gioca una pedina **Gialla** per bloccare il Giocatore 1 o favorire il Giocatore 2.
- Nella Fase 4, gioca una pedina **Rossa** per bloccare il Giocatore 2 o favorire il Giocatore 1.
- Il primo partecipante che allinea **4 pedine consecutive** del proprio colore (in orizzontale, verticale o diagonale) si aggiudica la vittoria.

---

### Architettura e Dettagli Tecnici

```
┌──────────────────────────────────────────────┐
│             Pygame GUI (gui.py)              │
│      Rendering, Animazioni, Dashboard        │
└──────────────────────┬───────────────────────┘
                       │ Janus (Bridge C-level)
┌──────────────────────▼───────────────────────┐
│         Motore SWI-Prolog (engine.pl)        │
│ ┌──────────────────┬───────────────────────┐ │
│ │ bitboard.pl      │ threats.pl            │ │
│ │ Bitboard 81-bit  │ Analisi Minacce Allis │ │
│ └──────────────────┼───────────────────────┘ │
│ │ ai.pl                                    │ │
│ │ Minimax Paranoico + Alpha-Beta + TT      │ │
│ └──────────────────────────────────────────┘ │
└──────────────────────────────────────────────┘
```

1. **Rappresentazione a Bitboard (`bitboard.pl`)**:
   - Ogni tavola e la maschera di occupazione sono interi a 81-bit (9 colonne × 9 bit: 8 righe giocabili + 1 bit sentinella a 0).
   - Verifica di allineamento e vittoria tramite shift di bit istantanei:
     - Verticale: `>> 1`
     - Orizzontale: `>> 9`
     - Diagonale `/`: `>> 10`
     - Diagonale `\`: `>> 8`
2. **Spazio delle Minacce (`threats.pl`)**:
   - 153 tuple da 4 celle calcolate all'avvio.
   - Riconoscimento minacce dirette, dipendenze su celle sottostanti e controllo della colonna centrale (colonna 5).
3. **Motore Decisionale IA (`ai.pl`)**:
   - **Minimax Paranoico**: Turni IA (fasi 2 e 4) = nodi MAX; turni umani (fasi 1 e 3) = nodi MIN.
   - **Potatura Alpha-Beta e Tabella di Trasposizione**: Memorizzazione delle posizioni esplorate e potatura rapida dei rami non ottimali.
   - **Profondità per Difficoltà**:
     - **Facile (`e`)**: Profondità 3
     - **Media (`m`)**: Profondità 4 *(Default)*
     - **Difficile (`h`)**: Profondità 5
     - **Esperto (`x`)**: Profondità 6

---

### Prerequisiti e Installazione

#### 1. Requisiti di Sistema
- **Python 3.10+**
- **SWI-Prolog 9.0+** (assicurarsi che `swipl` sia incluso nel `PATH` di sistema)

#### 2. Installazione Dipendenze Python
```bash
pip install pygame janus-swi
```

> **Nota per Windows**: Assicurati che l'architettura di SWI-Prolog (es. 64-bit) coincida con quella di Python (es. 64-bit).

---

### Esecuzione

#### Avvio del Gioco:
```bash
python main.py
```

#### Esecuzione dei Test Automatizzati:
```bash
python test_system.py
```

---

### Struttura del Progetto

```
.
├── main.py          # Entry point e wrapper Janus Python/Prolog
├── gui.py           # Interfaccia grafica Pygame a 1260x830 px
├── engine.pl        # Modulo principale Prolog e transizione di stato
├── ai.pl            # Minimax paranoico, alpha-beta, tabella trasposizioni
├── bitboard.pl      # Bitboard a 81 bit, maschere e logica di vittoria
├── threats.pl       # Euristica Allis e analisi dello spazio delle minacce
└── test_system.py   # Suite di test automatizzata completa
```
