import pygame
import math


# ═══════════════════════════════════════════════════════════════
# PALETA DE COLORES — tema oscuro industrial/moderno
# ═══════════════════════════════════════════════════════════════
C_BG          = (15,  20,  30)    # fondo principal casi negro azulado
C_BG2         = (22,  30,  45)    # fondo panel lateral
C_SHAFT       = (25,  35,  52)    # hueco del ascensor
C_SHAFT_LINE  = (40,  55,  80)    # líneas guía del hueco
C_FLOOR_LINE  = (45,  60,  88)    # línea de piso
C_FLOOR_LABEL = (80, 110, 150)    # texto etiqueta piso
C_CAB_BODY    = (52, 120, 200)    # cabina ascensor (azul acero)
C_CAB_SHADOW  = (30,  70, 130)    # sombra cabina
C_CAB_OPEN    = (30, 190, 120)    # cabina puerta abierta (verde)
C_CAB_OPEN_S  = (15, 110,  70)    # sombra cabina abierta
C_CAB_DOOR_L  = (200, 230, 255)   # panel puerta izquierda
C_CAB_DOOR_R  = (200, 230, 255)   # panel puerta derecha
C_PERSON_WAIT = (220, 180,  80)   # silueta esperando (ámbar)
C_PERSON_IN   = (255, 255, 255)   # silueta dentro (blanco)
C_ACCENT      = ( 80, 180, 255)   # acento azul claro
C_ACCENT2     = ( 50, 220, 140)   # acento verde
C_TEXT_HI     = (230, 240, 255)   # texto principal
C_TEXT_MID    = (130, 160, 200)   # texto secundario
C_TEXT_DIM    = ( 70,  95, 130)   # texto tenue
C_PANEL_BDR   = ( 50,  70, 105)   # borde panel
C_TAG_BG      = ( 28,  42,  65)   # fondo etiqueta
C_TAG_BDR     = ( 55,  80, 120)   # borde etiqueta


def lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


class PygameView:

    ANCHO        = 1000
    ALTO         = 640
    SHAFT_X      = 80          # borde izquierdo del hueco
    SHAFT_W      = 300         # ancho del hueco
    CAB_W        = 120         # ancho cabina
    CAB_H        = 76          # alto cabina
    PANEL_X      = 440         # inicio panel derecho
    PANEL_W      = 520         # ancho panel derecho

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((self.ANCHO, self.ALTO))
        pygame.display.set_caption("Ascensor Inteligente — Demo IA")

        # fuentes
        self.font_title  = pygame.font.SysFont("consolas",  22, bold=True)
        self.font_label  = pygame.font.SysFont("consolas",  16, bold=True)
        self.font_small  = pygame.font.SysFont("consolas",  13)
        self.font_big    = pygame.font.SysFont("consolas",  36, bold=True)
        self.font_icon   = pygame.font.SysFont("consolas",  11)

        self._cab_y_real  = None   # posición Y actual (para animación suave)
        self._puerta_open = 0.0    # 0.0 = cerrada, 1.0 = abierta
        self._tick        = 0

    # ───────────────────────────────────────────────────────────
    # utilidades de dibujo
    # ───────────────────────────────────────────────────────────
    def _piso_y(self, piso, num_pisos):
        """Y del suelo del piso (borde inferior de la cabina cuando está ahí).
        Se divide la zona en num_pisos+1 slots para que el piso más alto
        tenga espacio suficiente y la cabina no salga por encima del edificio.
        """
        margen_top = 60
        margen_bot = 40
        zona_h     = self.ALTO - margen_top - margen_bot
        paso       = zona_h / (num_pisos + 1)
        return int(self.ALTO - margen_bot - piso * paso)

    def _text(self, surf, txt, font, color, x, y, anchor="topleft"):
        s = font.render(str(txt), True, color)
        r = s.get_rect(**{anchor: (x, y)})
        surf.blit(s, r)
        return r

    def _rounded_rect(self, surf, color, rect, radius=8, border=0, border_color=None):
        pygame.draw.rect(surf, color, rect, border_radius=radius)
        if border and border_color:
            pygame.draw.rect(surf, border_color, rect, border, border_radius=radius)

    def _draw_person(self, surf, cx, cy, color, scale=1.0):
        """Silueta minimalista: cabeza + cuerpo redondeado."""
        r_head  = int(6  * scale)
        body_w  = int(10 * scale)
        body_h  = int(14 * scale)
        # cabeza
        pygame.draw.circle(surf, color, (cx, cy - body_h // 2 - r_head), r_head)
        # cuerpo (rectángulo redondeado)
        body_r = pygame.Rect(cx - body_w // 2, cy - body_h // 2, body_w, body_h)
        pygame.draw.rect(surf, color, body_r, border_radius=4)

    def _draw_persons_grid(self, surf, x0, y0, n, color, scale=1.0, max_col=5):
        """Dibuja n siluetas en grilla."""
        gap_x = int(18 * scale)
        gap_y = int(30 * scale)
        for i in range(n):
            col = i % max_col
            row = i // max_col
            self._draw_person(surf, x0 + col * gap_x, y0 + row * gap_y, color, scale)

    # ───────────────────────────────────────────────────────────
    # secciones principales
    # ───────────────────────────────────────────────────────────
    def _draw_background(self):
        self.screen.fill(C_BG)
        # panel derecho
        panel = pygame.Rect(self.PANEL_X - 10, 0, self.PANEL_W + 10, self.ALTO)
        pygame.draw.rect(self.screen, C_BG2, panel)
        pygame.draw.line(self.screen, C_PANEL_BDR,
                         (self.PANEL_X - 10, 0), (self.PANEL_X - 10, self.ALTO), 1)

    def _draw_shaft(self, num_pisos):
        """Hueco del ascensor: fondo + líneas guía + etiquetas de piso."""
        shaft_rect = pygame.Rect(self.SHAFT_X, 50, self.SHAFT_W, self.ALTO - 90)
        pygame.draw.rect(self.screen, C_SHAFT, shaft_rect, border_radius=6)
        pygame.draw.rect(self.screen, C_SHAFT_LINE, shaft_rect, 1, border_radius=6)

        # raíles verticales
        for rx in [self.SHAFT_X + 18, self.SHAFT_X + self.SHAFT_W - 18]:
            pygame.draw.line(self.screen, C_SHAFT_LINE,
                             (rx, 55), (rx, self.ALTO - 45), 1)

        for piso in range(1, num_pisos + 1):
            y = self._piso_y(piso, num_pisos)

            # línea de piso
            pygame.draw.line(self.screen, C_FLOOR_LINE,
                             (self.SHAFT_X + 22, y),
                             (self.SHAFT_X + self.SHAFT_W - 22, y), 1)

            # etiqueta piso
            tag_w, tag_h = 52, 22
            tag_x = self.SHAFT_X - tag_w - 6
            tag_y = y - tag_h // 2
            self._rounded_rect(self.screen, C_TAG_BG,
                                pygame.Rect(tag_x, tag_y, tag_w, tag_h),
                                radius=4, border=1, border_color=C_TAG_BDR)
            self._text(self.screen, f"P{piso:02d}", self.font_label,
                       C_FLOOR_LABEL, tag_x + tag_w // 2, tag_y + tag_h // 2,
                       anchor="center")

    def _draw_waiting_persons(self, env):
        """Siluetas de pasajeros esperando a la derecha del hueco."""
        shaft_right = self.SHAFT_X + self.SHAFT_W
        for piso in range(1, env.num_pisos + 1):
            y_floor = self._piso_y(piso, env.num_pisos)
            cantidad = sum(1 for p in env.pasajeros_esperando
                           if p["origen"] == piso)
            if cantidad == 0:
                continue
            # pequeño fondo indicador
            area_w = min(cantidad, 5) * 18 + 10
            area_h = 30
            area_x = shaft_right + 8
            area_y = y_floor - area_h - 2
            self._rounded_rect(self.screen, C_TAG_BG,
                                pygame.Rect(area_x - 4, area_y - 2,
                                            area_w, area_h + 4),
                                radius=4)
            self._draw_persons_grid(self.screen,
                                    area_x, area_y,
                                    cantidad, C_PERSON_WAIT,
                                    scale=0.85, max_col=5)

    def _draw_cabin(self, env, accion_nombre):
        """Cabina con animación suave y puertas."""
        y_target = self._piso_y(env.piso_actual, env.num_pisos) - self.CAB_H

        estado_idle = (
            len(env.pasajeros_dentro) == 0 and
            len(env.pasajeros_esperando) == 0
        )

        if self._cab_y_real is None:
            self._cab_y_real = float(y_target)
        elif estado_idle:
            # En idle: congelar la cabina exactamente donde está.
            # No interpolamos — quedarse quieto en el último piso visitado.
            self._cab_y_real = self._cab_y_real  # sin cambio
        else:
            # interpolación suave — con 12 sub-frames a 0.35 llega al 99%
            self._cab_y_real += (y_target - self._cab_y_real) * 0.35

        y = int(self._cab_y_real)

        # La puerta solo se puede abrir cuando la cabina está
        # completamente alineada al piso destino (diferencia < 2 px).
        distancia_al_destino = abs(self._cab_y_real - y_target)
        cabina_alineada = distancia_al_destino < 2.0
        is_open = (accion_nombre == "ABRIR") and cabina_alineada

        # animación apertura puerta
        target_open = 1.0 if is_open else 0.0
        self._puerta_open += (target_open - self._puerta_open) * 0.3

        # cabina: fondo
        cab_x   = self.SHAFT_X + (self.SHAFT_W - self.CAB_W) // 2
        cab_rect = pygame.Rect(cab_x, y, self.CAB_W, self.CAB_H)

        body_color   = C_CAB_OPEN   if is_open else C_CAB_BODY
        shadow_color = C_CAB_OPEN_S if is_open else C_CAB_SHADOW

        # sombra
        s_rect = pygame.Rect(cab_x + 4, y + 6, self.CAB_W, self.CAB_H)
        pygame.draw.rect(self.screen, shadow_color, s_rect, border_radius=8)
        # cuerpo
        pygame.draw.rect(self.screen, body_color, cab_rect, border_radius=8)

        # borde superior (highlight)
        hl_color = C_CAB_OPEN_S if is_open else (80, 150, 230)
        pygame.draw.rect(self.screen, hl_color, cab_rect, 2, border_radius=8)

        # ── puertas deslizantes ──────────────────────────────
        door_max  = self.CAB_W // 2 - 6
        door_open = int(self._puerta_open * (door_max - 4))
        door_y    = y + 10
        door_h    = self.CAB_H - 20

        # puerta izquierda
        dl_w = door_max - door_open
        if dl_w > 2:
            dl_rect = pygame.Rect(cab_x + 6, door_y, dl_w, door_h)
            pygame.draw.rect(self.screen, C_CAB_DOOR_L, dl_rect, border_radius=3)
            # línea borde
            pygame.draw.rect(self.screen, (150, 190, 230), dl_rect, 1, border_radius=3)

        # puerta derecha
        dr_x = cab_x + self.CAB_W // 2 + door_open
        dr_w = door_max - door_open
        if dr_w > 2:
            dr_rect = pygame.Rect(dr_x, door_y, dr_w, door_h)
            pygame.draw.rect(self.screen, C_CAB_DOOR_R, dr_rect, border_radius=3)
            pygame.draw.rect(self.screen, (150, 190, 230), dr_rect, 1, border_radius=3)

        # ── pasajeros dentro ────────────────────────────────
        n_dentro = len(env.pasajeros_dentro)
        if n_dentro > 0:
            px0 = cab_x + 14
            py0 = y + 16
            self._draw_persons_grid(self.screen, px0, py0,
                                    n_dentro, C_PERSON_IN,
                                    scale=0.7, max_col=4)

        # ── número de piso actual sobre la cabina ────────────
        self._text(self.screen, f"▲ P{env.piso_actual}",
                   self.font_label, C_ACCENT,
                   cab_x + self.CAB_W // 2, y - 18, anchor="center")

    def _draw_panel(self, env, accion_nombre):
        """Panel de información lateral derecho."""
        x0 = self.PANEL_X + 10
        y0 = 30

        # ── título ──────────────────────────────────────────
        self._text(self.screen, "ASCENSOR IA",
                   self.font_title, C_TEXT_HI, x0, y0)
        pygame.draw.line(self.screen, C_PANEL_BDR,
                         (x0, y0 + 28), (x0 + self.PANEL_W - 30, y0 + 28), 1)

        # ── acción actual (destacada) ────────────────────────
        accion_color = {
            "SUBIR": (80, 180, 255),
            "BAJAR": (180, 120, 255),
            "ABRIR": (50,  220, 140),
        }.get(accion_nombre, C_TEXT_HI)

        accion_icon = {
            "SUBIR": "▲",
            "BAJAR": "▼",
            "ABRIR": "◈",
        }.get(accion_nombre, "·")

        tag_rect = pygame.Rect(x0, y0 + 38, 220, 52)
        self._rounded_rect(self.screen, C_TAG_BG, tag_rect,
                            radius=8, border=1, border_color=accion_color)
        self._text(self.screen, f"{accion_icon}  {accion_nombre}",
                   self.font_big, accion_color,
                   x0 + 14, y0 + 38 + 10)

        # ── métricas en tarjetas ─────────────────────────────
        metricas = [
            ("Piso actual",    f"{env.piso_actual}",                  C_ACCENT),
            ("Paso",           f"{env.step_actual}",                  C_TEXT_MID),
            ("Transportados",  f"{env.transportados}",                C_ACCENT2),
            ("Esperando",      f"{len(env.pasajeros_esperando)}",     C_PERSON_WAIT),
            ("Dentro",         f"{len(env.pasajeros_dentro)}",        C_PERSON_IN),
        ]

        card_w  = 220
        card_h  = 52
        card_x  = x0
        card_y0 = y0 + 105
        gap     = 8

        for i, (label, valor, color) in enumerate(metricas):
            cy = card_y0 + i * (card_h + gap)
            card = pygame.Rect(card_x, cy, card_w, card_h)
            self._rounded_rect(self.screen, C_TAG_BG, card,
                                radius=6, border=1, border_color=C_TAG_BDR)
            # label
            self._text(self.screen, label, self.font_small,
                       C_TEXT_DIM, card_x + 12, cy + 8)
            # valor
            self._text(self.screen, valor, self.font_label,
                       color, card_x + 12, cy + 26)

        # ── destinos de pasajeros dentro ─────────────────────
        sec_y = card_y0 + len(metricas) * (card_h + gap) + 16
        pygame.draw.line(self.screen, C_PANEL_BDR,
                         (x0, sec_y), (x0 + card_w, sec_y), 1)
        self._text(self.screen, "DESTINOS ACTIVOS", self.font_small,
                   C_TEXT_DIM, x0, sec_y + 6)

        if env.pasajeros_dentro:
            for j, p in enumerate(env.pasajeros_dentro):
                px = x0 + 8 + j * 46
                py = sec_y + 26
                badge = pygame.Rect(px, py, 38, 26)
                self._rounded_rect(self.screen, C_CAB_BODY, badge,
                                   radius=5, border=1,
                                   border_color=(80, 150, 230))
                self._text(self.screen, f"P{p['destino']}",
                           self.font_label, C_TEXT_HI,
                           px + 19, py + 13, anchor="center")
        else:
            self._text(self.screen, "—", self.font_label,
                       C_TEXT_DIM, x0 + 8, sec_y + 28)

        # ── demanda por piso (mini barra) ─────────────────────
        bar_y = sec_y + 70
        pygame.draw.line(self.screen, C_PANEL_BDR,
                         (x0, bar_y), (x0 + card_w, bar_y), 1)
        self._text(self.screen, "DEMANDA POR PISO", self.font_small,
                   C_TEXT_DIM, x0, bar_y + 6)

        for piso in range(1, env.num_pisos + 1):
            n = sum(1 for p in env.pasajeros_esperando
                    if p["origen"] == piso)
            bx    = x0 + (piso - 1) * 44
            by    = bar_y + 26
            bw    = 36
            bh_max = 40
            bh    = int((n / max(1, 5)) * bh_max)

            # fondo barra
            self._rounded_rect(self.screen, C_TAG_BG,
                                pygame.Rect(bx, by, bw, bh_max), radius=4)
            # barra rellena
            if bh > 0:
                fill_color = lerp_color(C_ACCENT2, (220, 80, 80),
                                        min(1.0, n / 4))
                self._rounded_rect(self.screen, fill_color,
                                   pygame.Rect(bx, by + bh_max - bh,
                                               bw, bh), radius=3)
            # etiqueta piso
            self._text(self.screen, f"P{piso}", self.font_icon,
                       C_TEXT_DIM, bx + bw // 2,
                       by + bh_max + 4, anchor="center")
            # número de personas
            if n > 0:
                self._text(self.screen, str(n), self.font_icon,
                           C_TEXT_HI, bx + bw // 2,
                           by + bh_max - bh - 10, anchor="center")

        # ── estado idle ──────────────────────────────────────
        if not env.pasajeros_dentro and not env.pasajeros_esperando:
            idle_y = bar_y + 95
            idle_rect = pygame.Rect(x0, idle_y, card_w, 32)
            self._rounded_rect(self.screen, (40, 55, 40), idle_rect,
                                radius=6, border=1,
                                border_color=(50, 150, 80))
            self._text(self.screen, "⏸  MODO INACTIVO", self.font_label,
                       (80, 200, 100), x0 + idle_rect.w // 2,
                       idle_y + 10, anchor="center")

    # ───────────────────────────────────────────────────────────
    # MÉTODO PRINCIPAL
    # ───────────────────────────────────────────────────────────
    def dibujar(self, env, accion_nombre=""):
        """
        Dibuja un frame completo. Como demo.py llama dibujar() una sola vez
        por step (con pygame.time.delay entre steps), hacemos múltiples
        sub-frames de animación internos para que la cabina llegue al piso
        ANTES de abrir la puerta.
        """
        self._tick += 1

        # Calcular cuántos sub-frames necesita la cabina para llegar al destino.
        # Animamos el movimiento completo ANTES de mostrar la apertura de puerta.
        y_target = self._piso_y(env.piso_actual, env.num_pisos) - env.num_pisos  # referencia
        SUB_FRAMES = 12  # suficientes para completar el 97% de la interpolación

        for sub in range(SUB_FRAMES):
            self._draw_background()
            self._draw_shaft(env.num_pisos)
            self._draw_waiting_persons(env)
            self._draw_cabin(env, accion_nombre)
            self._draw_panel(env, accion_nombre)
            pygame.display.flip()
            pygame.time.delay(20)  # 12 * 20ms = 240ms de animación suave