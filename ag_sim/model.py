from mesa import Model
from mesa.space import SingleGrid
from mesa.datacollection import DataCollector
from ag_sim.schedule import ActivePassiveAgentActivation


class AgSimulator(Model):
    height = 50
    width = 50
    active_agents = 5
    description = ("A model for simulating agricultural activity of autonomous robots")
    # TODO: Add more parameters to the model

    def __init__(self, height = 50, width = 50, active_agents = 5):
        super().__init__()
        self.height = height
        self.width = width
        self.active_agents = active_agents
        self.schedule = ActivePassiveAgentActivation(self)
        self.grid = SingleGrid(self.height, self.width, False)
        # TODO: Specify data collection points
        self.datacollector = DataCollector()
        # TODO: Create and object to serve as common knowledge base for active agents

        # TODO: Agents need to be created and added to the schedule here

        self.running = True
        self.datacollector.collect(self)



    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)

    def run_model(self, step_count = 4800):
        for i in range(step_count):
            self.step()
