import pygame


class PygameView:

    def __init__(self):

        pygame.init()

        self.ANCHO = 900
        self.ALTO = 600

        self.screen = pygame.display.set_mode(
            (self.ANCHO, self.ALTO)
        )

        pygame.display.set_caption(
            "Ascensor Inteligente"
        )

        self.font = pygame.font.SysFont(None, 24)

        self.piso_altura = 100

        # colores
        self.COLOR_FONDO = (255, 255, 255)
        self.COLOR_PISO = (0, 0, 0)
        self.COLOR_ASCENSOR = (70, 130, 180)
        self.COLOR_PUERTA_ABIERTA = (0, 200, 0)
        self.COLOR_PUERTA_CERRADA = (0, 100, 255)
        self.COLOR_PASAJERO = (0, 0, 0)

    # -------------------------
    # función auxiliar
    # -------------------------
    def dibujar_pasajeros(self, x, y, cantidad, color=(0, 0, 0)):

        radio = 6
        espacio = 15

        for i in range(cantidad):

            px = x + (i % 5) * espacio
            py = y + (i // 5) * espacio

            pygame.draw.circle(
                self.screen,
                color,
                (px, py),
                radio
            )

    # -------------------------
    # MAIN DRAW
    # -------------------------
    def dibujar(self, env, accion_nombre=""):

        self.screen.fill(self.COLOR_FONDO)

        # =================================================
        # DIBUJAR PISOS Y PASAJEROS ESPERANDO
        # =================================================
        for piso in range(env.num_pisos):

            y = self.ALTO - ((piso + 1) * self.piso_altura)

            # línea del piso
            pygame.draw.line(
                self.screen,
                self.COLOR_PISO,
                (50, y),
                (400, y),
                2
            )

            # texto piso
            texto = self.font.render(
                f"Piso {piso + 1}",
                True,
                self.COLOR_PISO
            )

            self.screen.blit(texto, (10, y - 20))

            # contar pasajeros esperando en ese piso
            cantidad = sum(
                1 for p in env.pasajeros_esperando
                if p["origen"] == piso + 1
            )

            # dibujar pasajeros esperando
            self.dibujar_pasajeros(
                120,
                y - 30,
                cantidad,
                (0, 0, 0)
            )

        # =================================================
        # ASCENSOR
        # =================================================

        ascensor_y = (
            self.ALTO
            - (env.piso_actual * self.piso_altura)
            - 70
        )

        # estado puerta
        if accion_nombre == "ABRIR":
            color_ascensor = self.COLOR_PUERTA_ABIERTA
        else:
            color_ascensor = self.COLOR_ASCENSOR

        # cuerpo ascensor
        pygame.draw.rect(
            self.screen,
            color_ascensor,
            (180, ascensor_y, 80, 60)
        )

        # =================================================
        # PASAJEROS DENTRO DEL ASCENSOR
        # =================================================

        if len(env.pasajeros_dentro) > 0:

            self.dibujar_pasajeros(
                190,
                ascensor_y + 10,
                len(env.pasajeros_dentro),
                (255, 255, 255)
            )

        # =================================================
        # INFORMACIÓN LATERAL
        # =================================================

        info_x = 500

        textos = [
            f"Piso actual: {env.piso_actual}",
            f"Paso: {env.step_actual}",
            f"Transportados: {env.transportados}",
            f"Esperando: {len(env.pasajeros_esperando)}",
            f"Dentro: {len(env.pasajeros_dentro)}",
            f"Acción: {accion_nombre}"
        ]

        for i, texto in enumerate(textos):

            superficie = self.font.render(
                texto,
                True,
                (0, 0, 0)
            )

            self.screen.blit(
                superficie,
                (info_x, 50 + i * 40)
            )

        pygame.display.flip()