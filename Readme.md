#  Agriculture processes simulation for autonomous agents

## Design of Multi Agent Systems - University of Groningen Fall 2020

### Contributors:
    

        Jussi Boersma (s2779153)
        Nicholas Stepanov (s4422503)
        Cosmin Roger Harsulescu (s3190722)
        Boris Winter (s2774291)
  

## Summary


Autonomous Systems are actively used in modern farming. This project will simulate the behavior of robotic agents in agriculture on various pieces of land. One aspect this project will focus on will be communication and shared rewarding protocols which aim at optimizing the overall performance of autonomous farming agents. Various setups will be investigated and the results of simulation will be reported in this paper. We would further investigate the influence of communication and shared rewarding protocols on the optimal number of agents in an environment with regard to type of agriculture and size of land.


## Installation

To install the dependencies use pip and the requirements.txt in this directory. 

```
    $ pip install -r requirements.txt
```

## How to Run

You can use python to execute ``run.py`` script

```
    $ python ./run.py
```

Then open your browser to [http://127.0.0.1:8521/](http://127.0.0.1:8521/) and press Reset, then Run.

## Folder/Files content

* ag_sim
    * **agents.py** - contains every aspect of the modeled agents
    * **model.py** - contains the model code
    * **schedule.py** - contains the MESA schedule
    * **server.py** - contains the server core code
* plot_data - contains the data used for the plots in the report
* **astar.py** - the A* algorithm, adapted to MESA
* **plotter.py** - function used to plot all the figures from the report
* **run.py** - run this file if you want to run the simulation
* **run_experiments.py** and **run_experiments_handcrafted.py** - are used for running the models for a number of epochs, given some parameters (much faster than running through run.py)