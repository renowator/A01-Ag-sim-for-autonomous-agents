from mesa import Model
from mesa.space import SingleGrid, MultiGrid
from mesa.datacollection import DataCollector
from ag_sim.schedule import ActivePassiveAgentActivation
from ag_sim.agents import ActiveAgent, PassiveAgent, PassiveAgentPerception, ActiveAgentPlanning, FarmAgent
from collections import defaultdict
import numpy

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

    def __init__(self, height, width, model):
        self.navigationGrid = SingleGrid(height, width, False)
        self.planGrid = MultiGrid(height, width, False)
        self.planAgents = defaultdict(list)
        self.perceptionAgents = {}
        self.model = model
        agent = FarmAgent(0, self.model.farmPos, self)
        self.navigationGrid.place_agent(agent, self.model.farmPos)
        self.attendancePoints = list()

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
                existing_agent = self.navigationGrid.get_cell_list_contents(agent.pos)[
                    0]
                existing_agent.update(agent.state, agent.time_at_current_state)

    # This function is used for removing a step from the KnowledgeMap
    def removeOneStep(self, agentID):
        if self.planAgents[agentID]:
            self.planGrid.remove_agent(self.planAgents[agentID].pop(0))

    # This function is used for canceling the entire plan in case a collision is detected
    def cancelPlan(self, agentID):
        while len(self.planAgents[agentID]) > 0:
            self.planGrid.remove_agent(self.planAgents[agentID].pop(0))
    '''
    *** getGridStateAtStep returns a SingleGrid object with anticipated state of the grid at specified steps
        Input:
              - step for which the SingleGrid should be generated
        Output:
              - SingleGrid object with PassiveAgentPerception objects and ActiveAgentPlanning objects corresponding to chosen step
    '''

    def getGridStateAtStep(self, step=0):
        plan_agent_keys = [uid for uid, a in self.planAgents.items()]
        perception_agent_keys = [uid for uid,
                                 a in self.perceptionAgents.items()]
        navGridAtStep = SingleGrid(
            self.navigationGrid.height, self.navigationGrid.width, False)
        for key in perception_agent_keys:
            navGridAtStep.place_agent(
                self.perceptionAgents[key], self.perceptionAgents[key].pos)
        for key in plan_agent_keys:
            for agent in self.planAgents[key]:
                if agent.steps_left == step and navGridAtStep.is_cell_empty(agent.pos):
                    navGridAtStep.place_agent(agent, agent.pos)
        return navGridAtStep

    # This function is used to get a numpy array containing 0 and 1;
    # 0 for empty blocks at step X
    # 1 for any kind of agent at step X
    def getGridAtStepAsNumpyArray(self, step=0):
        plan_agent_keys = [uid for uid, a in self.planAgents.items()]
        perception_agent_keys = [uid for uid,
                                 a in self.perceptionAgents.items()]
        return_numpy_array = numpy.zeros(
            (self.navigationGrid.width, self.navigationGrid.height), dtype='int8')
        for key in perception_agent_keys:
            return_numpy_array[self.perceptionAgents[key].pos[1],
                               self.perceptionAgents[key].pos[0]] = 1
        for agent_key in self.planAgents:
            agent_plans = self.planAgents[agent_key]
            if len(agent_plans) > 0 and len(agent_plans) >= step:
                for plan in agent_plans:
                    if plan.steps_left == step:
                        return_numpy_array[plan.pos[1], plan.pos[0]] = 1
            elif len(agent_plans) == 0:
                active_agent = self.model.schedule.getPassiveAgent(agent_key)
                return_numpy_array[active_agent.pos[1],
                                   active_agent.pos[0]] = 1
            else:
                return_numpy_array[agent_plans[-1].pos[1],
                                   agent_plans[-1].pos[0]] = 1
        return_numpy_array[self.model.farmPos[1], self.model.farmPos[0]] = 1
        return return_numpy_array


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
    description = (
        "A model for simulating agricultural activity of autonomous robots")
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

    def __init__(self, height=50, width=50, **model_params):
        super().__init__()

        # Set a shut off condition (used with the BatchRunner to run multiple experiments)
        self.running = model_params.get("running_condition", True)

        # Initialize the model's variables that measure performance
        self.harvest_score = 0
        self.total_steps_dehydrated = 0
        self.total_steps_sick = 0
        self.total_steps_weeds = 0

        # Set all model parameters from **model_params;
        # second value is the default for when the requested parameter is not set
        self.active_agents = model_params.get("active_agents", 1)
        self.farmPos = (47, 48)
        # Create the schedule
        self.schedule = ActivePassiveAgentActivation(self)

        # Create the single grid on which everything happens
        self.height = height
        self.width = width
        self.grid = MultiGrid(self.height, self.width, False)

        # Specify the data that has to be collected during the run
        self.datacollector = DataCollector(
            model_reporters={
                "harvest_score": self.get_harvest_score,
                "total_steps_dehydrated": self.get_total_steps_dehydrated,
                "total_steps_sick": self.get_total_steps_sick,
                "total_steps_weeds": self.get_total_steps_weeds
            },
            agent_reporters={
                "X": lambda a: a.pos[0],
                "Y": lambda a: a.pos[1]
            }
        )

        # TODO: Create and object to serve as common knowledge base for active agents
        self.knowledgeMap = AgentKnowledgeMap(self.height, self.width, self)

        # TODO: Agents need to be created and added to the schedule here
        # Add the active agents (farming robots)
        for i in range(self.active_agents):
            agent = ActiveAgent(self.next_id(), (0, i), self, **model_params)
            self.grid.place_agent(agent, (48, 48-i))
            self.schedule.add(agent)

        # Add the passive agents (land, crops)
        for n in range(1, int(self.width/2) - 1):
            for j in range(self.height-2):
                agent = PassiveAgent(
                    self.next_id(), (n*2 - 1, j+1), self, **model_params)
                self.grid.place_agent(agent, (n*2 - 1, j+1))
                self.knowledgeMap.update(PassiveAgentPerception(agent))
                self.schedule.add(agent)

        # Add the farm agent
        agent = FarmAgent(self.next_id(), self.farmPos, self)
        self.farmObject = agent
        self.grid.place_agent(agent, self.farmPos)
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

        # Test prints
        # print("Harvest score = " + str(self.harvest_score))
        # print("Time dehydrated = " + str(self.total_steps_dehydrated))
        # print("Time sick = " + str(self.total_steps_sick))
        # print("Time weeds = " + str(self.total_steps_weeds))

    # Functions for harvest score

    def increase_harvest_score(self):
        self.harvest_score += 1

    def get_harvest_score(self, model):
        return model.harvest_score

    # Functions for total steps dehydrated

    def increase_total_steps_dehydrated(self, steps):
        self.total_steps_dehydrated += steps

    def get_total_steps_dehydrated(self, model):
        return model.total_steps_dehydrated

    # Functions for total steps sick

    def increase_total_steps_sick(self, steps):
        self.total_steps_sick += steps

    def get_total_steps_sick(self, model):
        return model.total_steps_sick

    # Functions for total steps weeds

    def increase_total_steps_weeds(self, steps):
        self.total_steps_weeds += steps

    def get_total_steps_weeds(self, model):
        return model.total_steps_weeds

    '''
    *** run_model defines the end condition for simulation and overwrites Model.run_model
    '''

    def run_model(self, step_count=4800):
        for i in range(step_count):
            if i % 100 == 0:
                print("Step " + str(i))
            self.step()
