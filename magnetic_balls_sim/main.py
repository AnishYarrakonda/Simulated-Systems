"""Entry point: wires up the pygame window, the simulation, and the UI."""

import sys

import pygame
import pygame_gui

import config
from renderer import draw as draw_sim
from simulation import Simulation
from ui import UI


def main():
    pygame.init()
    pygame.display.set_caption("Magnetic Color-Wheel Balls")
    screen = pygame.display.set_mode((config.WINDOW_W, config.WINDOW_H))
    clock = pygame.time.Clock()

    manager = pygame_gui.UIManager((config.WINDOW_W, config.WINDOW_H))

    sim = Simulation(config.SIM_X, config.SIM_Y, config.SIM_SIZE)

    sidebar_x = config.SIM_X + config.SIM_SIZE + config.BOX_MARGIN
    sidebar_w = config.WINDOW_W - sidebar_x - config.BOX_MARGIN
    sidebar_y = config.BOX_MARGIN
    sidebar_h = config.WINDOW_H - 2 * config.BOX_MARGIN
    ui = UI(manager, sidebar_x, sidebar_y, sidebar_w, sidebar_h)

    font = pygame.font.SysFont("Arial", 14)

    running = True
    while running:
        dt = clock.tick(config.FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
                handle_slider(event, sim, ui)

            elif event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
                if event.ui_element is ui.dist_drop:
                    sim.distribution = event.text
                    ui.set_distribution_visibility(event.text)

            elif event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element is ui.restart_btn:
                    sim.restart()
                elif event.ui_element is ui.pause_btn:
                    sim.paused = not sim.paused
                    ui.pause_btn.set_text("Resume" if sim.paused else "Pause")

            manager.process_events(event)

        sim.step(dt)
        manager.update(dt)

        screen.fill(config.WINDOW_BG)
        draw_sim(screen, sim, font, clock.get_fps())
        manager.draw_ui(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


def handle_slider(event, sim, ui):
    el = event.ui_element
    v = el.get_current_value()

    if el is ui.n_slider:
        sim.n = int(v)
        ui.n_label.set_text(f"Ball count: {sim.n}")
        return
    if el is ui.f_slider:
        sim.force_strength = float(v)
        ui.f_label.set_text(f"Force: {sim.force_strength:.0f}")
        return
    if el is ui.gauss_mean_slider:
        sim.params["mean"] = float(v)
        ui.gauss_mean_label.set_text(f"Gauss mean hue: {sim.params['mean']:.2f}")
        return
    if el is ui.gauss_std_slider:
        sim.params["stddev"] = float(v)
        ui.gauss_std_label.set_text(f"Gauss stddev: {sim.params['stddev']:.2f}")
        return
    if el is ui.bimo_center_slider:
        sim.params["center"] = float(v)
        ui.bimo_center_label.set_text(f"Bimodal center hue: {sim.params['center']:.2f}")
        return


if __name__ == "__main__":
    main()
