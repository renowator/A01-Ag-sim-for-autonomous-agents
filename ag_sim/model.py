from mesa import Model
from mesa.space import SingleGrid
from mesa.datacollection import DataCollector
from ag_sim.schedule import ActivePassiveAgentActivation
from ag_sim.agents import ActiveAgent, PassiveAgent

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
        self.schedule = ActivePassiveAgentActivation(self, ["sample_stage"], False, False)
        self.grid = SingleGrid(self.height, self.width, False)
        # TODO: Specify data collection points
        self.datacollector = DataCollector(            agent_reporters={
                "X": lambda a: a.pos[0],
                "Y": lambda a: a.pos[1]
            })
        # TODO: Create and object to serve as common knowledge base for active agents

        # TODO: Agents need to be created and added to the schedule here
        for i in range(self.active_agents):
            agent = ActiveAgent(self.next_id(), (0,i), self )
            self.grid.place_agent(agent, (0,i))
            self.schedule.add(agent)
        for n in range(int(self.width/2) - 1):
            for j in range(self.height-2):
                agent = PassiveAgent(self.next_id(), (n*2 - 1, j+1), self)
                self.grid.place_agent(agent, (n*2 - 1, j+1))
                self.schedule.add(agent)

        self.running = True
        self.datacollector.collect(self)



    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)

    def run_model(self, step_count = 4800):
        for i in range(step_count):
            self.step()
