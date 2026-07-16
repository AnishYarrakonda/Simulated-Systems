"""Tunable parameters for the natural selection sim.

Defaults are Primer's, from natural_sim.py in Helpsypoo/primerpython.
"""

from dataclasses import dataclass


@dataclass
class Config:
    # -- world -------------------------------------------------------------
    world_extent: float = 150.0  # WORLD_DIMENSIONS is a half-extent: -150..150
    sim_resolution: int = 1  # SIM_RESOLUTION
    default_day_length: int = 600  # DEFAULT_DAY_LENGTH (fallback only)

    food_count: int = 100  # the video's f100 runs
    initial_creatures: int | None = None  # None -> floor(food_count / 5)

    # -- creature ----------------------------------------------------------
    starting_energy: float = 800.0  # STARTING_ENERGY
    base_sense_distance: float = 25.0  # BASE_SENSE_DISTANCE
    eat_distance: float = 10.0  # EAT_DISTANCE
    predator_size_ratio: float = 1.2  # PREDATOR_SIZE_RATIO
    speed_adjust_factor: float = 1.0  # SPEED_ADJUST_FACTOR
    size_adjust_factor: float = 1.0  # SIZE_ADJUST_FACTOR
    homebound_ratio: float = 2.0  # HOMEBOUND_RATIO

    # -- movement ----------------------------------------------------------
    heading_target_variation: float = 0.4  # HEADING_TARGET_VARIATION (radians)
    max_turn_speed: float = 0.07  # MAX_TURN_SPEED
    turn_acceleration: float = 0.005  # TURN_ACCELERATION
    edge_margin: float = 60.0  # steer back when max(|x|,|y|) + 60 > extent

    # -- mutation ----------------------------------------------------------
    mutation_chance: float = 0.05  # MUTATION_CHANCE, rolled per trait
    mutation_variation: float = 0.1  # MUTATION_VARIATION, delta is exactly +/- this
    mutate_speed: bool = True
    mutate_size: bool = True
    mutate_sense: bool = True

    start_speed: float = 1.0
    start_size: float = 1.0
    start_sense: float = 1.0

    days: int = 50
    seed: int | None = None
    render: bool = True

    # Food can be dropped partway through to reproduce the famine segments.
    famine_day: int | None = None
    famine_food_count: int = 10

    def creature_count(self):
        if self.initial_creatures is not None:
            return self.initial_creatures
        return max(1, int(self.food_count // 5))

    @property
    def max_turn_speed_eff(self):
        return self.max_turn_speed / self.sim_resolution

    @property
    def turn_acceleration_eff(self):
        return self.turn_acceleration / self.sim_resolution
