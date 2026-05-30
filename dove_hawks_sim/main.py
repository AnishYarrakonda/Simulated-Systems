from individual import Individual
from simulation import Simulation

import random
import matplotlib.pyplot as plt

# Requires the number of patches, days, starting doves, and starting hawks to be passed
def main(patches, days, doves, hawks):
    # create a new simulation
    sim = Simulation(patches)

    # number of days it runs for
    days_to_simulate = days

    # Initialize the simulation with x doves and y hawks
    initial_doves = doves
    initial_hawks = hawks
    total = initial_doves + initial_hawks

    # Cap total population to patches * 2
    max_total = patches * 2

    # for invalid input
    if total > max_total:
        scale_factor = max_total / total
        initial_doves = int(initial_doves * scale_factor)
        initial_hawks = int(initial_hawks * scale_factor)

        # Ensure the total doesn't go under due to rounding
        while initial_doves + initial_hawks < max_total:
            random1 = random.random()
            if random1 < 0.5:
                initial_doves += 1
            else:
                initial_hawks += 1

    # quickly loop to add all the individuals to the sim
    for _ in range(initial_doves):
        sim.add_individual_to_sim(Individual("Dove", sim))

    for _ in range(initial_hawks):
        sim.add_individual_to_sim(Individual("Hawk", sim))

    # Print out a statement so the user knows its running
    print("Simulation running...\nPlease be patient for large numbers\nMay take longer than expected.")

    # Create the figures to be plotted on
    fig, axs = plt.subplots(2)

    axs[0].set_title("Doves vs. Hawks")
    axs[1].set_title("Total Population")
    axs[0].set_xlabel("Days")
    axs[1].set_xlabel("Days")
    axs[0].set_ylabel("Number of Individuals")
    axs[1].set_ylabel("Number of Individuals")
    axs[0].set_ylim(0, patches * 2)
    axs[1].set_ylim(0, patches * 2)

    # Initialize lines
    line_doves, = axs[0].plot([], [], color="teal", label="Doves")
    line_hawks, = axs[0].plot([], [], color="red", label="Hawks")
    line_total, = axs[1].plot([], [], color="black", label="Total Population")

    axs[0].legend()
    axs[1].legend()

    # Simulate the specified number of days
    for day in range(1, days_to_simulate + 1):
        sim.simulate_day()

        days_list = list(sim.doves_on_day.keys())
        doves_list = list(sim.doves_on_day.values())
        hawks_list = list(sim.hawks_on_day.values())
        total_list = list(sim.individuals_on_day.values())

        line_doves.set_data(days_list, doves_list)
        line_hawks.set_data(days_list, hawks_list)
        line_total.set_data(days_list, total_list)

        axs[0].set_xlim(1, max(10, day))
        axs[1].set_xlim(1, max(10, day))

        # pause each iteration for animation
        plt.pause(0.001)

    # keeps window open after animation
    plt.show()

    # After simulation, print population history
    print("\nPopulation history:")
    for day in range(1, days_to_simulate + 1):
        doves = sim.doves_on_day.get(day, 0)
        hawks = sim.hawks_on_day.get(day, 0)
        total = sim.individuals_on_day.get(day, 0)
        print(f"Day {day}: Doves = {doves}, Hawks = {hawks}, Total = {total}")

    # Print out the average population for each category
    print("Average Dove total:")
    sim.print_population_average("Dove")
    print("Average Hawk total:")
    sim.print_population_average("Hawk")
    print("Average total population:")
    sim.print_population_average("Total")


if __name__ == "__main__":
    main(patches=100, days=1000, doves=10, hawks=10)