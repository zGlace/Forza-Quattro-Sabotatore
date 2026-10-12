"""
Pygame graphical user interface (1260x830px): 8x9 board,
drop animations, game telemetry, and informational modals.
"""

import sys
import time
import math
import pygame


# WINDOW DIMENSIONS
WIN_WIDTH = 1260
WIN_HEIGHT = 830


# COLOR PALETTE
COLOR_BG = (11, 15, 25)
COLOR_HEADER_BG = (17, 24, 39)
COLOR_BOARD_BG = (22, 31, 48)
COLOR_BOARD_BORDER = (42, 58, 84)
COLOR_SLOT_EMPTY = (11, 15, 25)
COLOR_SLOT_RIM = (30, 41, 59)

COLOR_RED_BASE = (239, 68, 68)
COLOR_RED_HIGHLIGHT = (252, 165, 165)
COLOR_RED_DARK = (185, 28, 28)
COLOR_RED_GHOST = (239, 68, 68, 120)

COLOR_YELLOW_BASE = (250, 204, 21)
COLOR_YELLOW_HIGHLIGHT = (254, 249, 195)
COLOR_YELLOW_DARK = (202, 138, 4)
COLOR_YELLOW_GHOST = (250, 204, 21, 120)

COLOR_PANEL_BG = (17, 24, 39)
COLOR_PANEL_BORDER = (31, 41, 55)
COLOR_CARD_BG = (24, 33, 50)
COLOR_TEXT_PRIMARY = (243, 244, 246)
COLOR_TEXT_SECONDARY = (156, 163, 175)
COLOR_TEXT_MUTED = (107, 114, 128)
COLOR_ACCENT_BLUE = (59, 130, 246)
COLOR_ACCENT_GREEN = (16, 185, 129)
COLOR_ACCENT_PURPLE = (139, 92, 246)
COLOR_DISABLED_BG = (22, 28, 38)
COLOR_DISABLED_BORDER = (38, 45, 55)
COLOR_DISABLED_TEXT = (60, 68, 80)
COLOR_WHITE_RING = (255, 255, 255)


# BOARD 8x9 PARAMETERS
BOARD_COLS = 9
BOARD_ROWS = 8
CELL_SIZE = 64
CELL_GAP = 10
CELL_PITCH = CELL_SIZE + CELL_GAP
BOARD_X = 35
BOARD_Y = 105
BOARD_W = BOARD_COLS * CELL_PITCH + CELL_GAP
BOARD_H = BOARD_ROWS * CELL_PITCH + CELL_GAP


class DropAnimation:
    """Physical drop animation with gravity and bounce."""
    def __init__(self, col, target_row, piece, start_y=BOARD_Y - CELL_SIZE):
        self.col = col
        self.target_row = target_row
        self.piece = piece
        self.x = BOARD_X + CELL_GAP + (col - 1) * CELL_PITCH + CELL_SIZE // 2
        self.y = start_y
        visual_row = (BOARD_ROWS - 1) - target_row
        self.target_y = BOARD_Y + CELL_GAP + visual_row * CELL_PITCH + CELL_SIZE // 2
        self.vy = 0.0
        self.gravity = 1.45
        self.bounce_factor = 0.28
        self.bounces = 0
        self.max_bounces = 2
        self.finished = False

    def update(self, dt_scale=1.0):
        if self.finished:
            return
        self.vy += self.gravity * dt_scale
        self.y += self.vy * dt_scale
        if self.y >= self.target_y:
            self.y = self.target_y
            if self.bounces < self.max_bounces and abs(self.vy) > 3.0:
                self.vy = -self.vy * self.bounce_factor
                self.bounces += 1
            else:
                self.vy = 0
                self.finished = True


class ConnectFourGUI:
    """Pygame graphical user interface for game state management and telemetry."""
    def __init__(self, janus_engine):
        self.engine = janus_engine
        pygame.init()
        pygame.display.set_caption("Forza Quattro - Sabotatore")

        # Initialize screen with native hardware V-Sync
        try:
            self.screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT), vsync=1)
        except Exception:
            self.screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))

        # Automatically detect monitor refresh rate
        try:
            hz = pygame.display.get_current_refresh_rate()
            self.target_fps = int(hz) if (hz and hz >= 30) else 60
        except Exception:
            self.target_fps = 60

        self.clock = pygame.time.Clock()

        # Interface fonts
        self.font_title = pygame.font.SysFont(["Segoe UI", "Arial", "Helvetica"], 24, bold=True)
        self.font_badge = pygame.font.SysFont(["Segoe UI", "Arial", "Helvetica"], 16, bold=True)
        self.font_card_title = pygame.font.SysFont(["Segoe UI", "Arial", "Helvetica"], 14, bold=True)
        self.font_data = pygame.font.SysFont(["Segoe UI", "Arial", "Helvetica"], 14)
        self.font_data_bold = pygame.font.SysFont(["Segoe UI", "Arial", "Helvetica"], 14, bold=True)
        self.font_btn = pygame.font.SysFont(["Segoe UI", "Arial", "Helvetica"], 13, bold=True)
        self.font_btn_header = pygame.font.SysFont(["Segoe UI", "Arial", "Helvetica"], 14, bold=True)
        self.font_col_num = pygame.font.SysFont(["Segoe UI", "Arial", "Helvetica"], 18, bold=True)
        self.font_modal_title = pygame.font.SysFont(["Segoe UI", "Arial", "Helvetica"], 26, bold=True)
        self.font_modal_section = pygame.font.SysFont(["Segoe UI", "Arial", "Helvetica"], 16, bold=True)
        self.font_modal_label = pygame.font.SysFont(["Segoe UI", "Arial", "Helvetica"], 17, bold=True)
        self.font_modal_desc = pygame.font.SysFont(["Segoe UI", "Arial", "Helvetica"], 16)
        self.font_modal_body = pygame.font.SysFont(["Segoe UI", "Arial", "Helvetica"], 17)
        self.font_modal_small = pygame.font.SysFont(["Segoe UI", "Arial", "Helvetica"], 15)
        self.font_modal_btn = pygame.font.SysFont(["Segoe UI", "Arial", "Helvetica"], 18, bold=True)
        self.font_history = pygame.font.SysFont(["Segoe UI", "Arial", "Helvetica"], 14)
        self.font_history_bold = pygame.font.SysFont(["Segoe UI", "Arial", "Helvetica"], 15, bold=True)
        self.font_toggle = pygame.font.SysFont(["Segoe UI", "Arial", "Helvetica"], 12, bold=True)
        self.font_subtitle = pygame.font.SysFont(["Segoe UI", "Arial", "Helvetica"], 14)
        self.font_authors = pygame.font.SysFont(["Segoe UI", "Arial", "Helvetica"], 13)

        # Game state and telemetry
        self.state = self.engine.init_game('m')
        self.current_difficulty = 'm'
        self.last_ai_info = self._make_default_ai_info()

        self.anim = None
        self.hover_col = None
        self.ai_thinking = False
        self.ai_start_time = 0.0

        self.last_move = None
        self.move_history = []
        self.show_advanced = False
        self.show_rules_modal = False

        # Interactive rectangles for controls
        self.btn_diff_rects = {}
        self.btn_restart_rect = None
        self.btn_rules_header_rect = None
        self.btn_rules_close_rect = None
        self.btn_toggle_rect = None
        self.btn_gameover_restart_rect = None

    def _make_default_ai_info(self):
        return {
            'depth': {'e': 3, 'm': 4, 'h': 5, 'x': 6}.get(self.current_difficulty, 4),
            'nodes': 0,
            'tt_hits': 0,
            'quiescence_nodes': 0,
            'time_ms': 0,
            'score': 0,
            'threats': self.state.get('threat_stats', {})
        }

    def _reset_game(self):
        """Reset the game to the current difficulty level."""
        self.state = self.engine.init_game(self.current_difficulty)
        self.last_ai_info = self._make_default_ai_info()
        self.last_move = None
        self.move_history = []
        self.anim = None
        self.ai_thinking = False
        self.show_rules_modal = False

    def _get_phase_label(self, phase):
        """Return description and color for the current turn phase."""
        if phase == 1:
            return "Giocatore 1 (Rosso)", COLOR_RED_BASE
        elif phase == 2:
            return "IA Sabotatore (Giallo)", COLOR_YELLOW_BASE
        elif phase == 3:
            return "Giocatore 2 (Giallo)", COLOR_YELLOW_BASE
        else:
            return "IA Sabotatore (Rosso)", (220, 38, 38)

    def _record_move(self, col, target_row, piece, phase):
        """Record the move in the game history."""
        move_num = len(self.move_history) + 1
        is_ai = (phase in (2, 4))
        if phase == 1:
            player_label = "G1 Rosso"
        elif phase == 2:
            player_label = "IA Giallo"
        elif phase == 3:
            player_label = "G2 Giallo"
        else:
            player_label = "IA Rosso"
        self.move_history.append({
            'num': move_num,
            'player_label': player_label,
            'col': col,
            'piece': piece,
            'phase': phase,
            'is_ai': is_ai
        })
        self.last_move = (col, target_row, piece)

    def run(self):
        """Main event loop synchronized with monitor refresh rate."""
        running = True
        while running:
            # Normalized delta-time calculation relative to 60 FPS (dt_scale = 1.0 at 60 FPS)
            dt_ms = self.clock.tick(self.target_fps)
            dt_scale = dt_ms / (1000.0 / 60.0)
            # Safety clamp to prevent anomalous jumps after pauses or window dragging
            dt_scale = max(0.1, min(dt_scale, 2.5))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEMOTION:
                    self.handle_mouse_motion(event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_mouse_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    self.handle_key_down(event.key)

            # Animation update with time scale factor
            if self.anim:
                self.anim.update(dt_scale)
                if self.anim.finished:
                    self.anim = None

            # Execution of AI turn when no animations are in progress
            if (not self.anim and self.state['status'] == 'ongoing'
                    and self.state['player_kind'] == 'ai'
                    and not self.show_rules_modal):
                if not self.ai_thinking:
                    self.ai_thinking = True
                    self.ai_start_time = time.time()
                else:
                    if time.time() - self.ai_start_time > 0.08:
                        self.execute_ai_turn()
                        self.ai_thinking = False

            self.render()
            pygame.display.flip()

        pygame.quit()
        sys.exit()

    def handle_key_down(self, key):
        """Handle keyboard shortcuts."""
        if self.show_rules_modal:
            if key in (pygame.K_ESCAPE, pygame.K_r):
                self.show_rules_modal = False
            return

        if key == pygame.K_TAB:
            self.show_advanced = not self.show_advanced
        elif key == pygame.K_r:
            if self.state['status'] != 'game_over':
                self.show_rules_modal = True
        elif key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
            if not self.anim and not self.ai_thinking:
                self._reset_game()

    def handle_mouse_motion(self, pos):
        """Track the column hovered by mouse cursor."""
        if self.show_rules_modal or (self.state['status'] == 'game_over' and not self.anim):
            self.hover_col = None
            return

        mx, my = pos
        if BOARD_X <= mx <= BOARD_X + BOARD_W and BOARD_Y - 40 <= my <= BOARD_Y + BOARD_H:
            col = int((mx - BOARD_X - CELL_GAP) // CELL_PITCH) + 1
            if 1 <= col <= BOARD_COLS:
                self.hover_col = col
            else:
                self.hover_col = None
        else:
            self.hover_col = None

    def handle_mouse_click(self, pos):
        """Handle mouse clicks on interactive elements."""
        if self.show_rules_modal:
            if self.btn_rules_close_rect and self.btn_rules_close_rect.collidepoint(pos):
                self.show_rules_modal = False
            return

        if self.state['status'] == 'game_over' and not self.anim:
            if self.btn_gameover_restart_rect and self.btn_gameover_restart_rect.collidepoint(pos):
                self._reset_game()
            return

        # Difficulty selection (locked after the first move)
        for diff_key, rect in self.btn_diff_rects.items():
            if rect.collidepoint(pos):
                moves_played = self.state.get('moves', 0)
                if moves_played == 0 and self.current_difficulty != diff_key and not self.anim and not self.ai_thinking:
                    self.current_difficulty = diff_key
                    self.state = self.engine.set_difficulty(diff_key, self.state)
                    self.last_ai_info = self._make_default_ai_info()
                return

        if self.btn_restart_rect and self.btn_restart_rect.collidepoint(pos):
            if not self.anim and not self.ai_thinking:
                self._reset_game()
            return

        if self.btn_rules_header_rect and self.btn_rules_header_rect.collidepoint(pos):
            self.show_rules_modal = not self.show_rules_modal
            return

        if self.btn_toggle_rect and self.btn_toggle_rect.collidepoint(pos):
            self.show_advanced = not self.show_advanced
            return

        # User move
        if self.state['status'] == 'ongoing' and self.state['player_kind'] == 'human' and not self.anim:
            if self.hover_col and self.hover_col in self.state.get('valid_moves', []):
                self.execute_human_move(self.hover_col)

    def execute_human_move(self, col):
        """Execute the move selected by the user."""
        phase = self.state.get('phase', 1)
        piece = self.state['piece']
        target_row = self.get_next_row_for_col(col)
        new_state = self.engine.play_move(col, self.state)
        self.anim = DropAnimation(col, target_row, piece)
        self._record_move(col, target_row, piece, phase)
        self.state = new_state

    def execute_ai_turn(self):
        """Request and execute move computed by the AI."""
        phase = self.state.get('phase', 1)
        piece = self.state['piece']
        best_col, info = self.engine.get_ai_move(self.state)
        self.last_ai_info = info
        target_row = self.get_next_row_for_col(best_col)
        new_state = self.engine.play_move(best_col, self.state)
        self.anim = DropAnimation(best_col, target_row, piece)
        self._record_move(best_col, target_row, piece, phase)
        self.state = new_state

    def get_next_row_for_col(self, col):
        """Return logical row (0..7) where the piece lands."""
        matrix = self.state.get('matrix', [])
        for visual_r in range(BOARD_ROWS - 1, -1, -1):
            if matrix[visual_r][col - 1] == 0:
                return (BOARD_ROWS - 1) - visual_r
        return BOARD_ROWS - 1


    # GRAPHIC RENDERING
    def render(self):
        """Render the complete game interface on screen."""
        self.screen.fill(COLOR_BG)
        self.render_header()
        self.render_board()
        self.render_dashboard()

        if self.state['status'] == 'game_over' and not self.anim:
            self.render_game_over_modal()
        elif self.show_rules_modal:
            self.render_rules_modal()

    def render_header(self):
        """Top header with title, credits, and rules button."""
        header_rect = pygame.Rect(0, 0, WIN_WIDTH, 80)
        pygame.draw.rect(self.screen, COLOR_HEADER_BG, header_rect)
        pygame.draw.line(self.screen, COLOR_PANEL_BORDER, (0, 80), (WIN_WIDTH, 80), 2)

        title_surf = self.font_title.render("FORZA QUATTRO - SABOTATORE", True, COLOR_TEXT_PRIMARY)
        title_rect = title_surf.get_rect(topleft=(BOARD_X, 26))
        self.screen.blit(title_surf, title_rect)

        sep_surf = self.font_authors.render("|", True, (75, 85, 105))
        sep_rect = sep_surf.get_rect(midleft=(title_rect.right + 14, title_rect.centery + 1))
        self.screen.blit(sep_surf, sep_rect)

        authors_surf = self.font_authors.render("Candigliota Michele & Gismondi Alexander", True, COLOR_TEXT_SECONDARY)
        authors_rect = authors_surf.get_rect(midleft=(sep_rect.right + 14, title_rect.centery + 1))
        self.screen.blit(authors_surf, authors_rect)

        btn_text = "Regole del Gioco [R]"
        btn_surf = self.font_btn_header.render(btn_text, True, COLOR_ACCENT_BLUE)
        btn_w = btn_surf.get_width() + 28
        btn_h = 36
        btn_x = WIN_WIDTH - btn_w - 30
        btn_y = (80 - btn_h) // 2
        self.btn_rules_header_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)

        pygame.draw.rect(self.screen, (24, 40, 66), self.btn_rules_header_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_ACCENT_BLUE, self.btn_rules_header_rect, width=2, border_radius=8)
        btn_rect = btn_surf.get_rect(center=self.btn_rules_header_rect.center)
        self.screen.blit(btn_surf, btn_rect)

    def render_board(self):
        """Draw the game grid, pieces, highlights, and previews."""
        board_rect = pygame.Rect(BOARD_X, BOARD_Y, BOARD_W, BOARD_H)
        pygame.draw.rect(self.screen, COLOR_BOARD_BG, board_rect, border_radius=18)
        pygame.draw.rect(self.screen, COLOR_BOARD_BORDER, board_rect, width=3, border_radius=18)

        # Selected column indicator and piece preview (ghost)
        if self.hover_col and self.state['status'] == 'ongoing' and not self.anim:
            col_x = BOARD_X + CELL_GAP + (self.hover_col - 1) * CELL_PITCH
            beam_surf = pygame.Surface((CELL_SIZE, BOARD_H), pygame.SRCALPHA)
            beam_surf.fill((255, 255, 255, 12))
            self.screen.blit(beam_surf, (col_x, BOARD_Y))

            arrow_x = col_x + CELL_SIZE // 2
            arrow_y = BOARD_Y - 14
            pygame.draw.polygon(self.screen, COLOR_ACCENT_BLUE, [
                (arrow_x - 10, arrow_y - 12),
                (arrow_x + 10, arrow_y - 12),
                (arrow_x, arrow_y)
            ])

            if self.hover_col in self.state.get('valid_moves', []):
                piece = self.state['piece']
                ghost_color = COLOR_RED_GHOST if piece == 1 else COLOR_YELLOW_GHOST
                ghost_surf = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                pygame.draw.circle(ghost_surf, ghost_color, (CELL_SIZE // 2, CELL_SIZE // 2), CELL_SIZE // 2 - 4)
                self.screen.blit(ghost_surf, (col_x, BOARD_Y - 48))

        # Board cells and last move highlighting
        matrix = self.state.get('matrix', [])
        for vr in range(BOARD_ROWS):
            for vc in range(BOARD_COLS):
                cx = BOARD_X + CELL_GAP + vc * CELL_PITCH + CELL_SIZE // 2
                cy = BOARD_Y + CELL_GAP + vr * CELL_PITCH + CELL_SIZE // 2
                radius = CELL_SIZE // 2 - 4

                cell_val = matrix[vr][vc] if vr < len(matrix) and vc < len(matrix[vr]) else 0
                if self.anim and (vc + 1) == self.anim.col and ((BOARD_ROWS - 1) - vr) == self.anim.target_row:
                    cell_val = 0

                pygame.draw.circle(self.screen, COLOR_SLOT_EMPTY, (cx, cy), radius)
                pygame.draw.circle(self.screen, COLOR_SLOT_RIM, (cx, cy), radius, 2)

                if cell_val == 1:
                    self.draw_shiny_piece(cx, cy, radius, COLOR_RED_BASE, COLOR_RED_HIGHLIGHT, COLOR_RED_DARK)
                    if self._is_last_move_cell(vc + 1, (BOARD_ROWS - 1) - vr, 1):
                        self._draw_last_move_ring(cx, cy, radius)
                elif cell_val == 2:
                    self.draw_shiny_piece(cx, cy, radius, COLOR_YELLOW_BASE, COLOR_YELLOW_HIGHLIGHT, COLOR_YELLOW_DARK)
                    if self._is_last_move_cell(vc + 1, (BOARD_ROWS - 1) - vr, 2):
                        self._draw_last_move_ring(cx, cy, radius)

        # Falling game piece (active animation)
        if self.anim:
            radius = CELL_SIZE // 2 - 4
            if self.anim.piece == 1:
                self.draw_shiny_piece(int(self.anim.x), int(self.anim.y), radius,
                                      COLOR_RED_BASE, COLOR_RED_HIGHLIGHT, COLOR_RED_DARK)
            else:
                self.draw_shiny_piece(int(self.anim.x), int(self.anim.y), radius,
                                      COLOR_YELLOW_BASE, COLOR_YELLOW_HIGHLIGHT, COLOR_YELLOW_DARK)

        # Numeric indices of the columns (1..9)
        for col_idx in range(1, 10):
            num_x = BOARD_X + CELL_GAP + (col_idx - 1) * CELL_PITCH + CELL_SIZE // 2
            num_y = BOARD_Y + BOARD_H + 20
            num_surf = self.font_col_num.render(str(col_idx), True, COLOR_TEXT_MUTED)
            rect = num_surf.get_rect(center=(num_x, num_y))
            self.screen.blit(num_surf, rect)

    def _is_last_move_cell(self, col, logical_row, piece):
        """Check if the cell corresponds to the last played move."""
        if self.last_move is None or self.anim:
            return False
        lm_col, lm_row, lm_piece = self.last_move
        return col == lm_col and logical_row == lm_row and piece == lm_piece

    def _draw_last_move_ring(self, cx, cy, radius):
        """Circular glow ring highlighting the last dropped piece."""
        pygame.draw.circle(self.screen, COLOR_WHITE_RING, (cx, cy), radius + 2, 3)
        ring_surf = pygame.Surface((radius * 2 + 12, radius * 2 + 12), pygame.SRCALPHA)
        pygame.draw.circle(ring_surf, (255, 255, 255, 80),
                           (radius + 6, radius + 6), radius + 5, 2)
        self.screen.blit(ring_surf, (cx - radius - 6, cy - radius - 6))

    def draw_shiny_piece(self, cx, cy, radius, base_color, highlight_color, dark_color):
        """Draw a piece with 3D depth and circular highlight effects."""
        pygame.draw.circle(self.screen, dark_color, (cx, cy + 2), radius)
        pygame.draw.circle(self.screen, base_color, (cx, cy), radius)

        inner_r = int(radius * 0.72)
        inner_cx = cx - int(radius * 0.18)
        inner_cy = cy - int(radius * 0.18)
        pygame.draw.circle(self.screen, highlight_color, (inner_cx, inner_cy), inner_r // 2)
        pygame.draw.circle(self.screen, base_color, (cx, cy), radius, 2)

    def render_dashboard(self):
        """Side panel with telemetry, controls, and move history."""
        panel_x = 760
        panel_w = 460


        # TURN SECTION 
        card1_y = BOARD_Y
        card1_h = 82
        self.draw_card(panel_x, card1_y, panel_w, card1_h, "TURNO CORRENTE")

        phase = self.state.get('phase', 1)
        phase_label, phase_color = self._get_phase_label(phase)
        badge_text = f"Fase {phase}/4: {phase_label}"

        badge_surf = self.font_badge.render(badge_text, True, phase_color)
        self.screen.blit(badge_surf, (panel_x + 18, card1_y + 34))

        if self.state['status'] == 'game_over':
            sub_msg = "Partita conclusa"
        elif self.state['player_kind'] == 'human':
            sub_msg = "Clicca su una colonna giocabile"
        elif self.ai_thinking:
            sub_msg = "L'IA sta analizzando l'albero decisionale..."
        else:
            sub_msg = "Mossa calcolata"
        msg_surf = self.font_subtitle.render(sub_msg, True, COLOR_TEXT_SECONDARY)
        self.screen.blit(msg_surf, (panel_x + 18, card1_y + 57))

        # DIFFICULTY SECTION (locked in-game)
        card2_y = card1_y + card1_h + 10
        card2_h = 78
        self.draw_card(panel_x, card2_y, panel_w, card2_h, "DIFFICOLTÀ IA")

        moves_played = self.state.get('moves', 0)
        is_locked = moves_played > 0

        diffs = [
            ('e', 'Facile (D:3)'),
            ('m', 'Medio (D:4)'),
            ('h', 'Difficile (D:5)'),
            ('x', 'Estremo (D:6)')
        ]
        btn_w = (panel_w - 36 - 3 * 8) // 4
        btn_h = 32
        btn_y = card2_y + 36
        self.btn_diff_rects = {}

        for i, (key, label) in enumerate(diffs):
            bx = panel_x + 18 + i * (btn_w + 8)
            rect = pygame.Rect(bx, btn_y, btn_w, btn_h)
            self.btn_diff_rects[key] = rect
            is_active = (self.current_difficulty == key)

            if is_locked and not is_active:
                bg = COLOR_DISABLED_BG
                border_c = COLOR_DISABLED_BORDER
                text_c = COLOR_DISABLED_TEXT
            elif is_active:
                bg = COLOR_ACCENT_BLUE
                border_c = (96, 165, 250)
                text_c = (255, 255, 255)
            else:
                bg = (31, 41, 55)
                border_c = (55, 65, 81)
                text_c = COLOR_TEXT_SECONDARY

            pygame.draw.rect(self.screen, bg, rect, border_radius=6)
            pygame.draw.rect(self.screen, border_c, rect, width=1, border_radius=6)

            lbl_surf = self.font_btn.render(label, True, text_c)
            lbl_rect = lbl_surf.get_rect(center=rect.center)
            self.screen.blit(lbl_surf, lbl_rect)


        # STATISTICS AND TELEMETRY SECTION (Base / Advanced)
        card3_y = card2_y + card2_h + 10
        if self.show_advanced:
            card3_h = 244
            card_title = "INFORMAZIONI AVANZATE"
        else:
            card3_h = 135
            card_title = "INFORMAZIONI"

        self.draw_card(panel_x, card3_y, panel_w, card3_h, card_title)

        active_tab_text = "Avanzate" if self.show_advanced else "Base"
        toggle_surf = self.font_toggle.render(active_tab_text, True, COLOR_ACCENT_BLUE)
        toggle_w = toggle_surf.get_width() + 16
        toggle_h = 22
        toggle_x = panel_x + panel_w - toggle_w - 14
        toggle_y = card3_y + 7
        self.btn_toggle_rect = pygame.Rect(toggle_x, toggle_y, toggle_w, toggle_h)

        pygame.draw.rect(self.screen, (30, 50, 80), self.btn_toggle_rect, border_radius=4)
        pygame.draw.rect(self.screen, COLOR_ACCENT_BLUE, self.btn_toggle_rect, width=1, border_radius=4)
        tog_rect = toggle_surf.get_rect(center=self.btn_toggle_rect.center)
        self.screen.blit(toggle_surf, tog_rect)

        tab_surf = self.font_toggle.render("[TAB]", True, COLOR_TEXT_MUTED)
        self.screen.blit(tab_surf, (toggle_x - tab_surf.get_width() - 6, toggle_y + 4))

        moves_count = self.state.get('moves', 0)
        free_cells = 72 - moves_count
        depth = self.last_ai_info.get('depth', 4)
        t_ms = self.last_ai_info.get('time_ms', 0)
        threats = self.last_ai_info.get('threats', self.state.get('threat_stats', {}))
        dir_p1 = threats.get('direct_threats_p1', 0)
        dir_p2 = threats.get('direct_threats_p2', 0)
        del_p1 = threats.get('delayed_threats_p1', 0)
        del_p2 = threats.get('delayed_threats_p2', 0)

        if not self.show_advanced:
            rows_info = [
                ("Mosse giocate:", f"{moves_count} / 72  ({free_cells} celle libere)", COLOR_TEXT_PRIMARY),
                ("Profondità di ricerca:", f"{depth} semimosse (plies)", COLOR_ACCENT_BLUE),
                ("Tempo di calcolo:", f"{t_ms} ms", COLOR_ACCENT_GREEN),
                ("Minacce dirette:",
                 f"P1: {dir_p1}   |   P2: {dir_p2}",
                 COLOR_RED_BASE if dir_p1 > 0 else (COLOR_YELLOW_BASE if dir_p2 > 0 else COLOR_TEXT_PRIMARY)),
                ("Minacce differite:", f"P1: {del_p1}   |   P2: {del_p2}", COLOR_TEXT_PRIMARY),
            ]
        else:
            nodes = self.last_ai_info.get('nodes', 0)
            tt_hits = self.last_ai_info.get('tt_hits', 0)
            q_nodes = self.last_ai_info.get('quiescence_nodes', 0)
            score = self.last_ai_info.get('score', 0)
            blocked = threats.get('blocked_tuples', 0)
            double_p1 = threats.get('double_threat_pairs_p1', 0)
            double_p2 = threats.get('double_threat_pairs_p2', 0)

            rows_info = [
                ("Mosse giocate:", f"{moves_count} / 72  ({free_cells} celle libere)", COLOR_TEXT_PRIMARY),
                ("Profondità di ricerca:", f"{depth} semimosse (plies)", COLOR_ACCENT_BLUE),
                ("Nodi esplorati:", f"{nodes:,} nodi", COLOR_ACCENT_PURPLE),
                ("Trasposizioni (TT hit):", f"{tt_hits:,} hit", COLOR_ACCENT_GREEN),
                ("Estensione tattica:", f"{q_nodes:,} nodi", COLOR_ACCENT_PURPLE),
                ("Tempo di calcolo:", f"{t_ms} ms", COLOR_ACCENT_GREEN),
                ("Punteggio minimax:", f"{score}", COLOR_TEXT_PRIMARY),
                ("Minacce dirette:",
                 f"P1: {dir_p1}   |   P2: {dir_p2}",
                 COLOR_RED_BASE if dir_p1 > 0 else (COLOR_YELLOW_BASE if dir_p2 > 0 else COLOR_TEXT_PRIMARY)),
                ("Minacce differite:", f"P1: {del_p1}   |   P2: {del_p2}", COLOR_TEXT_PRIMARY),
                ("Doppie minacce:", f"P1: {double_p1}   |   P2: {double_p2}", COLOR_RED_BASE),
                ("Tuple neutralizzate:", f"{blocked} / 153 tuple", COLOR_ACCENT_GREEN),
            ]

        for idx, (lbl, val, col) in enumerate(rows_info):
            ry = card3_y + 32 + idx * 18
            lbl_surf = self.font_data.render(lbl, True, COLOR_TEXT_SECONDARY)
            val_surf = self.font_data_bold.render(val, True, col)
            self.screen.blit(lbl_surf, (panel_x + 18, ry))
            self.screen.blit(val_surf, (panel_x + 220, ry))


        # MOVE HISTORY SECTION
        card4_y = card3_y + card3_h + 10
        card4_bottom = BOARD_Y + BOARD_H
        card4_h = card4_bottom - card4_y
        if card4_h < 80:
            card4_h = 80
        self.draw_card(panel_x, card4_y, panel_w, card4_h, "CRONOLOGIA MOSSE")

        history_start_y = card4_y + 32
        history_end_y = card4_y + card4_h - 6
        row_height = 24
        available_rows = max(1, (history_end_y - history_start_y) // row_height)

        if not self.move_history:
            empty_surf = self.font_data.render("Nessuna mossa ancora giocata", True, COLOR_TEXT_MUTED)
            self.screen.blit(empty_surf, (panel_x + 18, history_start_y + 6))
        else:
            visible = self.move_history[-available_rows:]
            visible = list(reversed(visible))

            for idx, entry in enumerate(visible):
                ry = history_start_y + idx * row_height
                if ry + row_height > history_end_y:
                    break

                num_str = f"#{entry['num']:>2}"
                player_str = entry['player_label']
                is_ai = entry.get('is_ai', False) or player_str.startswith('IA')

                if is_ai:
                    turn_col = (255, 255, 255)
                elif entry['piece'] == 1:
                    turn_col = COLOR_RED_BASE
                else:
                    turn_col = COLOR_YELLOW_BASE

                dot_y = ry + row_height // 2
                dot_x = panel_x + 22
                pygame.draw.circle(self.screen, turn_col, (dot_x, dot_y), 6)

                num_surf = self.font_history_bold.render(num_str, True, COLOR_TEXT_MUTED)
                num_rect = num_surf.get_rect(midleft=(dot_x + 14, dot_y))
                self.screen.blit(num_surf, num_rect)

                player_surf = self.font_history_bold.render(player_str, True, turn_col)
                player_rect = player_surf.get_rect(midleft=(dot_x + 60, dot_y))
                self.screen.blit(player_surf, player_rect)

                badge_w = 98
                badge_h = 24
                badge_x = panel_x + panel_w - badge_w - 18
                badge_y = ry + (row_height - badge_h) // 2
                col_badge_rect = pygame.Rect(badge_x, badge_y, badge_w, badge_h)
                pygame.draw.rect(self.screen, (20, 28, 44), col_badge_rect, border_radius=6)
                pygame.draw.rect(self.screen, (38, 50, 72), col_badge_rect, width=1, border_radius=6)

                col_surf = self.font_history.render(f"Colonna {entry['col']}", True, COLOR_TEXT_SECONDARY)
                visual_b = col_surf.get_bounding_rect()
                col_rect = col_surf.get_rect()
                col_rect.x = col_badge_rect.centerx - (visual_b.x + visual_b.width // 2)
                col_rect.y = col_badge_rect.centery - (visual_b.y + visual_b.height // 2)
                self.screen.blit(col_surf, col_rect)


        # NEW GAME BUTTON
        btn_restart_y = BOARD_Y + BOARD_H + 12
        self.btn_restart_rect = pygame.Rect(panel_x, btn_restart_y, panel_w, 42)
        pygame.draw.rect(self.screen, (30, 41, 59), self.btn_restart_rect, border_radius=8)
        pygame.draw.rect(self.screen, (51, 65, 85), self.btn_restart_rect, width=2, border_radius=8)

        restart_lbl = self.font_badge.render("NUOVA PARTITA [SPAZIO]", True, COLOR_TEXT_PRIMARY)
        restart_rect = restart_lbl.get_rect(center=self.btn_restart_rect.center)
        self.screen.blit(restart_lbl, restart_rect)

    def draw_card(self, x, y, w, h, title):
        card_rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, COLOR_CARD_BG, card_rect, border_radius=10)
        pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, card_rect, width=1, border_radius=10)
        t_surf = self.font_card_title.render(title, True, COLOR_TEXT_MUTED)
        self.screen.blit(t_surf, (x + 16, y + 10))


    # GAME RULES
    def render_rules_modal(self):
        """Semi-transparent modal overlay displaying game rules."""
        overlay = pygame.Surface((WIN_WIDTH, WIN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        modal_w = 760
        modal_h = 565
        mx = (WIN_WIDTH - modal_w) // 2
        my = (WIN_HEIGHT - modal_h) // 2
        modal_rect = pygame.Rect(mx, my, modal_w, modal_h)

        pygame.draw.rect(self.screen, COLOR_CARD_BG, modal_rect, border_radius=16)
        pygame.draw.rect(self.screen, (255, 255, 255), modal_rect, width=2, border_radius=16)

        title_surf = self.font_modal_title.render("REGOLE DEL GIOCO", True, COLOR_TEXT_PRIMARY)
        title_rect = title_surf.get_rect(center=(WIN_WIDTH // 2, my + 36))
        self.screen.blit(title_surf, title_rect)

        pygame.draw.line(self.screen, COLOR_PANEL_BORDER,
                         (mx + 30, my + 64), (mx + modal_w - 30, my + 64), 1)

        # Section: Objectives
        cy = my + 80
        section_surf = self.font_modal_section.render("OBIETTIVI", True, COLOR_ACCENT_BLUE)
        self.screen.blit(section_surf, (mx + 36, cy))
        cy += 28

        objectives = [
            ("Giocatore 1 (Rosso):", "Allineare 4 pedine rosse in fila.", COLOR_RED_BASE),
            ("Giocatore 2 (Giallo):", "Allineare 4 pedine gialle in fila.", COLOR_YELLOW_BASE),
            ("Sabotatore (IA):", "Impedire ogni 4-in-linea, saturando le 72 celle.", (255, 255, 255)),
        ]
        for label, desc, color in objectives:
            lbl_surf = self.font_modal_label.render(label, True, color)
            desc_surf = self.font_modal_desc.render(desc, True, COLOR_TEXT_SECONDARY)
            self.screen.blit(lbl_surf, (mx + 46, cy))
            self.screen.blit(desc_surf, (mx + 260, cy + 1))
            cy += 28

        # Section: Turn Cycle
        cy += 14
        section_surf = self.font_modal_section.render("CICLO DEI TURNI (4 FASI)", True, COLOR_ACCENT_BLUE)
        self.screen.blit(section_surf, (mx + 36, cy))
        cy += 28

        turns = [
            ("Fase 1:", "Giocatore 1 piazza una pedina Rossa", COLOR_RED_BASE),
            ("Fase 2:", "Sabotatore piazza una pedina Gialla", (255, 255, 255)),
            ("Fase 3:", "Giocatore 2 piazza una pedina Gialla", COLOR_YELLOW_BASE),
            ("Fase 4:", "Sabotatore piazza una pedina Rossa", (255, 255, 255)),
        ]
        for label, desc, color in turns:
            lbl_surf = self.font_modal_label.render(label, True, color)
            desc_surf = self.font_modal_desc.render(desc, True, COLOR_TEXT_SECONDARY)
            self.screen.blit(lbl_surf, (mx + 46, cy))
            self.screen.blit(desc_surf, (mx + 140, cy + 1))
            cy += 26

        # Section: Shortcuts
        cy += 14
        pygame.draw.line(self.screen, COLOR_PANEL_BORDER,
                         (mx + 30, cy), (mx + modal_w - 30, cy), 1)
        cy += 14
        section_surf = self.font_modal_section.render("SCORCIATOIE DA TASTIERA", True, COLOR_ACCENT_BLUE)
        self.screen.blit(section_surf, (mx + 36, cy))
        cy += 28

        shortcuts = [
            ("TAB", "Alterna statistiche Base / Avanzate"),
            ("R", "Apri / Chiudi questa schermata"),
            ("SPAZIO", "Ricomincia una Nuova Partita"),
            ("ESC", "Chiudi questa schermata"),
        ]
        for key, desc in shortcuts:
            key_surf = self.font_modal_label.render(f"[{key}]", True, COLOR_ACCENT_PURPLE)
            desc_surf = self.font_modal_desc.render(desc, True, COLOR_TEXT_SECONDARY)
            self.screen.blit(key_surf, (mx + 46, cy))
            self.screen.blit(desc_surf, (mx + 140, cy + 1))
            cy += 26

        btn_w = 220
        btn_h = 42
        btn_x = (WIN_WIDTH - btn_w) // 2
        btn_y = my + modal_h - 54
        self.btn_rules_close_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        pygame.draw.rect(self.screen, (24, 40, 66), self.btn_rules_close_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_ACCENT_BLUE, self.btn_rules_close_rect, width=2, border_radius=8)
        close_text = self.font_modal_btn.render("Chiudi [ESC / R]", True, COLOR_ACCENT_BLUE)
        close_text_rect = close_text.get_rect(center=self.btn_rules_close_rect.center)
        self.screen.blit(close_text, close_text_rect)


    #  GAME OVER
    def render_game_over_modal(self):
        """Overlay displaying game outcome and restart button."""
        overlay = pygame.Surface((WIN_WIDTH, WIN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        winner = self.state.get('winner', 0)
        modal_w = 660
        modal_h = 260
        mx = (WIN_WIDTH - modal_w) // 2
        my = (WIN_HEIGHT - modal_h) // 2
        modal_rect = pygame.Rect(mx, my, modal_w, modal_h)

        pygame.draw.rect(self.screen, COLOR_CARD_BG, modal_rect, border_radius=16)

        if winner == 1:
            title_text = "VITTORIA DEL GIOCATORE 1 (ROSSO)!"
            desc_text = "Il Giocatore 1 ha completato 4 pedine in linea."
            t_color = COLOR_RED_BASE
            border_color = COLOR_RED_BASE
        elif winner == 2:
            title_text = "VITTORIA DEL GIOCATORE 2 (GIALLO)!"
            desc_text = "Il Giocatore 2 ha completato 4 pedine in linea."
            t_color = COLOR_YELLOW_BASE
            border_color = COLOR_YELLOW_BASE
        else:
            title_text = "TRIONFO DEL SABOTATORE! (PAREGGIO)"
            desc_text = "L'IA ha saturato la griglia 8x9 impedendo ogni 4-in-linea!"
            t_color = COLOR_ACCENT_GREEN
            border_color = COLOR_ACCENT_GREEN

        pygame.draw.rect(self.screen, border_color, modal_rect, width=3, border_radius=16)

        t_surf = self.font_modal_title.render(title_text, True, t_color)
        t_rect = t_surf.get_rect(center=(WIN_WIDTH // 2, my + 50))
        self.screen.blit(t_surf, t_rect)

        d_surf = self.font_modal_body.render(desc_text, True, COLOR_TEXT_PRIMARY)
        d_rect = d_surf.get_rect(center=(WIN_WIDTH // 2, my + 95))
        self.screen.blit(d_surf, d_rect)

        info_moves = f"Partita conclusa con {self.state.get('moves', 72)} mosse su 72 celle."
        m_surf = self.font_modal_small.render(info_moves, True, COLOR_TEXT_MUTED)
        m_rect = m_surf.get_rect(center=(WIN_WIDTH // 2, my + 128))
        self.screen.blit(m_surf, m_rect)

        btn_w = 300
        btn_h = 48
        btn_x = (WIN_WIDTH - btn_w) // 2
        btn_y = my + modal_h - 70
        self.btn_gameover_restart_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)

        pygame.draw.rect(self.screen, COLOR_ACCENT_BLUE, self.btn_gameover_restart_rect, border_radius=10)
        pygame.draw.rect(self.screen, (96, 165, 250), self.btn_gameover_restart_rect, width=2, border_radius=10)

        btn_text = self.font_modal_btn.render("NUOVA PARTITA [SPAZIO]", True, (255, 255, 255))
        btn_text_rect = btn_text.get_rect(center=self.btn_gameover_restart_rect.center)
        self.screen.blit(btn_text, btn_text_rect)
