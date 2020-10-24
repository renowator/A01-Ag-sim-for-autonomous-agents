#%%
'''
The file run_experiments.py is used in order to quickly run a lot of experiments
with the model.
'''
# Imports
from collections import defaultdict
from ag_sim.model import AgSimulator
from ag_sim.agents import PassiveAgent, ActiveAgent, PassiveAgentPerception, ActiveAgentPlanning, PassiveAgentStateMachine, FarmAgent
from mesa.datacollection import DataCollector
from mesa.batchrunner import BatchRunner

import matplotlib.pyplot as plt


'''
*** The get_harvest_score function returns the current harvest score of the model.
'''
def get_harvest_score(model):
    return model.harvest_score

def compute_harvest_score(model):
    agent_states = [agent.machine.current_state for agent in model.schedule._agents]
    harvest_score = 0
    for state in agent_states:
        if state == "harvested":
            harvest_score += 1
    return harvest_score



'''
Function set_variable_params sets all the model parameters that have to be varied in the experiments. 
Change these parameters to perform different experiments.
'''
def set_variable_params():
    variable_params = {
    "active_agents" : range(1,2,1)
    }
    return variable_params


'''
Function set_fixed_params sets all the fixed model parameters for the experiments. 
Parameters are only set here if they have not been set as a variable parameter.
'''
def set_fixed_params():

    # Quick params for if you want no differences between states
    steps_between_states = 1000
    max_steps_bad_state = 500
    sick_prob = 0.0003
    weeds_prob = 0.0003

    fixed_params = {
    # General parameters
    "running_condition" : True,                 # Condition for when the model should be shut of (True = no condition)
    # "active_agents": 10,                       # Number of active agents ("farming robots")
    "com_protocol": "Helper-Based protocol",   # Cooperation protocol used between agents

    "max_water_level" : steps_between_states,
    "max_steps_dehydrated": max_steps_bad_state,            # Threshold below which crops start drying out [1-100]
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
    "steps_harvestable_to_dead" : steps_between_states,
    }
    return fixed_params



# Set all parameters that have to be varied in the experiments
variable_params = set_variable_params()

# Set all parameters that are not varied and thus fixed for all experiments
fixed_params = set_fixed_params()

# Prepare the batch of experiments
batch_run = BatchRunner(AgSimulator,
                        variable_params,
                        fixed_params,
                        iterations=1,
                        max_steps=1000,
                        model_reporters={
                            "harvest_score": get_harvest_score,
                            # "computed_harvest_score" : compute_harvest_score
                            },
                        agent_reporters={"pos": "pos"}
                        )

# Run the batch of experiments
batch_run.run_all()

#%%
# Get all agent data
agent_data = batch_run.get_agent_vars_dataframe()
print(agent_data.head())

#%%
# Get all model data
model_data = batch_run.get_model_vars_dataframe()
print(model_data.head())



plt.scatter(model_data.active_agents, model_data.harvest_score)


# %%
