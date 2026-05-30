# imports
from individual import Individual
from patch import Patch
from simulation import Simulation
import matplotlib.pyplot as plt

# main functions
# parameters are self-explanatory
def main(patches=100, days=100, starting_counts=None, true_mutation_chance=0,
         winner_result=2, loser_result=0, tie_result=1):
    # Stores the interactions between individuals at a patch for all scenarios
    Patch.ratios = {"alone": 2,
              "rs": [winner_result, loser_result],
              "pr": [winner_result, loser_result],
              "sp": [winner_result, loser_result],
              "rp": [loser_result, winner_result],
              "sr": [loser_result, winner_result],
              "ps": [loser_result, winner_result],
              "rr": [tie_result, tie_result],
              "pp": [tie_result, tie_result],
              "ss": [tie_result, tie_result]}

    # initialize sim object
    sim = Simulation(patches)

    # set the max_population and mutation_chance to get simulation started
    max_population = patches * 2
    Individual.mutation_chance = true_mutation_chance

    # check if total starting population is valid
    total_start = sum(starting_counts.values())
    if total_start > max_population:
        print("\nInvalid starting population: greater than max population\n")
        return
    
    # default starting_counts values are 1/10 the number of patches per strategy type
    if starting_counts is None:
        starting_counts = {
        "RRR": patches*0.1,
        "PPP": patches*0.1,
        "SSS": patches*0.1,
        "RPS": patches*0.1,
        "RRP": patches*0.1,
        "RRS": patches*0.1,
        "PPR": patches*0.1,
        "PPS": patches*0.1,
        "SSR": patches*0.1,
        "SSP": patches*0.1,
        }

    # add individuals according to the starting counts
    for strat_str, count in starting_counts.items():
        sim.add_individuals_by_name(strat_str, count)

    print("Simulation running...\nPlease be patient for large numbers\nMay take longer than expected.")

    # get the two plots ready
    fig, axs = plt.subplots(2, 1, figsize=(10, 8))

    # Set titles and labels
    axs[0].set_title("Strategy populations over time")
    axs[0].set_xlabel("Day")
    axs[0].set_ylabel("Number of Individuals")
    
    axs[1].set_title("Total Population over time")
    axs[1].set_xlabel("Day")
    axs[1].set_ylabel("Number of Individuals")
    axs[1].set_ylim(0, max_population)

    # Initialize lines
    strat_lines = {}
    for strat_tuple in sim.strategies:
        strat_name = sim.strategy_map.get(strat_tuple, str(strat_tuple))
        line, = axs[0].plot([], [], label=strat_name)
        strat_lines[strat_tuple] = line
        
    axs[0].legend(loc="upper right")
        
    line_total, = axs[1].plot([], [], color='black', label="Total Population")
    axs[1].legend()

    # simulates the entire time range
    for day in range(1, days + 1):
        # one day of simulation
        sim.simulate_day()

        # Update all strategy populations using strategy names
        for strat_tuple, log in sim.strategy_logs.items():
            days_list = sorted(log.keys())
            counts_list = [log[d] for d in days_list]
            strat_lines[strat_tuple].set_data(days_list, counts_list)

        # Total population plot
        if sim.individuals_on_day:
            days_list = sorted(sim.individuals_on_day.keys())
            counts_list = [sim.individuals_on_day[d] for d in days_list]
            line_total.set_data(days_list, counts_list)

        axs[0].set_xlim(1, max(10, day))
        # update y_lim for upper plot dynamically
        max_y = 0
        for log in sim.strategy_logs.values():
            if log:
                max_y = max(max_y, max(log.values()))
        axs[0].set_ylim(0, max_y + 10)
        axs[1].set_xlim(1, max(10, day))

        # pause between frames for 1 millisecond or whatever the computers max fps is for the animation
        plt.pause(0.001)

    # Print average population per strategy
    print("\nAverage population per strategy:")
    sim.print_population_average()

    # keeps matplotlib window open
    plt.show()

if __name__ == "__main__":
    # all strategies
    all_strategies = [
        "RRR", "PPP", "SSS",    # Only one move
        "RPS",                  # Random
        "RRP", "RRS",           # Heavy Rock
        "PPR", "PPS",           # Heavy Paper
        "SSR", "SSP"            # Heavy Scissors
    ]

    # counts for each strategy
    population_counts = [100 for _ in all_strategies]

    # starting population dictionary for all 10 strategies
    true_starting_counts = {all_strategies[i]: population_counts[i] for i in range(10)}

    # running the main method
    main(patches=1000,
         days=1000, 
         starting_counts=true_starting_counts,
         true_mutation_chance=0.01,
         winner_result=1.8, loser_result=0.2, tie_result=1)