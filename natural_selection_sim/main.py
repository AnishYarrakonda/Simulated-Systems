from creature import Creature
from environment import Environment
import matplotlib.pyplot as plt

def main(days=100,
         edge_length=30,
         food_spawn_rate=0.2,
         creature_total=None,
         average_size=1,
         average_speed=1,
         average_vision=1,
         average_trait_variability=0.25,
         ticks_per_day=20,
         true_vision_accuracy = 0.25):

    Creature.vision_accuracy = true_vision_accuracy
    Creature.distribution_rate = average_trait_variability
    
    environment = Environment(edge_length=edge_length,
                              food_spawn_rate=food_spawn_rate,
                              creature_total=creature_total,
                              average_size=average_size,
                              average_speed=average_speed,
                              average_vision=average_vision,
                              average_trait_variability=average_trait_variability,
                              ticks_per_day=ticks_per_day)

    # Set up plotting
    fig = plt.figure(figsize=(14, 7))
    gs = fig.add_gridspec(2, 2, width_ratios=[3, 2])

    # Left side: 3D scatterplot of creature traits
    ax3d = fig.add_subplot(gs[:, 0], projection='3d')
    ax3d.set_xlim(1, 8)
    ax3d.set_ylim(1, 8)
    ax3d.set_zlim(1, 8)
    ax3d.set_xlabel("Size")
    ax3d.set_ylabel("Speed")
    ax3d.set_zlabel("Vision")
    ax3d.set_title("Creature Trait Distribution")

    # Top-right: Trait averages over time
    ax_traits = fig.add_subplot(gs[0, 1])
    ax_traits.set_title("Average Trait Values Over Time")
    trait_lines = {
        "size": ax_traits.plot([], [], label="Size", color='red')[0],
        "speed": ax_traits.plot([], [], label="Speed", color='blue')[0],
        "vision": ax_traits.plot([], [], label="Vision", color='green')[0],
    }
    ax_traits.legend()
    ax_traits.set_ylim(1, 8)

    # Bottom-right: Population over time
    ax_pop = fig.add_subplot(gs[1, 1])
    ax_pop.set_title("Population Over Time")
    pop_line, = ax_pop.plot([], [], label="Population", color='black')
    ax_pop.legend()

    plt.tight_layout()

    for _ in range(days):
        environment.simulate_day()

        # Update 3D trait scatter
        ax3d.cla()
        ax3d.set_xlim(1, 8)
        ax3d.set_ylim(1, 8)
        ax3d.set_zlim(1, 8)
        ax3d.set_xlabel("Size")
        ax3d.set_ylabel("Speed")
        ax3d.set_zlabel("Vision")
        ax3d.set_title("Creature Trait Distribution")

        sizes = [c.size for c in environment.creatures]
        speeds = [c.speed for c in environment.creatures]
        visions = [c.vision for c in environment.creatures]
        ax3d.scatter(sizes, speeds, visions, c='green', s=15, alpha=0.6)

        # Update trait averages
        days_list = sorted(environment.day_to_averages["size"].keys())
        for trait, line in trait_lines.items():
            y_vals = [environment.day_to_averages[trait][d] for d in days_list]
            line.set_data(days_list, y_vals)
        ax_traits.set_xlim(1, max(10, environment.day))

        # Update population graph
        pop_days = sorted(environment.day_to_population.keys())
        pops = [environment.day_to_population[d] for d in pop_days]
        pop_line.set_data(pop_days, pops)
        ax_pop.set_xlim(1, max(10, environment.day))
        ax_pop.set_ylim(0, max(pops) + 10)

        plt.pause(0.001)

    plt.show()

if __name__ == "__main__":
    main(days=1000,
         food_spawn_rate=0.5,
         creature_total=100,
         edge_length=30,
         ticks_per_day=30,
         true_vision_accuracy=1)

"""
Key Points:
Size relies on encounter frequency. More encounters = greater size and less encounters = less size
Speed relies on the length of a day and also the chance of food spawn. Less time = move faster and More food = Move faster to get more
Vision relies on food scarcity and also time. Less food and time = better vision gets food first.
"""