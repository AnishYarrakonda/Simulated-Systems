"""Tunable parameters for the rock/paper/scissors sim.

Defaults are Primer's, from EvoGameTheorySim.cs in Primer-Learning/RockPaperScissors
(the "Simulating the Evolution of Rock, Paper, Scissors" video, 2024).
"""

from dataclasses import dataclass

ROCK, PAPER, SCISSORS = 0, 1, 2
NAMES = ("Rock", "Paper", "Scissors")


@dataclass
class Config:
    num_days: int = 200
    initial_blob_count: int = 800
    num_trees: int = 400

    mutation_rate: float = 0.001
    num_alleles_per_blob: int = 1  # 1 = pure strategy; 3 = mixed in thirds

    # The knob that shapes the orbit. Paying a cost to tie means a common
    # strategy meets *itself* often and pays for it, which favours rare
    # strategies -- negative frequency dependence, so it stabilises the cycle.
    #
    # Writing the payoffs as C - tie_cost*I (C = zero-sum cyclic RPS) and taking
    # V = x_r*x_p*x_s gives d(ln V)/dt = tie_cost*(3*sum(x^2) - 1) >= 0, and V
    # peaks at the centre. So:
    #   tie_cost > 0 -> V rises -> spirals inward to (1/3, 1/3, 1/3)  [stable]
    #   tie_cost = 0 -> V conserved -> neutral closed orbits (drift eventually
    #                   walks a finite population out to fixation anyway)
    #   tie_cost < 0 -> spirals outward toward the heteroclinic cycle
    # Confirmed empirically at n=3000; see the README.
    win_magnitude: float = 1.0
    tie_cost: float = 0.5

    # None => even split. Primer's FindStability seeds [2, 1, 1] -> 0.5/0.25/0.25.
    initial_allele_frequencies: tuple | None = None

    seed: int | None = 0
    render: bool = True

    def reward_matrix(self):
        """Row = my move, column = opponent's. Straight from RewardMatrix.

        Beating someone pays 1+win_magnitude, losing pays 1-win_magnitude, and a
        tie pays 1-tie_cost. A reward of 1 is break-even (one offspring).
        """
        w, t = self.win_magnitude, self.tie_cost
        return (
            (1 - t, 1 - w, 1 + w),  # Rock: ties rock, loses to paper, beats scissors
            (1 + w, 1 - t, 1 - w),  # Paper: beats rock, ties paper, loses to scissors
            (1 - w, 1 + w, 1 - t),  # Scissors: loses to rock, beats paper, ties scissors
        )
