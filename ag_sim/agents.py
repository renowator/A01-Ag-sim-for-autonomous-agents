from mesa import Agent
from statemachine import State, StateMachine
import ag_sim.schedule
from queue import PriorityQueue
import astar
from copy import deepcopy

# Heuristic needed for movement cost to the goal
def heuristic(a, b):
    v1 = abs(a[1]-b[1])
    v2 = abs(a[0]-b[0])
    temp = v1+(v2*v2)
    return temp


# Using this function for adding an element in the "queue" at the appropriate position
def prioritizeQueue(queue,element):
    check = 0
    while check == 0:
        length = len(queue)
        if length == 0:
            queue.insert(0,element)
            break
        else:
            while length >= 0:
                length -= 1
                if element[0] > queue[length][0]:
                    queue.insert(length+1, element)
                    check = 1
                    break

        if check == 0:
            queue.insert(0,element)
            break

    return queue

def printMaze(maze):

    for x in range(0,len(maze)):
        for y in range(0,len(maze[x])):
            print(maze[x][y], end = " ")
        print("")



'''
*** PassiveAgentStateMachine to be used by PassiveAgent.
***  - Interact directly through calling transitions
***  - Schematics will be given in the report

*** Each PassiveAgent instance creates its own instance of PassiveAgentStateMachine
*** Transitions are made by the Agents

+++ May incorporate water level and utilize on_'transition' functions
+++ Group states according to various parameters: there are weeds in the grid spot, there is disease in the grid spot;
    Or group by states (baby) (growing) (flowering) (harvest)
'''
class PassiveAgentStateMachine(StateMachine):
    # All Possible states of a soil patch
    # Start
    start = State("start", initial=True)
    # Plowed
    plowed = State("plowed")
    # Baby
    baby = State("baby")
    baby_sick = State("baby_sick")
    baby_weeds = State("baby_weeds")
    # Growing
    growing = State("growing")
    growing_sick = State("growing_sick")
    growing_weeds = State("growing_weeds")
    unhappy_growing = State("unhappy_growing")
    #Flowering
    flowering = State("flowering")
    flowering_sick = State("flowering_sick")
    flowering_weeds = State("flowering_weeds")
    # Harvestable
    harvestable = State("harvestable")
    end = State("end")
    # State groups
    waterable_states = (baby, baby_sick, baby_weeds, growing, growing_sick, growing_weeds, unhappy_growing, flowering, flowering_sick, flowering_weeds)

    # All possible transitions of a soil patch
    # Start state transitions
    plow = start.to(plowed)
    # Plowed state transitions
    sow = plowed.to(baby)
    # Baby state transitions
    sick_baby = baby.to(baby_sick)
    sick_baby_death = baby_sick.to(end)
    sick_baby_recovery = baby_sick.to(baby)
    weeds_baby = baby.to(baby_weeds)
    weeds_baby_recovery = baby_weeds.to(baby)
    weeds_baby_death = baby_weeds.to(end)
    baby_grown = baby.to(growing)
    # Growing state transitions
    sick_growing = growing.to(growing_sick)
    sick_growing_death = growing_sick.to(end)
    sick_growing_recovery = growing_sick.to(growing)
    weeds_growing = growing.to(growing_weeds)
    weeds_growing_recovery = growing_weeds.to(growing)
    weeds_growing_death = growing_weeds.to(end)
    low_nutrition = growing.to(unhappy_growing)
    death_from_low_nutrition = unhappy_growing.to(end)
    growing_to_flowering = growing.to(flowering)
    # Flowering state transitions
    sick_flowering = flowering.to(flowering_sick)
    sick_flowering_death = flowering_sick.to(end)
    sick_flowering_recovery = flowering_sick.to(flowering)
    weeds_flowering = flowering.to(flowering_weeds)
    weeds_flowering_recovery = flowering_weeds.to(flowering)
    weeds_flowering_death = flowering_weeds.to(end)
    # Harvestable state transitions
    flowering_to_harvestable = flowering.to(harvestable)
    harvest = harvestable.to(end)
    # We can add functions for transitions here

'''
*** PassiveAgent implements the agent functionality for a piece of soil in Ag AgSimulator
*** Mesa Agent functionality with StagedActivation (currently a single sample_stage)
*** Interaction function with ActiveAgent defined and called through:
                          PassiveAgent.interact(calling_active_agent)
*** The staged updates only the independent transitions in PassiveObjectStateMachine eg.:
                          - Random element Transitions
                          - Death of the crop due to its states
                          - Developing into next stage if conditions met
+++ May be extended to a particular kind of crop if needed
'''
class PassiveAgent(Agent):
    grid = None
    x = None
    y = None

    '''
    *** Constructor:
        Inputs:
               - unique id for PassiveAgent
               - position of PassiveAgent
               - Inherent model of PassiveAgent (AgSimulator)

        Actions:
                - Call constructor from Agent on unique_id and model
                - Initialize agent_type as 'PASSIVE'
                - Construct and store PassiveAgentStateMachine

    '''
    def __init__(self, unique_id, pos, model, **model_params):
        super().__init__(unique_id, model)
        self.pos = pos
        self.agent_type = 'PASSIVE'
        self.machine = PassiveAgentStateMachine()
        self.time_at_current_state = 0
        self.taken = 0

        # Set passive agent's baby crop parameters
        self.baby_sick_probability = model_params["baby_sick_probability"]
        self.baby_weeds_probability = model_params["baby_weeds_probability"]
        self.steps_baby_to_growing = model_params["steps_baby_to_growing"]

        # Set passive agent's growing crop parameters
        self.growing_sick_probability = model_params["growing_sick_probability"]
        self.growing_weeds_probability = model_params["growing_weeds_probability"]
        self.steps_growing_to_flowering = model_params["steps_growing_to_flowering"]

        # Set passive agent's flowering crop parameters
        self.flowering_sick_probability = model_params["flowering_sick_probability"]
        self.flowering_weeds_probability = model_params["flowering_weeds_probability"]
        self.steps_flowering_to_harvestable = model_params["steps_flowering_to_harvestable"]

        # Set passive agent's harvestable crop parameters
        #  ------> Should they be able to get sick / weeds when harvestable?
        self.harvestable_sick_probability = model_params["harvestable_sick_probability"]
        self.harvestable_weeds_probability = model_params["harvestable_weeds_probability"]

    '''
    *** Main interaction function between ActiveAgent and PassiveAgent
    *** ActiveAgent calls PassiveAgent.interact(calling_active_agent) to change the state of PassiveAgent
    *** switcher dictionary determines which particular function to run depending on ActiveAgent current_tool
    *** Interaction functions defined below (subject to change)
    '''
    def interact(self, agent):
        if (agent.agent_type == 'ACTIVE'):
            switcher = {'PLOW' : self.plow, 'SOW' : self.sow, 'CURE' : self.cure, 'PESTICIDES' : self.kill_weeds,
            'WATERING_TOOL' : self.water, 'HARVESTING_TOOL' : self.harvest}
            func = switcher.get(agent.current_tool, lambda: None)
            if (func is not None):
                func()

    #----------------------------------- Interaction functions for interactions between active and passive agents
    def plow(self):
        if ( self.machine.current_state == self.machine.start):
            self.time_at_current_state = 0
            self.machine.plow()

    def sow(self):
        if ( self.machine.current_state == self.machine.plowed):
            self.time_at_current_state = 0
            self.machine.sow()

    def cure(self):
        # Baby
        if ( self.machine.current_state == self.machine.baby_sick):
            self.time_at_current_state = 0
            self.machine.sick_baby_recovery()
        # growing
        if ( self.machine.current_state == self.machine.growing_sick):
            self.time_at_current_state = 0
            self.machine.sick_growing_recovery()
        # Flowering
        if ( self.machine.current_state == self.machine.flowering_sick):
            self.time_at_current_state = 0
            self.machine.sick_flowering_recovery()

    def kill_weeds(self):
        # Baby
        if ( self.machine.current_state == self.machine.baby_weeds):
            self.time_at_current_state = 0
            self.machine.weeds_baby_recovery()
        # growing
        if ( self.machine.current_state == self.machine.growing_weeds):
            self.time_at_current_state = 0
            self.machine.weeds_growing_recovery()
        # Flowering
        if ( self.machine.current_state == self.machine.flowering_weeds):
            self.time_at_current_state = 0
            self.machine.weeds_flowering_recovery()

    def water(self):
        if ( self.machine.current_state in self.machine.waterable_states):
            return
            #TODO: Add watering effects

    def harvest(self):
        if ( self.machine.current_state == self.machine.harvestable):
            self.time_at_current_state = 0
            self.machine.harvest()
    # ******************               THE INTERACTION FUNCTIONS END HERE             *******************

    '''
    *** sample_Stage is the stage used to debug the model
    *** It will not be used eventually
    *** All the below functionality will be in passive_stage
    *** Indepentent state transitions for PassiveAgents only
    '''
    # Here only elements essential to the plants itself are updated (random growing of weeds or spread of disease, check if enough energy to survive, etc)
    def sample_stage(self):
        self.time_at_current_state += 1
        # TODO: Implement random variability in state transitions
        switcher = {self.machine.baby: self.when_baby, self.machine.growing : self.when_growing, self.machine.flowering : self.when_flowering, self.machine.harvest : self.when_harvestable}
        func = switcher.get(self.machine.current_state,  None)
        if (func is not None):
            func()

    # ---------------------------------------- Independent transitions start here

    '''
    Independent baby state transitions
    '''
    def when_baby(self):
        if (self.time_at_current_state >= self.steps_baby_to_growing):
            self.time_at_current_state = 0
            self.machine.baby_grown()
        elif (self.random.random() < self.baby_sick_probability):
            # self.time_at_current_state = 0 ---> Is this needed?
            self.machine.sick_baby()
        elif (self.random.random() < self.baby_weeds_probability):
            # self.time_at_current_state = 0
            self.machine.weeds_baby()

    '''
    Independent growing state transitions
    '''
    def when_growing(self):
        if (self.time_at_current_state >= self.steps_growing_to_flowering):
            self.time_at_current_state = 0
            self.machine.growing_to_flowering()
        elif (self.random.random() < self.growing_sick_probability):
            # self.time_at_current_state = 0
            self.machine.sick_growing()
        elif (self.random.random() < self.growing_weeds_probability):
            # self.time_at_current_state = 0
            self.machine.weeds_growing()

    def when_flowering(self):
        if (self.time_at_current_state >= self.steps_flowering_to_harvestable):
            self.time_at_current_state = 0
            self.machine.flowering_to_harvestable()
        elif (self.random.random() < self.flowering_sick_probability):
            # self.time_at_current_state = 0
            self.machine.sick_flowering()
        elif (self.random.random() < self.flowering_weeds_probability):
            # self.time_at_current_state = 0
            self.machine.weeds_flowering()

    def when_harvestable(self):
        return
    # ******************               THE INDEPENDENT TRANSITIONS END HERE             *******************

    def returnState(self):
        return self.machine
'''
*** PassiveAgentPerception is used to track PassiveObjects on the AgentKnowledgeMap.navigationGrid
*** Placed on AgentKnowledgeMap.navigationGrid by ActiveAgent instances when they see new objects using:
              - AgentKnowledgeMap.update() is called by ActiveAgent
              IF object at this location does not exist:
                    - Place PassiveObjectPerception on AgentKnowledgeMap.navigationGrid
              ELSE:
                    - PassiveAgentPerception.update() is called by AgentKnowledgeMap.update()
'''
class PassiveAgentPerception(Agent):
    # The perception object will have the unique id same as the actual PassiveObject
    def __init__(self, agent):
        super().__init__(agent.unique_id, agent.model)
        self.pos = agent.pos
        self.taken = 0
        if isinstance(agent, PassiveAgent):
            self.state = agent.machine.current_state
            self.time_at_current_state = agent.time_at_current_state

    def update(self, state = None, time_at_current_state = 0, taken = 0):
        if (state is not None):
            self.state = state
            self.time_at_current_state = time_at_current_state
            self.taken = taken



'''
*** ActiveAgent represents the robotic agent that operates on the farm
*** Currently sample_stage is used to test functionality of the rest of the project

+++ Implement Perception in passive stage
+++ Obtain targets from AgentKnowledgeMap.taskGrid
+++ Attach A* algorithm for finding distance to tasks
+++ Implement Object Sorting Task in passive stage
+++ Record the plan and update AgentKnowledgeMap.navigationGrid in passive stage
+++ Execute the plan and interact with PassiveObjects in active stage

'''
class ActiveAgent(Agent):
    grid = None
    x = None
    y = None


    '''
    *** Constructor:
        Inputs:
               - unique id for ActiveAgent
               - position of ActiveAgent
               - Inherent model of ActiveAgent (AgSimulator)

        Actions:
                - Call constructor from Agent on unique_id and model
                - Initialize agent_type as 'ACTIVE'
                + More functionality to be implemented for decision making and path planning

    '''
    def __init__(self, unique_id, pos, model):
        super().__init__(unique_id, model)
        self.pos = pos
        self.agent_type = 'ACTIVE'
        self.targets = None # target can be watering, plowing, spraying and to gather or return the needed equipment
        self.mode = 'TEST'
        self.current_tool = 'PLOW'
        self.plan = None
        self.target = None # This variable is used when a target location is set by the agent
        self.step = 0
        self.calculationQueue = list()
        self.visitedNodes = list()
        self.goals = list()

    def newPositions(self, pos):
        newPos = list()

        if pos[1]-1 >= 0:
            newPos.append((pos[0],pos[1]-1))

        if pos[1]+1 <= 49:
            newPos.append((pos[0],pos[1]+1))
        
        if pos[0]-1 >= 0:
            newPos.append((pos[0]-1,pos[1]))

        if pos[0]+1 <= 49:
            newPos.append((pos[0]+1,pos[1]))
        return newPos

    def checkState(self, new, maze):
        checked = list()
        for element in new:
            if maze[element[1]][element[0]] == 0 and (element not in self.visitedNodes):
                #print("Element added: ", element, " Maze value: ", maze[element[0]][element[1]])
                checked.append(element)

        return checked

    def addElemToQueue(self,pos,trace):
        if pos:
            for each in pos:
                self.calculationQueue.append((each,trace))

    def BFS(self,step):
        done = 0            
        temp = list()
        if self.calculationQueue:
            # position[0] is the pos of the element popped
            # position[1] is the passive agent associated
            position = self.calculationQueue.pop(0)
            
            # We need a deepcopy otherwise the same variable will be used recursevly
            temp = deepcopy(position[1])
            #print("Temp: ",temp, " Location: ", position[0])

            for element in self.goals:
                if element[0] == position[0] and element[1].taken == 0:
                    self.target = element[1].pos
                    element[1].taken = 1

                    done = 1
                    temp.append(position[0])
                    return temp
            if done == 0:
                self.visitedNodes.append(position[0])
                newPositions = self.newPositions(position[0])
                temp.append(position[0])
                check1 = self.checkState(newPositions, self.model.knowledgeMap.getGridAtStepAsNumpyArray(step))
                check2 = self.checkState(check1, self.model.knowledgeMap.getGridAtStepAsNumpyArray(step+1))
                self.addElemToQueue(check2,temp[0:])
                answer = self.BFS(step+1)
                return answer

            return None

    def update_perception(self, perceptionRadius = 5):
        # Add what the agent sees to the knowledge grid
        neighbors = self.model.grid.get_neighborhood(self.pos, True, False, perceptionRadius)
        for neighbor in neighbors:
            neighbor_obj = self.model.grid.get_cell_list_contents([neighbor])
            if (len(neighbor_obj) > 0):
                if isinstance(neighbor_obj[0], PassiveAgent):
                    self.model.knowledgeMap.update(PassiveAgentPerception(neighbor_obj[0]))


    def executeMove(self):
        my_plans = self.model.knowledgeMap.planAgents[self.unique_id]
        my_plans.sort(key=lambda x: x.steps_left, reverse=False)
        plan_count = len(my_plans)

        if plan_count > 0:
            if self.model.grid.is_cell_empty(my_plans[0].pos):
                self.model.grid.move_agent(self,my_plans[0].pos)
            else:
                print("CELL NOT EMPTY")
    '''
    *** sample_Stage is the stage used to debug the model
    *** It will not be used eventually
    *** All the below functionality will be divided in passive_stage and active_stage
    !!!!              NOTE:: There are some bugs in here
    '''

    def sample_stage(self):

        self.executeMove()
        plan_count = len(self.model.knowledgeMap.planAgents[self.unique_id])
        
        # Add what the agent sees to the knowledge grid
        self.update_perception()

        if self.step == 0:
            self.update_perception
        else:
            if plan_count == 0:
                # If the agent has a target, check if the target is in the neighborhood
                if self.target is not None:
                    neighbors = self.model.grid.get_neighborhood(self.pos, False, False)
                    for neighbor in neighbors:
                        cell = self.model.grid.get_cell_list_contents([neighbor])
                        passive = [obj for obj in cell if isinstance(obj, PassiveAgent)]
                        if len(passive) > 0 and passive[0].pos == self.target:
                            passive[0].interact(self)
                            passive[0].taken = 0
                            self.target = None

                # Get all fields that the agents added in the perception map
                listOfFieldsFromKnowledge = [obj for obj in self.model.knowledgeMap.navigationGrid if isinstance(obj, PassiveAgentPerception)]
                possibleTargets = list()

                # Get all possible points the agent can go based on interest
                for obj in listOfFieldsFromKnowledge:
                    pointOfInterest = self.model.schedule.getPassiveAgent(obj.unique_id)
                    if pointOfInterest.taken == 0 and pointOfInterest.machine.current_state.value == "start":
                        # These are the two possible locations for every field
                        possibleTargets.append(((pointOfInterest.pos[0]-1,pointOfInterest.pos[1]),pointOfInterest))
                        possibleTargets.append(((pointOfInterest.pos[0]+1,pointOfInterest.pos[1]),pointOfInterest))

                        # If there is a top or bottom field, there is also an alternitve point it can go
                        if pointOfInterest.pos[1] == 1:
                            possibleTargets.append(((pointOfInterest.pos[0],0),pointOfInterest))
                        elif pointOfInterest.pos[1] == 48:
                            possibleTargets.append(((pointOfInterest.pos[0],49),pointOfInterest))

                self.goals = possibleTargets
                # Decide which is the closest point you can attend and that is free
                while possibleTargets:

                    # Calculate the shortest path based on agents point and the other possible points
                    self.visitedNodes.append(self.pos)
                    newPossiblePositions = self.newPositions(self.pos)
                    initCheck = self.checkState(newPossiblePositions,self.model.knowledgeMap.getGridAtStepAsNumpyArray(self.step))
                    secondCheck = self.checkState(initCheck,self.model.knowledgeMap.getGridAtStepAsNumpyArray(self.step+1))
                    self.addElemToQueue(secondCheck,[self.pos])
                    steps = self.BFS(self.step)

                    # If there are any steps that the agent can take, add them to the knowledgeMap
                    temp = -1
                    print(steps)
                    if steps:
                        for step in steps:
                            if temp == -1:
                                #Skip the first step
                                temp = temp + 1
                            else:
                                temp = temp + 1
                                new_plan = ActiveAgentPlanning(self, step, temp)
                                self.model.knowledgeMap.update(new_plan)
                                self.model.schedule.add(new_plan)

                    self.calculationQueue.clear()
                    self.visitedNodes.clear()
                    self.goals.clear()
                    self.executeMove()
                    break
        self.step += 1

'''
*** ActiveAgentPlanning is an object which represents a plan of a particular ActiveAgentPlanning
*** Place on AgentKnowledgeMap.planGrid
*** Expires when particular stage is reached through sample_stage -> passive_stage
'''
# This class is used to post agent plan on the AgentKnowledgeMap.planGrid
class ActiveAgentPlanning(Agent):
    # The plan will have a unique id of the agent who made the plan
    def __init__(self, agent, pos, steps = 0):
        super().__init__(agent.unique_id, agent.model)
        self.pos = pos
        self.steps_left = steps

    def sample_stage(self):
        self.steps_left -= 1
        if (self.steps_left < 0):
            self.model.schedule.remove(self)
            self.model.knowledgeMap.planGrid.remove_agent(self)
            self.model.knowledgeMap.planAgents[self.unique_id].remove(self)


# this function should be inserted somewhere, where 'cell' is a neighbouring cell of an active agent
# 'self.' will be the active agent

# if isinstance(cell, FarmAgent) and self.current_tool != None:
#     if self.target == 'get_plow':
#         if cell.interact(self.target, None):
#             self.current_tool = 'plow'
#         else:
#             None #there is no tool available so change plans
#     elif self.target == 'get_irrigator':
#         if cell.interact(self.target, None):
#             self.current_tool = 'irrigator'
#         else:
#             None #there is no tool available so change plans
#     elif self.target == 'get_spray':
#         if cell.interact(self.target, None):
#             self.current_tool = 'spray'
#         else:
#             None #there is no tool available so change plans
#     elif self.target == 'return_tool':
#         cell.interact(self.target, self.current_tool)
#         self.current_tool = None

class FarmAgent(Agent):
    grid = None
    x = None
    y = None

    def __init__(self, unique_id, pos, model):
        super().__init__(unique_id, model)
        self.pos = pos
        self.food = 0
        self.irrigator = 5
        self.plow = 5
        self.spray = 5

    def sample_stage(self):
        return

    def interact(self, target, tool): #for the taking and returning of farm equipment
        if tool != None:
            if tool == 'irrigator':
                self.irrigator += 1
                return True
            elif tool == 'plow':
                self.plow += 1
                return True
            elif tool == 'spray':
                self.spray += 1
                return True
        elif target == 'watering' and self.irrigator > 0:
            self.irrigator -= 1
            return True
        elif target == 'plowing' and self.plow > 0:
            self.plow -= 1
            return True
        elif target == 'spraying' and self.spray > 0:
            self.spray -= 1
            return True
        else:
            return False
