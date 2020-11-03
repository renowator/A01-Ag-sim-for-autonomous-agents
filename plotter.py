import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt

#plotter
# simple_df = pd.read_pickle('simple_6')
# print(simple_df)
# hcp_df = pd.read_pickle('hcp_df')
df6 = pd.read_pickle('ccp_6')
df12 = pd.read_pickle('ccp_12')
df18 = pd.read_pickle('ccp_18')
df24 = pd.read_pickle('ccp_24')
df30 = pd.read_pickle('ccp_30')

# df6 = pd.read_pickle('hcp_6')
# df12 = pd.read_pickle('hcp_12')
# df18 = pd.read_pickle('hcp_18')
# df24 = pd.read_pickle('hcp_24')
# df30 = pd.read_pickle('hcp_30')

# df6 = pd.read_pickle('simple_6')
# df12 = pd.read_pickle('simple_12')
# df18 = pd.read_pickle('simple_18')
# df24 = pd.read_pickle('simple_24')
# df30 = pd.read_pickle('simple_30')


data =   [[df6.iloc[6499, 0], df6.iloc[6499, 0]/sum(df6.iloc[6499, 1:4])], 
        [df12.iloc[6499, 0], df6.iloc[6499, 0]/sum(df12.iloc[6499, 1:4])],
        [df18.iloc[6499, 0], df6.iloc[6499, 0]/sum(df18.iloc[6499, 1:4])],
        [df24.iloc[6499, 0], df6.iloc[6499, 0]/sum(df24.iloc[6499, 1:4])],
        [df30.iloc[6499, 0], df6.iloc[6499, 0]/sum(df30.iloc[6499, 1:4])]]

# Create the pandas DataFrame 
df = pd.DataFrame(data, columns = ['Harvest_score', 'Total_unattended'], index = ['6', '12','18', '24','30']) 

# df.plot(kind="bar")

# plt.show()


fig = plt.figure() # Create matplotlib figure

ax = fig.add_subplot(111) # Create matplotlib axes
ax2 = ax.twinx() # Create another axes that shares the same x-axis as ax.

width = 0.4

df.Harvest_score.plot(kind='bar', color='red', ax=ax, width=width, position=1)
df.Total_unattended.plot(kind='bar', color='blue', ax=ax2, width=width, position=0)

ax.set_ylabel('Harvest score')
ax2.set_ylabel('Quality of harvested crops')
ax.set_xlabel('Amount of agents')
ax.set_title('Coordination Cooperation Protocol - Agent Amount Comparison')

plt.show()