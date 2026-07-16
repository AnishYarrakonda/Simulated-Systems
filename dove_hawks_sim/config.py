"""Tunable parameters for the hawk/dove sim.

Defaults are Primer's, from hawk_dove.py in Helpsypoo/primerpython.
"""

from dataclasses import dataclass


@dataclass
class Config:
    # -- Primer's constants ------------------------------------------------
    num_creatures: int = 121  # DEFAULT_NUM_CREATURES
    food_count: int = 61  # World(food_count=61) -> 122 slots, so one blob eats alone
    food_value: float = 2.0  # FOOD_VALUE: one bush feeds two
    base_food: float = 0.0  # BASE_FOOD

    share_fraction: float = 1 / 2  # SHARE_FRACTION
    hawk_take_fraction: float = 3 / 4  # HAWK_TAKE_FRACTION
    sucker_fraction: float = 1 / 4  # SUCKER_FRACTION
    fight_fraction: float = 1 / 2  # FIGHT_FRACTION
    fight_cost: float = 16 / 16  # FIGHT_COST = 1.0

    mutation_chance: float = 0.0  # MUTATION_CHANCE (off for the main demo)
    mutation_variation: float = 0.1  # MUTATION_VARIATION (float mode only)
    trait_mode: str = "binary"  # TRAIT_MODE: 'binary' or 'float'

    days: int = 50
    seed: int | None = None

    # -- initial mix -------------------------------------------------------
    # None => Primer's `fight_chance = i % 2` seeding (~50/50, so 61 doves / 60 hawks).
    # Set both to reproduce his skewed demos, e.g. doves=10, hawks=150.
    doves: int | None = None
    hawks: int | None = None

    render: bool = True

    def payoffs(self):
        """The four outcomes, in food units. Verified against hawk_dove.py."""
        v = self.food_value
        return {
            "share_share": (v * self.share_fraction, v * self.share_fraction),
            "fight_share": (v * self.hawk_take_fraction, v * self.sucker_fraction),
            "fight_fight": (
                v * self.fight_fraction - self.fight_cost,
                v * self.fight_fraction - self.fight_cost,
            ),
            "alone": (v + self.base_food, 0.0),
        }
