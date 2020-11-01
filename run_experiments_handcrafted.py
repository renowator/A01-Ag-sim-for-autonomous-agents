'''
The file run_without_visuals.py is used in order to quickly run a lot of experiments
with the model.
'''
#%%
# Imports
from collections import defaultdict
from ag_sim.model import AgSimulator
from ag_sim.agents import PassiveAgent, ActiveAgent, PassiveAgentPerception, ActiveAgentPlanning, PassiveAgentStateMachine, FarmAgent

'''
Function set_fixed_params sets all the fixed model parameters for the experiments. 
Parameters are only set here if they have not been set as a variable parameter.
'''
def set_model_params():

    # Quick params for if you want no differences between states
    steps_between_states = 20
    max_steps_bad_state = 500
    sick_prob = 0.0003
    weeds_prob = 0.0003

    fixed_params = {
    # General parameters
    "running_condition" : True,                 # Condition for when the model should be shut of (True = no condition)
    "active_agents": 24,                       # Number of active agents ("farming robots")
    "com_protocol": "Helper-Based protocol",   # Cooperation protocol used between agents

    "max_water_level" : 50000,
    "max_steps_dehydrated": max_steps_bad_state,
    "max_steps_sick" : max_steps_bad_state,
    "max_steps_weeds" : max_steps_bad_state,

    # Seed crop parameters
    "seed_sick_probability": sick_prob,
    "seed_weeds_probability": weeds_prob,
    "steps_seed_to_growing": steps_between_states,

    # Growing crop parameters
    "growing_sick_probability" : sick_prob,
    "growing_weeds_probability" : weeds_prob,
    "steps_growing_to_flowering": steps_between_states,

    # Flowering crop parameters
    "flowering_sick_probability" : sick_prob,
    "flowering_weeds_probability": weeds_prob,
    "steps_flowering_to_harvestable": steps_between_states,
    
    # Harvestable crop parameters
    "harvestable_sick_probability": sick_prob,
    "harvestable_weeds_probability": weeds_prob,
    "steps_harvestable_to_dead" : max_steps_bad_state,
    }
    return fixed_params

'''
Function run_experiment runs a single experiment for a given number of iterations
'''
def run_experiment(num_iterations, max_steps, exp_number=0):

    # Set this experiment's model parameters and create the model
    model_params = set_model_params()

    # Perform all iterations
    for i in range(num_iterations):
        print("**************** ITERATION " + str(i) + " of EXP " + str(exp_number) + " ****************")

        model = AgSimulator(**model_params)
        model.run_model(max_steps) # Run the model for at most max_steps

        agent_coords = model.datacollector.get_agent_vars_dataframe()
        model_results = model.datacollector.get_model_vars_dataframe()
        print(model_results)

    # TODO: Return the collected data from this experiment
    return

# Use the line below to run a single experiment
run_experiment(1, 1000)
#%%


# Use the line below to run multiple experiments
# run_multiple_experiments()

#%%