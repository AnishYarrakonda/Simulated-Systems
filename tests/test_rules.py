"""Rule checks against Primer's published source.

These pin the details that are easy to get subtly wrong and that quietly break
the result rather than raising -- the energy exponents, the 1.2x predation
threshold, the tree allocation, and the two independent survival rolls.
"""

import os
import random
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# Each sim keeps its own config.py / individual.py / patch.py / simulation.py and
# imports them by bare name, which is fine when you run one sim from its folder
# but means the module cache would serve whichever sim imported first. So load
# each sim from a clean slate.
_SHARED_NAMES = ("config", "creature", "environment", "individual", "patch", "simulation")


def _load(sim_dir, names):
    import importlib

    for name in _SHARED_NAMES:
        sys.modules.pop(name, None)
    path = os.path.join(ROOT, sim_dir)
    sys.path.insert(0, path)
    try:
        return tuple(importlib.import_module(n) for n in names)
    finally:
        sys.path.remove(path)


# ---------------------------------------------------------------- natural selection
def _ns():
    return _load("natural_selection_sim", ("config", "creature", "environment"))


def test_energy_cost_is_size_cubed_times_speed_squared_plus_sense():
    ns_config, ns_creature, _ = _ns()
    c = ns_creature.Creature(ns_config.Config(), size=2, speed=3, sense=1)
    assert c.energy_cost == 2**3 * 3**2 + 1 == 73


def test_energy_cost_scales_with_sim_resolution():
    ns_config, ns_creature, _ = _ns()
    cfg = ns_config.Config(sim_resolution=2)
    c = ns_creature.Creature(cfg, size=2, speed=3, sense=1)
    assert c.energy_cost == 73 / 2


def test_sense_radius():
    ns_config, ns_creature, _ = _ns()
    cfg = ns_config.Config()
    c = ns_creature.Creature(cfg, sense=2.0)
    assert c.sense_radius == 10 + 25 * 2.0  # EAT_DISTANCE + BASE_SENSE_DISTANCE * sense


def test_creature_count_defaults_to_food_over_five():
    ns_config, _, _ = _ns()
    assert ns_config.Config(food_count=100).creature_count() == 20


def test_mutation_delta_is_exactly_plus_or_minus_variation():
    ns_config, ns_creature, _ = _ns()
    cfg = ns_config.Config(mutation_chance=1.0)  # always mutate
    parent = ns_creature.Creature(cfg, size=1.0, speed=1.0, sense=1.0,
                                  rng=random.Random(0))
    deltas = set()
    for _ in range(200):
        child = parent.make_offspring()
        deltas.add(round(child.speed - parent.speed, 6))
    assert deltas == {-0.1, 0.1}, f"expected discrete +/-0.1, got {deltas}"


def test_mutation_switches_are_respected():
    ns_config, ns_creature, _ = _ns()
    cfg = ns_config.Config(mutation_chance=1.0, mutate_size=False, mutate_sense=False)
    parent = ns_creature.Creature(cfg, rng=random.Random(0))
    for _ in range(50):
        child = parent.make_offspring()
        assert child.size == parent.size
        assert child.sense == parent.sense
        assert child.speed != parent.speed


def test_day_length_is_driven_by_the_most_efficient_creature():
    import math

    ns_config, ns_creature, ns_env = _ns()
    cfg = ns_config.Config(seed=0)
    env = ns_env.Environment(cfg)
    env.creatures = [
        ns_creature.Creature(cfg, size=1, speed=1, sense=1),  # cost 2   -> 400 steps
        ns_creature.Creature(cfg, size=2, speed=2, sense=1),  # cost 33  -> 25 steps
    ]
    assert env.day_length() == math.ceil(800 / 2) == 400


@pytest.mark.parametrize(
    "prey_size, predator_size, expected",
    [
        (1.0, 1.2, True),   # exactly at the threshold: edible
        (1.0, 1.19, False),  # just under: safe
        (1.0, 2.0, True),
        (1.0, 1.0, False),  # same size: safe
    ],
)
def test_predation_threshold_is_exactly_1_2x(prey_size, predator_size, expected):
    ns_config, ns_creature, ns_env = _ns()
    cfg = ns_config.Config(seed=0)
    env = ns_env.Environment(cfg)
    predator = ns_creature.Creature(cfg, size=predator_size)
    prey = ns_creature.Creature(cfg, size=prey_size)
    predator.x = predator.y = 0.0
    prey.x, prey.y = 1.0, 0.0
    env.creatures = [predator, prey]
    found, _ = env._nearest_prey(predator)
    assert (found is prey) is expected


def test_prey_is_immune_once_home():
    ns_config, ns_creature, ns_env = _ns()
    cfg = ns_config.Config(seed=0)
    env = ns_env.Environment(cfg)
    predator = ns_creature.Creature(cfg, size=2.0)
    prey = ns_creature.Creature(cfg, size=1.0)
    predator.x = predator.y = prey.y = 0.0
    prey.x = 1.0
    env.creatures = [predator, prey]

    assert env._nearest_prey(predator)[0] is prey
    prey.home = True
    assert env._nearest_prey(predator)[0] is None


def test_eating_caps_at_two_and_transfers_prey_stomach():
    ns_config, ns_creature, ns_env = _ns()
    cfg = ns_config.Config(seed=0)
    env = ns_env.Environment(cfg)
    predator = ns_creature.Creature(cfg, size=2.0)
    prey = ns_creature.Creature(cfg, size=1.0)
    predator.x = predator.y = prey.y = 0.0
    prey.x = 1.0
    prey.eaten = [ns_env.Food(50, 50)]  # prey already ate one
    env.creatures = [predator, prey]
    env.food = []

    env._try_eat(predator)
    assert not prey.alive
    # the prey's food, plus the prey itself, and never more than two
    assert len(predator.eaten) == 2
    assert not predator.can_eat()


def test_reaching_the_edge_without_food_is_not_home():
    ns_config, ns_creature, _ = _ns()
    cfg = ns_config.Config()
    c = ns_creature.Creature(cfg, speed=5.0)
    c.x, c.y, c.heading = 148.0, 0.0, 0.0  # heading straight at the wall
    c.advance()
    assert c.x == 150.0
    assert c.home is False  # ate nothing, so the edge is no refuge

    c2 = ns_creature.Creature(cfg, speed=5.0)
    c2.x, c2.y, c2.heading = 148.0, 0.0, 0.0
    c2.eaten = ["food"]
    c2.advance()
    assert c2.home is True


def test_homebound_latches():
    ns_config, ns_creature, _ = _ns()
    c = ns_creature.Creature(ns_config.Config(), speed=1.0)
    c.x = c.y = 0.0
    c.eaten = ["food"]
    c.state = "homebound"
    c.energy = 1e9  # plenty left, so the trigger would say "keep foraging"
    c.choose_state(predator_near=False)
    assert c.state == "homebound"  # sticky


def test_homebound_triggers_when_energy_runs_short():
    ns_config, ns_creature, _ = _ns()
    cfg = ns_config.Config()
    c = ns_creature.Creature(cfg, size=1, speed=1, sense=1)  # cost 2/step
    c.x = c.y = 0.0  # distance_out = 150
    c.eaten = ["food"]

    c.energy = 800.0  # 400 steps -> 400 > 150*2, keep foraging
    c.choose_state(False)
    assert c.state == "foraging"

    c.state = "foraging"
    c.energy = 200.0  # 100 steps -> 100 < 300, head home
    c.choose_state(False)
    assert c.state == "homebound"


def test_aim_home_targets_nearest_wall():
    import math

    ns_config, ns_creature, _ = _ns()
    c = ns_creature.Creature(ns_config.Config())
    c.x, c.y = 100.0, 0.0  # right wall is closest
    c.aim_home()
    assert c.heading_target == 0.0

    c.x, c.y = 0.0, -100.0  # bottom wall
    c.aim_home()
    assert c.heading_target == -math.pi / 2


# ---------------------------------------------------------------- hawk / dove
def _hd():
    return _load("dove_hawks_sim", ("config", "individual", "patch", "simulation"))


def test_hawk_dove_payoffs_match_primer():
    hd_config, _, _, _ = _hd()
    p = hd_config.Config().payoffs()
    assert p["share_share"] == (1.0, 1.0)
    assert p["fight_share"] == (1.5, 0.5)  # NOT 2/0 -- the dove keeps a quarter
    assert p["fight_fight"] == (0.0, 0.0)  # 2*0.5 - 1.0
    assert p["alone"][0] == 2.0


def test_hawk_dove_contest_outcomes():
    hd_config, hd_individual, hd_patch, _ = _hd()
    cfg = hd_config.Config()

    def contest(fc1, fc2):
        patch = hd_patch.Patch(cfg)
        patch.add(hd_individual.Individual(fc1, cfg, random.Random(0)))
        patch.add(hd_individual.Individual(fc2, cfg, random.Random(0)))
        return patch.resolve()

    assert contest(0, 0)[1:] == (1.0, 1.0)
    assert contest(1, 1)[1:] == (0.0, 0.0)
    assert contest(1, 0)[1:] == (1.5, 0.5)
    assert contest(0, 1)[1:] == (0.5, 1.5)  # order swaps correctly


def test_lone_blob_eats_the_whole_bush():
    hd_config, hd_individual, hd_patch, _ = _hd()
    cfg = hd_config.Config()
    patch = hd_patch.Patch(cfg)
    patch.add(hd_individual.Individual(0.0, cfg, random.Random(0)))
    kind, s1, s2 = patch.resolve()
    assert (kind, s1, s2) == ("alone", 2.0, None)


def test_patch_capacity_is_two():
    hd_config, hd_individual, hd_patch, _ = _hd()
    cfg = hd_config.Config()
    patch = hd_patch.Patch(cfg)
    for _ in range(2):
        patch.add(hd_individual.Individual(0.0, cfg, random.Random(0)))
    with pytest.raises(ValueError):
        patch.add(hd_individual.Individual(0.0, cfg, random.Random(0)))


def test_survival_and_reproduction_rolls_are_independent():
    """Primer draws two random()s. Sharing one correlates the outcomes.

    A score of 1.5 must survive always and reproduce ~50% of the time. With a
    single shared roll, reproduction would instead track the survival draw.
    """
    hd_config, hd_individual, _, _ = _hd()
    cfg = hd_config.Config()
    rng = random.Random(7)
    ind = hd_individual.Individual(1.0, cfg, rng)

    reproduced = 0
    trials = 4000
    for _ in range(trials):
        ind.score = 1.5
        assert ind.survives()  # 1.5 > random() is always true
        reproduced += ind.reproduces()
    assert 0.45 < reproduced / trials < 0.55


def test_score_one_survives_but_never_reproduces():
    hd_config, hd_individual, _, _ = _hd()
    ind = hd_individual.Individual(0.0, hd_config.Config(), random.Random(3))
    for _ in range(500):
        ind.score = 1.0
        assert ind.survives()
        assert not ind.reproduces()


def test_hawk_dove_has_no_population_cap():
    """The old code capped at patches*2, which pins the population artificially."""
    hd_config, _, _, hd_sim = _hd()
    cfg = hd_config.Config(food_count=5, num_creatures=4, days=1, seed=0)
    sim = hd_sim.Simulation(cfg)
    assert not hasattr(sim, "max_population")
    for ind in sim.individuals:
        ind.score = 2.0  # everyone survives and reproduces
    births, deaths = sim.survive_and_reproduce()
    assert (births, deaths) == (4, 0)
    assert len(sim.individuals) == 8 > 2 * cfg.food_count / 2


def test_binary_mutation_flips_the_strategy():
    hd_config, hd_individual, _, _ = _hd()
    cfg = hd_config.Config(mutation_chance=1.0, trait_mode="binary")
    dove = hd_individual.Individual(0.0, cfg, random.Random(0))
    assert dove.make_offspring().fight_chance == 1.0


def test_float_mutation_nudges_and_clamps():
    hd_config, hd_individual, _, _ = _hd()
    cfg = hd_config.Config(mutation_chance=1.0, trait_mode="float")
    ind = hd_individual.Individual(1.0, cfg, random.Random(0))
    for _ in range(100):
        assert 0.0 <= ind.make_offspring().fight_chance <= 1.0


# ---------------------------------------------------------------- rock/paper/scissors
def _rps():
    return _load("rps_sim", ("config", "individual", "simulation"))


def test_rps_reward_matrix():
    rps_config, _, _ = _rps()
    m = rps_config.Config(win_magnitude=1.0, tie_cost=0.5).reward_matrix()
    rock, paper, scissors = 0, 1, 2
    assert m[rock][scissors] == 2.0  # rock beats scissors
    assert m[rock][paper] == 0.0  # rock loses to paper
    assert m[rock][rock] == 0.5  # tie pays 1 - tie_cost
    assert m[paper][rock] == 2.0
    assert m[scissors][paper] == 2.0


@pytest.mark.parametrize(
    "n, trees, pairs, alone, starved",
    [
        (50, 100, 0, 50, 0),    # N <= T: everyone eats alone and doubles
        (100, 100, 0, 100, 0),  # N == T: still all alone
        (150, 100, 50, 50, 0),  # T < N < 2T: mixed, all trees used
        (200, 100, 100, 0, 0),  # N == 2T: all paired
        (250, 100, 100, 0, 50),  # N > 2T: the surplus starves
    ],
)
def test_rps_tree_allocation(n, trees, pairs, alone, starved):
    rps_config, _, rps_sim = _rps()
    cfg = rps_config.Config(initial_blob_count=n, num_trees=trees, seed=0)
    sim = rps_sim.Simulation(cfg)
    contests, starved_list = sim.assign()
    got_pairs = sum(1 for t in contests if t.individual2 is not None)
    got_alone = sum(1 for t in contests if t.individual1 and t.individual2 is None)
    assert (got_pairs, got_alone, len(starved_list)) == (pairs, alone, starved)
    assert got_pairs * 2 + got_alone + len(starved_list) == n  # nobody vanishes


def test_reward_is_expected_offspring_count():
    rps_config, rps_individual, _ = _rps()
    cfg = rps_config.Config()
    ind = rps_individual.Individual([0], cfg, random.Random(1))

    ind.reward = 2.0
    assert all(ind.offspring_count() == 2 for _ in range(50))

    ind.reward = 0.0
    assert all(ind.offspring_count() == 0 for _ in range(50))

    ind.reward = 0.5
    counts = [ind.offspring_count() for _ in range(4000)]
    assert set(counts) <= {0, 1}
    assert 0.45 < sum(counts) / len(counts) < 0.55


def test_generations_do_not_overlap():
    rps_config, _, rps_sim = _rps()
    cfg = rps_config.Config(initial_blob_count=40, num_trees=40, num_days=1, seed=0)
    sim = rps_sim.Simulation(cfg)
    parents = {id(i) for i in sim.individuals}
    sim.simulate_day()
    assert not parents & {id(i) for i in sim.individuals}  # every parent replaced
    assert len(sim.individuals) == 80  # N == T -> all eat alone -> all double


def test_allele_mutation_shifts_within_three():
    rps_config, rps_individual, _ = _rps()
    cfg = rps_config.Config(mutation_rate=1.0)
    ind = rps_individual.Individual([0], cfg, random.Random(0))
    seen = {ind.make_offspring().strategies[0] for _ in range(200)}
    assert seen == {1, 2}  # always shifts away from rock, never stays


def test_pure_blob_plays_only_its_allele():
    rps_config, rps_individual, _ = _rps()
    ind = rps_individual.Individual([1], rps_config.Config(), random.Random(0))
    assert {ind.play() for _ in range(100)} == {1}
