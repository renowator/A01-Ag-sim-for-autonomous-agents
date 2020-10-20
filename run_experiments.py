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



'''
Function set_variable_params sets all the model parameters that have to be varied in the experiments. 
Change these parameters to perform different experiments.
'''
def set_variable_params():
    variable_params = {
    "active_agents" : range(1,5,1)
    }
    return variable_params


'''
Function set_fixed_params sets all the fixed model parameters for the experiments. 
Parameters are only set here if they have not been set as a variable parameter.
'''
def set_fixed_params():
    fixed_params = {
    # General parameters
    "running_condition" : True,                 # Condition for when the model should be shut of (True = no condition)
    # "active_agents": 10,                       # Number of active agents ("farming robots")
    "com_protocol": "Helper-Based protocol",   # Cooperation protocol used between agents
    "water_threshold": 20,            # Threshold below which crops start drying out [1-100]

    # Seed crop parameters
    "seed_sick_probability": 0.01,
    "seed_weeds_probability": 0.01,
    "steps_seed_to_growing": 100,

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
                        max_steps=100,
                        model_reporters={"harvest_score": get_harvest_score},
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
