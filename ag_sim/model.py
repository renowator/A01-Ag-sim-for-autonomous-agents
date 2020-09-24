from mesa import Model
from mesa.space import SingleGrid, MultiGrid
from mesa.datacollection import DataCollector
from ag_sim.schedule import ActivePassiveAgentActivation
from ag_sim.agents import ActiveAgent, PassiveAgent, PassiveAgentPerception, ActiveAgentPlanning, FarmAgent
from collections import defaultdict

'''
*** AgentKnowledgeMap is a common knowledge object for ActiveAgents to update during passive_stage
*** AgentKnowledgeMap.navigationGrid:
                                        Tracks all the objects seen by ActiveAgents
*** AgentKnowledgeMap.planGrid:
                                        Tracks the plans for ActiveAgents
+++ AgentKnowledgeMap.targetGrid:
                                        Tracks the targets using AgentKnowledgeMap.navigationGrid


*** AgentKnowledgeMap.getGridStateAtStep(step):
                                         Will return the snticipated state of grid based on planGrid
'''
class AgentKnowledgeMap():
    '''
    *** Constructor:
        Inputs:
               - height and width of the grid used by the AgSimulator

       Actions:
               - Construct navigationGrid
               - Construct planGrid
               + Construct taskGrid
               - Create agent dictionaries
    '''
    def __init__(self, height, width):
        self.navigationGrid = SingleGrid(height, width, False)
        self.planGrid = MultiGrid(height, width, False)
        self.planAgents = defaultdict(list)
        self.perceptionAgents = {}


    '''
    *** update function is used by each ActiveAgent to update ActiveAgentKnowledgeMap
        Input:
              - ActiveAgentPlanning objects are placed on planGrid
              - PassiveAgentPerception objects are placed on navigationGrid
    '''
    def update(self, agent):
        if (isinstance(agent, ActiveAgentPlanning)):
            self.planGrid.place_agent(agent, agent.pos)
            self.planAgents.setdefault(agent.unique_id, [])
            self.planAgents[agent.unique_id].append(agent)
        elif(isinstance(agent, PassiveAgentPerception)):
                if self.navigationGrid.is_cell_empty(agent.pos):
                    self.navigationGrid.place_agent(agent, agent.pos)
                    self.perceptionAgents[agent.unique_id] = agent
                else:
                    existing_agent = self.navigationGrid.get_cell_list_contents(agent.pos)[0]
                    existing_agent.update(agent.state, agent.time_at_current_state)

    '''
    *** getGridStateAtStep returns a SingleGrid object with anticipated state of the grid at specified steps
        Input:
              - step for which the SingleGrid should be generated
        Output:
              - SingleGrid object with PassiveAgentPerception objects and ActiveAgentPlanning objects corresponding to chosen step
    '''
    def getGridStateAtStep(self, step = 0):
        plan_agent_keys = [uid for uid, a in self.planAgents.items()]
        perception_agent_keys = [uid for uid, a in self.perceptionAgents.items()]
        navGridAtStep = SingleGrid(self.navigationGrid.height , self.navigationGrid.width, False)
        for key in perception_agent_keys:
            navGridAtStep.place_agent(self.perceptionAgents[key], self.perceptionAgents[key].pos)
        for key in plan_agent_keys:
            for agent in self.planAgents[key]:
                if agent.steps_left == step and navGridAtStep.is_cell_empty(agent.pos):
                    navGridAtStep.place_agent(agent, agent.pos)
        return navGridAtStep





'''
*** AgSimulator is the main model class for this project
*** Specifies model parameters:
                               - grid size
                               - number of active Agents
                               more to come...
'''
class AgSimulator(Model):
    height = 50
    width = 50
    active_agents = 5
    description = ("A model for simulating agricultural activity of autonomous robots")
    # TODO: Add more parameters to the model

    '''
    *** Constructor:
        Inputs:
               - height and width for the grid
               - number of ActiveAgents to place on the grid

        Actions:
                - Construct and store SingleGrid for Model.grid
                - Construct and store ActivePassiveAgentActivation for Model.schedule
                - Construct and store datacollector
                - Construct and store AgentKnowledgeMap
                - Place Agents on the grid

    '''
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
        self.knowledgeMap = AgentKnowledgeMap(self.height, self.width)
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
        agent = FarmAgent(self.next_id(), (47,48), self) 
        self.grid.place_agent(agent, (47,48))
        self.schedule.add(agent)

        self.running = True
        self.datacollector.collect(self)


    '''
    *** step defines how the model behaves each step and overwrites Model.step
    +++ For more visualization information, it should probably be obtained here
    '''
    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)

    '''
    *** run_model defines the end condition for simulation and overwrites Model.run_model
    '''
    def run_model(self, step_count = 4800):
        for i in range(step_count):
            self.step()
