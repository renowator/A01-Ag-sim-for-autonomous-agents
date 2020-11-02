'''
The file run_without_visuals.py is used in order to quickly run a lot of experiments
with the model.
'''
#%%
# Imports
from collections import defaultdict
from ag_sim.model import AgSimulator
from ag_sim.agents import PassiveAgent, ActiveAgent, PassiveAgentPerception, ActiveAgentPlanning, PassiveAgentStateMachine, FarmAgent
import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
'''
Function set_fixed_params sets all the fixed model parameters for the experiments. 
Parameters are only set here if they have not been set as a variable parameter.
'''
def set_model_params():

    # Quick params for if you want no differences between states
    steps_between_states = 1000
    max_steps_bad_state = 500
    sick_prob = 0.0005
    weeds_prob = 0.0005

    fixed_params = {
    # General parameters
    "running_condition" : True,                 # Condition for when the model should be shut of (True = no condition)
    "active_agents": 18,                       # Number of active agents ("farming robots")
    "com_protocol": "Simple protocol",   # Cooperation protocol used between agents: Simple protocol, Helper-Based protocol, Coordination Cooperative protocol

    "max_water_level" : 750,
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
model_results = []
def run_experiment(num_iterations, max_steps, exp_number=0):

    # Set this experiment's model parameters and create the model
    model_params = set_model_params()

    # Perform all iterations
    for i in range(num_iterations):
        print("**************** ITERATION " + str(i) + " of EXP " + str(exp_number) + " ****************")

        model = AgSimulator(**model_params)
        model.run_model(max_steps) # Run the model for at most max_steps

        agent_coords = model.datacollector.get_agent_vars_dataframe()
        model_results.append(model.datacollector.get_model_vars_dataframe())

    # TODO: Return the collected data from this experiment
    return model_results



# Use the line below to run a single experiment
output = run_experiment(10, 6500) #comment this out when loading a outfile_ file to only plot.

#you have to use these two line or it given an error 
np.save('outfile', output)
output1 =  np.load('outfile.npy') # there are 3 outfile_ files for the three protocols which you can load


results = [[0 for i in range(4)] for j in range(6500)]
for i in range(10):
    for j in range(6500):
        if j == 0:
            pass
        else:
            results[j][0] = results[j][0] + output1[i][j][0]
            results[j][1] = results[j][1] + output1[i][j][1]
            results[j][2] = results[j][2] + output1[i][j][2]
            results[j][3] = results[j][3] + output1[i][j][3]

for i in range(4):
    for j in range(6500):
        results[j][i] = results[j][i]/10

df = pd.DataFrame(data=results,  columns=["Harvest_score", "Steps_dehydrated","Steps_sick", "Steps_weed"])

df.to_pickle('simple_18')

df.plot()	
plt.show()



#%%


# Use the line below to run multiple experiments
# run_multiple_experiments()

#%%