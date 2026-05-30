"""Sidebar UI built with pygame_gui.

Owns the sliders, dropdown, and buttons. Exposes them as attributes so
main.py can compare incoming UI events against them.
"""

import pygame
import pygame_gui
from pygame_gui.elements import (
    UIButton,
    UIDropDownMenu,
    UIHorizontalSlider,
    UILabel,
    UIPanel,
)

import config


class UI:
    PAD = 12
    LABEL_H = 20
    SLIDER_H = 22
    GAP = 6
    DROP_H = 28
    BTN_H = 30

    def __init__(self, manager, x: int, y: int, w: int, h: int):
        self.manager = manager
        self.w = w
        self.h = h
        self.panel = UIPanel(
            relative_rect=pygame.Rect(x, y, w, h),
            manager=manager,
            starting_height=1,
        )

        inner_w = w - 2 * self.PAD
        cy = self.PAD

        UILabel(
            relative_rect=pygame.Rect(self.PAD, cy, inner_w, 26),
            text="Magnetic Colors",
            manager=manager,
            container=self.panel,
        )
        cy += 26 + self.GAP

        cy = self._build_slider_row(
            manager, cy, inner_w,
            attr_label="n_label",
            attr_slider="n_slider",
            label_text=f"Ball count: {config.DEFAULT_N}",
            start=config.DEFAULT_N,
            vmin=config.MIN_N,
            vmax=config.MAX_N,
        )

        cy = self._build_slider_row(
            manager, cy, inner_w,
            attr_label="f_label",
            attr_slider="f_slider",
            label_text=f"Force: {config.DEFAULT_FORCE:.0f}",
            start=config.DEFAULT_FORCE,
            vmin=config.MIN_FORCE,
            vmax=config.MAX_FORCE,
        )

        UILabel(
            relative_rect=pygame.Rect(self.PAD, cy, inner_w, self.LABEL_H),
            text="Distribution",
            manager=manager,
            container=self.panel,
        )
        cy += self.LABEL_H

        self.dist_drop = UIDropDownMenu(
            options_list=config.DISTRIBUTIONS,
            starting_option=config.DEFAULT_DISTRIBUTION,
            relative_rect=pygame.Rect(self.PAD, cy, inner_w, self.DROP_H),
            manager=manager,
            container=self.panel,
        )
        cy += self.DROP_H + self.GAP

        # Reserve a region for distribution-specific params. Both
        # variants overlap at this y; only one is visible at a time.
        params_y = cy
        self._build_gaussian_widgets(manager, params_y, inner_w)
        self._build_bimodal_widgets(manager, params_y, inner_w)

        params_max_h = 2 * (self.LABEL_H + self.SLIDER_H + self.GAP)
        cy = params_y + params_max_h + self.GAP

        # Buttons row
        btn_w = (inner_w - self.PAD) // 2
        self.restart_btn = UIButton(
            relative_rect=pygame.Rect(self.PAD, cy, btn_w, self.BTN_H),
            text="Restart",
            manager=manager,
            container=self.panel,
        )
        self.pause_btn = UIButton(
            relative_rect=pygame.Rect(self.PAD + btn_w + self.PAD, cy, btn_w, self.BTN_H),
            text="Pause",
            manager=manager,
            container=self.panel,
        )

        self.set_distribution_visibility(config.DEFAULT_DISTRIBUTION)

    # ------------------------------------------------------------------
    # Builders
    # ------------------------------------------------------------------
    def _build_slider_row(self, manager, cy, inner_w,
                          attr_label, attr_slider,
                          label_text, start, vmin, vmax):
        lbl = UILabel(
            relative_rect=pygame.Rect(self.PAD, cy, inner_w, self.LABEL_H),
            text=label_text,
            manager=manager,
            container=self.panel,
        )
        sld = UIHorizontalSlider(
            relative_rect=pygame.Rect(self.PAD, cy + self.LABEL_H, inner_w, self.SLIDER_H),
            start_value=start,
            value_range=(vmin, vmax),
            manager=manager,
            container=self.panel,
        )
        setattr(self, attr_label, lbl)
        setattr(self, attr_slider, sld)
        return cy + self.LABEL_H + self.SLIDER_H + self.GAP

    def _build_gaussian_widgets(self, manager, cy, inner_w):
        self.gauss_mean_label = UILabel(
            relative_rect=pygame.Rect(self.PAD, cy, inner_w, self.LABEL_H),
            text=f"Gauss mean hue: {config.GAUSS_DEFAULT_MEAN:.2f}",
            manager=manager,
            container=self.panel,
        )
        self.gauss_mean_slider = UIHorizontalSlider(
            relative_rect=pygame.Rect(self.PAD, cy + self.LABEL_H, inner_w, self.SLIDER_H),
            start_value=config.GAUSS_DEFAULT_MEAN,
            value_range=(0.0, 1.0),
            manager=manager,
            container=self.panel,
        )
        cy2 = cy + self.LABEL_H + self.SLIDER_H + self.GAP
        self.gauss_std_label = UILabel(
            relative_rect=pygame.Rect(self.PAD, cy2, inner_w, self.LABEL_H),
            text=f"Gauss stddev: {config.GAUSS_DEFAULT_STD:.2f}",
            manager=manager,
            container=self.panel,
        )
        self.gauss_std_slider = UIHorizontalSlider(
            relative_rect=pygame.Rect(self.PAD, cy2 + self.LABEL_H, inner_w, self.SLIDER_H),
            start_value=config.GAUSS_DEFAULT_STD,
            value_range=(0.01, 0.30),
            manager=manager,
            container=self.panel,
        )

    def _build_bimodal_widgets(self, manager, cy, inner_w):
        self.bimo_center_label = UILabel(
            relative_rect=pygame.Rect(self.PAD, cy, inner_w, self.LABEL_H),
            text=f"Bimodal center hue: {config.BIMO_DEFAULT_CENTER:.2f}",
            manager=manager,
            container=self.panel,
        )
        self.bimo_center_slider = UIHorizontalSlider(
            relative_rect=pygame.Rect(self.PAD, cy + self.LABEL_H, inner_w, self.SLIDER_H),
            start_value=config.BIMO_DEFAULT_CENTER,
            value_range=(0.0, 1.0),
            manager=manager,
            container=self.panel,
        )

    # ------------------------------------------------------------------
    # Visibility
    # ------------------------------------------------------------------
    def set_distribution_visibility(self, dist: str):
        gauss = [
            self.gauss_mean_label, self.gauss_mean_slider,
            self.gauss_std_label, self.gauss_std_slider,
        ]
        bimo = [self.bimo_center_label, self.bimo_center_slider]

        for w in gauss + bimo:
            w.hide()

        if dist == "Gaussian":
            for w in gauss:
                w.show()
        elif dist == "Bimodal":
            for w in bimo:
                w.show()
