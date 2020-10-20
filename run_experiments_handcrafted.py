'''
The file run_without_visuals.py is used in order to quickly run a lot of experiments
with the model.
'''
# Imports
from collections import defaultdict
from ag_sim.model import AgSimulator
from ag_sim.agents import PassiveAgent, ActiveAgent, PassiveAgentPerception, ActiveAgentPlanning, PassiveAgentStateMachine, FarmAgent

'''
Function set_model_params sets all the model parameters. Change these parameters to perform different experiments.
'''
def set_model_params():
    model_params = {
    # General parameters
    "active_agents": 10,                        # Number of active agents ("farming robots")
    "com_protocol": "Helper-Based protocol",    # Cooperation protocol used between agents
    "water_threshold": 20,                      # Threshold below which crops start drying out [1-100]

    # Baby crop parameters
    "baby_sick_probability": 0.01,
    "baby_weeds_probability": 0.01,
    "steps_baby_to_growing": 100,

    # Growing crop parameters
    "growing_sick_probability" : 0.01,
    "growing_weeds_probability" : 0.01,
    "steps_growing_to_flowering": 100,

    # Flowering crop parameters
    "flowering_sick_probability" : 0.01,
    "flowering_weeds_probability": 0.01,
    "steps_flowering_to_harvestable": 100,
    
    # Harvestable crop parameters
    "harvestable_sick_probability": 0.01,
    "harvestable_weeds_probability": 0.01,
    }
    return model_params

'''
Function run_experiment runs a single experiment
'''
def run_experiment(num_runs, max_steps, exp_number=0):

    # Set this experiment's model parameters
    model_params = set_model_params()

    # Create a new model with the model parameters
    model = AgSimulator(**model_params)

    # Perform all runs
    for run in range(num_runs):
        print("**************** RUN " + str(run) + " of EXP " + str(exp_number) + " ****************")
        model.run_model(max_steps) # Run the model for at most max_steps
        # TODO: Partially reset the model so that all agents are in their starting state

        agent_coords = model.datacollector.get_agent_vars_dataframe()
        plt = agent_coords.plot()
        plt.show()

    # TODO: Return the collected data from this experiment
    return


'''
Function run_multiple_experiments runs multiple experiments by calling the run_experiment function
'''
def run_multiple_experiments():
    # Number of times this experiment has to be performed 
    # TODO: Make sure that results are averaged over this number of experiments
    num_experiments = 2
    # Number of runs in each experiment. Run = Until all crops are harvested or dead, or the max. number of steps is reached
    num_runs = 2
    # Number of steps after which a run is terminated
    max_steps = 6

    for exp in range(num_experiments):
        print("**************** STARTED RUNNING EXPERIMENT " + str(exp) + " ****************")
        run_experiment(num_runs, max_steps, exp)


# Use the line below to run a single experiment
run_experiment(1, 5)

# Use the line below to run multiple experiments
# run_multiple_experiments()