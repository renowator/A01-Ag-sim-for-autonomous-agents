from mesa import Agent
from statemachine import State, StateMachine
import ag_sim.schedule
from queue import PriorityQueue
import astar
from copy import deepcopy
from multiprocessing import Pool


def printMaze(maze):

    for x in range(0, len(maze)):
        for y in range(0, len(maze[x])):
            print(maze[x][y], end=" ")
        print("")

# Heuristic needed for movement cost to the goal


def heuristic(a, b):
    v1 = abs(a[1]-b[1])
    v2 = abs(a[0]-b[0])
    temp = v1+(v2*v2)
    return temp


# Using this function for adding an element in the "queue" at the appropriate position
def prioritizeQueue(queue, element):
    check = 0
    while check == 0:
        length = len(queue)
        if length == 0:
            queue.insert(0, element)
            break
        else:
            while length >= 0:
                length -= 1
                if element[0] > queue[length][0]:
                    queue.insert(length+1, element)
                    check = 1
                    break

        if check == 0:
            queue.insert(0, element)
            break

    return queue


'''
*** PassiveAgentStateMachine to be used by PassiveAgent.
***  - Interact directly through calling transitions
***  - Schematics will be given in the report

*** Each PassiveAgent instance creates its own instance of PassiveAgentStateMachine
*** Transitions are made by the Agents

+++ May incorporate water level and utilize on_'transition' functions
+++ Group states according to various parameters: there are weeds in the grid spot, there is disease in the grid spot;
    Or group by states (seed) (growing) (flowering) (harvest)
'''


class PassiveAgentStateMachine(StateMachine):
    # All Possible states of a soil patch
    # Start
    start = State("start", initial=True)
    # Plowed
    plowed = State("plowed")
    # Seed
    seed = State("seed")
    seed_sick = State("seed_sick")
    seed_weeds = State("seed_weeds")
    seed_dry = State("seed_dry")
    # Growing
    growing = State("growing")
    growing_sick = State("growing_sick")
    growing_weeds = State("growing_weeds")
    growing_dry = State("growing_dry")
    # Flowering
    flowering = State("flowering")
    flowering_sick = State("flowering_sick")
    flowering_weeds = State("flowering_weeds")
    flowering_dry = State("flowering_dry")
    # Harvestable
    harvestable = State("harvestable")
    harvestable_sick = State("harvestable_sick")
    harvestable_weeds = State("harvestable_weeds")
    harvestable_dry = State("harvestable_dry")

    # End states
    harvested = State("harvested")
    dead = State("dead")
    #end = State("end")
    # State groups
    waterable_states = (seed, seed_sick, seed_weeds, growing, growing_sick,
                        growing_weeds, flowering, flowering_sick, flowering_weeds)

    # All possible transitions of a soil patch
    # Start state transitions
    plow = start.to(plowed)
    # Plowed state transitions
    sow = plowed.to(seed)
    # Seed state transitions
    sick_seed = seed.to(seed_sick)
    sick_seed_death = seed_sick.to(dead)
    sick_seed_recovery = seed_sick.to(seed)
    weeds_seed = seed.to(seed_weeds)
    weeds_seed_recovery = seed_weeds.to(seed)
    weeds_seed_death = seed_weeds.to(dead)
    dry_seed = seed.to(seed_dry)
    dry_seed_recovery = seed_dry.to(seed)
    dry_seed_death = seed_dry.to(dead)
    seed_grown = seed.to(growing)
    # Growing state transitions
    sick_growing = growing.to(growing_sick)
    sick_growing_death = growing_sick.to(dead)
    sick_growing_recovery = growing_sick.to(growing)
    weeds_growing = growing.to(growing_weeds)
    weeds_growing_recovery = growing_weeds.to(growing)
    weeds_growing_death = growing_weeds.to(dead)
    dry_growing = growing.to(growing_dry)
    dry_growing_recovery = growing_dry.to(growing)
    dry_growing_death = growing_dry.to(dead)
    growing_to_flowering = growing.to(flowering)
    # Flowering state transitions
    sick_flowering = flowering.to(flowering_sick)
    sick_flowering_death = flowering_sick.to(dead)
    sick_flowering_recovery = flowering_sick.to(flowering)
    weeds_flowering = flowering.to(flowering_weeds)
    weeds_flowering_recovery = flowering_weeds.to(flowering)
    weeds_flowering_death = flowering_weeds.to(dead)
    dry_flowering = flowering.to(flowering_dry)
    dry_flowering_recovery = flowering_dry.to(flowering)
    dry_flowering_death = flowering_dry.to(dead)
    flowering_to_harvestable = flowering.to(harvestable)
    # Harvestable state transitions
    sick_harvestable = harvestable.to(harvestable_sick)
    sick_harvestable_death = harvestable_sick.to(dead)
    sick_harvestable_recovery = harvestable_sick.to(growing)
    weeds_harvestable = harvestable.to(harvestable_weeds)
    weeds_harvestable_recovery = harvestable_weeds.to(harvestable)
    weeds_harvestable_death = harvestable_weeds.to(dead)
    dry_harvestable = harvestable.to(harvestable_dry)
    dry_harvestable_recovery = harvestable_dry.to(harvestable)
    dry_harvestable_death = harvestable_dry.to(dead)
    harvestable_to_dead = harvestable.to(dead)
    harvest = harvestable.to(harvested)
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

        # Water level of the crop [0-100]. Initialized at 50 when seed is planted.
        # Crops will start to die whenever water_level is below water_threshold
        self.water_level = 0
        self.water_threshold = model_params["water_threshold"]

        # Set passive agent's seed crop parameters
        self.seed_sick_probability = model_params["seed_sick_probability"]
        self.seed_weeds_probability = model_params["seed_weeds_probability"]
        self.steps_seed_to_growing = model_params["steps_seed_to_growing"]

        # Set passive agent's growing crop parameters
        self.growing_sick_probability = model_params["growing_sick_probability"]
        self.growing_weeds_probability = model_params["growing_weeds_probability"]
        self.steps_growing_to_flowering = model_params["steps_growing_to_flowering"]

        # Set passive agent's flowering crop parameters
        self.flowering_sick_probability = model_params["flowering_sick_probability"]
        self.flowering_weeds_probability = model_params["flowering_weeds_probability"]
        self.steps_flowering_to_harvestable = model_params["steps_flowering_to_harvestable"]

        # Set passive agent's harvestable crop parameters
        self.harvestable_sick_probability = model_params["harvestable_sick_probability"]
        self.harvestable_weeds_probability = model_params["harvestable_weeds_probability"]
        self.steps_harvestable_to_dead = model_params["steps_harvestable_to_dead"]

    '''
    *** Main interaction function between ActiveAgent and PassiveAgent
    *** ActiveAgent calls PassiveAgent.interact(calling_active_agent) to change the state of PassiveAgent
    *** switcher dictionary determines which particular function to run depending on ActiveAgent current_tool
    *** Interaction functions defined below (subject to change)
    '''

    def interact(self, agent):
        if (agent.agent_type == 'ACTIVE'):
            switcher = {'plow': self.plow, 'seeder': self.sow, 'sprayer': self.cure, 'wacker': self.kill_weeds,
                        'irrigator': self.water, 'harvester': self.harvest}
            func = switcher.get(agent.current_tool, lambda: None)
            if (func is not None):
                func()

    def interactable(self):
        if self.machine == "seed" or self.machine == "growing" or self.machine == "flowering":
            return False
        else:
            return True



    # ----------------------------------- Interaction functions for interactions between active and passive agents

    '''
    Interaction function for the plowing of land
    '''

    def plow(self):
        if (self.machine.current_state == self.machine.start):
            self.time_at_current_state = 0
            self.machine.plow()

    '''
    Interaction function for the sowing of seeds
    '''

    def sow(self):
        if (self.machine.current_state == self.machine.plowed):
            self.time_at_current_state = 0
            self.water_level = 50
            self.machine.sow()

    '''
    Interaction function for curing plants of diseases
    '''

    def cure(self):
        # Seed
        if (self.machine.current_state == self.machine.seed_sick):
            self.time_at_current_state = 0
            self.machine.sick_seed_recovery()
        # growing
        if (self.machine.current_state == self.machine.growing_sick):
            self.time_at_current_state = 0
            self.machine.sick_growing_recovery()
        # Flowering
        if (self.machine.current_state == self.machine.flowering_sick):
            self.time_at_current_state = 0
            self.machine.sick_flowering_recovery()
        # Harvestable
        if (self.machine.current_state == self.machine.harvestable_sick):
            self.time_at_current_state = 0
            self.machine.sick_harvestable_recovery()

    '''
    Interaction function for the killing of weeds
    '''

    def kill_weeds(self):
        # Seed
        if self.machine.current_state == self.machine.seed_weeds:
            self.time_at_current_state = 0
            self.machine.weeds_seed_recovery()
        # growing
        if self.machine.current_state == self.machine.growing_weeds:
            self.time_at_current_state = 0
            self.machine.weeds_growing_recovery()
        # Flowering
        if self.machine.current_state == self.machine.flowering_weeds:
            self.time_at_current_state = 0
            self.machine.weeds_flowering_recovery()
        # Harvestable
        if self.machine.current_state == self.machine.harvestable_weeds:
            self.time_at_current_state = 0
            self.machine.weeds_harvestable_recovery()

    '''
    Interaction function for the watering of crops
    '''

    def water(self):
        if self.machine.current_state in self.machine.waterable_states:
            self.water_level = 100

    '''
    Interaction function for the harvesting of crops
    '''

    def harvest(self):
        if (self.machine.current_state == self.machine.harvestable):
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

    def step(self):
        self.time_at_current_state += 1
        self.water_level -= 1
        # TODO: Implement random variability in state transitions
        switcher = {self.machine.seed: self.when_seed, self.machine.growing: self.when_growing,
                    self.machine.flowering: self.when_flowering, self.machine.harvest: self.when_harvestable}
        func = switcher.get(self.machine.current_state,  None)
        if (func is not None):
            func()

    def advance(self):
        return "Hello"
    # ---------------------------------------- Independent transitions start here

    '''
    Independent seed state transitions
    '''

    def when_seed(self):
        # If enough time has passed, go to the growing state
        if (self.time_at_current_state >= self.steps_seed_to_growing):
            self.time_at_current_state = 0
            self.machine.seed_grown()
        # Dry out if there is not enough water
        elif (self.water_level < self.water_threshold):
            self.time_at_current_state = 0
            self.machine.dry_seed()
        # Randomly get sick
        elif (self.random.random() < self.seed_sick_probability):
            self.time_at_current_state = 0
            self.machine.sick_seed()
        # Randomly get weeds
        elif (self.random.random() < self.seed_weeds_probability):
            self.time_at_current_state = 0
            self.machine.weeds_seed()

    '''
    Independent growing state transitions
    '''

    def when_growing(self):
        # If enough time has passed, go to the flowering state
        if (self.time_at_current_state >= self.steps_growing_to_flowering):
            self.time_at_current_state = 0
            self.machine.growing_to_flowering()
        # Dry out if there is not enough water
        elif (self.water_level < self.water_threshold):
            self.time_at_current_state = 0
            self.machine.dry_growing()
        # Randomly get sick
        elif (self.random.random() < self.growing_sick_probability):
            self.time_at_current_state = 0
            self.machine.sick_growing()
        # Randomly get weeds
        elif (self.random.random() < self.growing_weeds_probability):
            self.time_at_current_state = 0
            self.machine.weeds_growing()

    def when_flowering(self):
        # If enough time has passed, go to the harvestable state
        if (self.time_at_current_state >= self.steps_flowering_to_harvestable):
            self.time_at_current_state = 0
            self.machine.flowering_to_harvestable()
        # Dry out if there is not enough water
        elif (self.water_level < self.water_threshold):
            self.time_at_current_state = 0
            self.machine.dry_flowering()
        # Randomly get sick
        elif (self.random.random() < self.flowering_sick_probability):
            self.time_at_current_state = 0
            self.machine.sick_flowering()
        # Randomly get weeds
        elif (self.random.random() < self.flowering_weeds_probability):
            self.time_at_current_state = 0
            self.machine.weeds_flowering()



    '''
    Independent transitions from the harvestable state
    '''

    def when_harvestable(self):
        # Die if too much time has passed without being harvested
        if (self.time_at_current_state >= self.steps_harvestable_to_dead):
            self.time_at_current_state = 0
            self.machine.harvestable_to_dead()
        # Dry out if there is not enough water
        elif (self.water_level < self.water_threshold):
            self.time_at_current_state = 0
            self.machine.dry_harvestable()
        # Randomly get sick
        elif (self.random.random() < self.harvestable_sick_probability):
            self.time_at_current_state = 0
            self.machine.sick_harvestable()
        # Randomly get weeds
        elif (self.random.random() < self.harvestable_weeds_probability):
            self.time_at_current_state = 0
            self.machine.weeds_harvestable()





    '''
    Independent transition function for drying out
    '''

    def when_drying(self):
        # Check if the crop was watered and should return to a non-drying state
        if self.water_level > self.water_threshold:
            recovery = True

        # Random probability for if the plant should die. Probability will go up and if the crop has been in the drying state
        # for as many steps as the water threshold is high, probability of dying will be 100%
        if self.random.random() < (self.time_at_current_state / self.water_threshold):
            dying = True

        # Seed
        if self.machine.current_state == self.machine.seed_dry:
            if recovery:
                self.time_at_current_state = 0  # Reset the time to 0 as a penalty for drying out
                self.machine.dry_seed_recovery
            if dying:
                self.time_at_current_state = 0
                self.machine.dry_seed_death
        # Growing
        if self.machine.current_state == self.machine.growing_dry:
            if recovery:
                self.time_at_current_state = 0  # Reset the time to 0 as a penalty for drying out
                self.machine.dry_growing_recovery
            if dying:
                self.time_at_current_state = 0
                self.machine.dry_growing_death
        # Flowering
        if self.machine.current_state == self.machine.flowering_dry:
            if recovery:
                self.time_at_current_state = 0  # Reset the time to 0 as a penalty for drying out
                self.machine.dry_flowering_recovery
            if dying:
                self.time_at_current_state = 0
                self.machine.dry_flowering_death



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

    def update(self, state=None, time_at_current_state=0, taken=0):
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

    def __init__(self, unique_id, pos, model, **model_params):
        super().__init__(unique_id, model)
        self.pos = pos
        self.agent_type = 'ACTIVE'
        self.protocol = model_params['com_protocol']
        # target can be watering, plowing, spraying and to gather or return the needed equipment
        self.targets = None
        self.mode = 'TEST'
        self.current_tool = 'plow'
        self.plan = None
        self.target = None  # This variable is used when a target location is set by the agent
        self.stepCount = 0
        self.calculationQueue = list()
        self.visitedNodes = list()

    # Calculate new positions
    def newPositions(self, pos):
        newPos = list()

        if pos[1]-1 >= 0:
            newPos.append((pos[0], pos[1]-1))

        if pos[1]+1 <= 49:
            newPos.append((pos[0], pos[1]+1))

        if pos[0]-1 >= 0:
            newPos.append((pos[0]-1, pos[1]))

        if pos[0]+1 <= 49:
            newPos.append((pos[0]+1, pos[1]))

        return newPos

    # Check in the maze (from currentStep to currentStep+2 done in BFS function) if the position is free
    def checkState(self, new, maze):
        checked = list()
        for element in new:
            if maze[element[1]][element[0]] == 0:
                test = 0
                for each in self.visitedNodes:
                    if each[0] == element[0] and each[1] == element[1]:
                        test = 1

                if test == 0:
                    checked.append(element)

        return checked

    # Add element to queue and mark the node as visited
    def addElemToQueue(self, pos, trace):
        if pos:
            for each in pos:
                if each not in self.visitedNodes:
                    self.calculationQueue.append((each, trace))
                    self.visitedNodes.append(each)

    # Implementation of BFS on a numpy array that searches for goals.
    # It will select the first one that it finds.
    def BFS(self, step):
        done = 0
        if len(self.calculationQueue) > 0:
            # position[0] is the pos of the element popped
            # position[1] is the passive agent associated
            position = self.calculationQueue.pop(0)

            # We need a deepcopy otherwise the same variable will be used recursivly
            # This is used as path history and need new copies sent the in recursive function
            temp = deepcopy(position[1])

            for element in self.model.knowledgeMap.attendancePoints:
                if element[0] == position[0] and element[1].taken == 0:
                    self.target = element[1].pos

                    # Remove all points marked for one field from the knowledgeMap attendancePoints
                    self.model.knowledgeMap.attendancePoints.remove(
                        ((element[1].pos[0]-1, element[1].pos[1]), element[1]))
                    self.model.knowledgeMap.attendancePoints.remove(
                        ((element[1].pos[0]+1, element[1].pos[1]), element[1]))

                    # If there is a top or bottom field, there is also an alternitve point it can go
                    if element[1].pos[1] == 1:
                        self.model.knowledgeMap.attendancePoints.append(
                            ((element[1].pos[0], 0), element[1]))
                    elif element[1].pos[1] == 48:
                        self.model.knowledgeMap.attendancePoints.append(
                            ((element[1].pos[0], 49), element[1]))

                    # Mark the passiveAgent (field) as taken
                    element[1].taken = 1

                    # done here used for safety
                    done = 1
                    temp.append(position[0])
                    return temp

            # If the search is not done, continue
            if done == 0:
                # Get new positions based on current
                newPositions = self.newPositions(position[0])

                # Update history
                temp.append(position[0])

                # Check for next step if the blocks I would like to move are available, based on current knowledge
                initCheck = self.checkState(
                    newPositions, self.model.knowledgeMap.getGridAtStepAsNumpyArray(1))

                # Add the new positions to the queue
                self.addElemToQueue(initCheck, temp[0:])

                # Calculate recursively a new point until we get near a field
                answer = self.BFS(deepcopy(1))
                return answer

        return None

    # Add what the agent sees to the knowledgeMap
    def update_perception(self, perceptionRadius=5):
        neighbors = self.model.grid.get_neighborhood(
            self.pos, True, False, perceptionRadius)
        for neighbor in neighbors:
            neighbor_obj = self.model.grid.get_cell_list_contents([neighbor])
            if (len(neighbor_obj) > 0):
                if isinstance(neighbor_obj[0], PassiveAgent):
                    self.model.knowledgeMap.update(
                        PassiveAgentPerception(neighbor_obj[0]))

    # This function is used to execute a move of an agent
    def executeMove(self):
        my_plans = self.model.knowledgeMap.planAgents[self.unique_id]
        plan_count = len(my_plans)

        if plan_count > 0:
            self.model.grid.move_agent(self, my_plans[0].pos)

    # Check if the tool is good for the field next to me
    # TODO: Add other tools and other field states

    def toolVSfield(self, fieldState):
        if self.current_tool == "plow" and fieldState == "start":
            return True
        elif self.current_tool == "seeder" and fieldState == "plowed":
            return True
        elif self.current_tool == "irrigator" and (fieldState == "seed_dry" or fieldState == "growing_dry" or fieldState == "flowering_dry"):
            return True
        elif self.current_tool == "wacker" and (fieldState == "seed_weeds" or fieldState == "growing_weeds" or fieldState == "flowering_weeds"):
            return True
        elif self.current_tool == "sprayer" and (fieldState == "seed_sick" or fieldState == "growing_sick" or fieldState == "flowering_sick"):
            return True
        elif self.current_tool == "harvester" and fieldState == "harvestable":
            return True
        return False

    def step(self):
        if self.protocol == "Simple protocol":
            # if the agent is searching for a task:
            # check fields around itself for possible task
            neighbors = self.model.grid.get_neighborhood(
                self.pos, False, False)
            for neighbor in neighbors:
                cell = self.model.grid.get_cell_list_contents([neighbor])
                # the cell next to the agent contains a crop
                if isinstance(cell, PassiveAgent):
                    if cell.interactable:  # the crop next to the agent has a task required to it
                        # if the agent has a tool which is good for the field next to it
                        if self.current_tool != 'none' and toolVSfield(self, cell.machine.current_state):
                            # interact with the crop
                            cell.interact(passive[0], self)
                        else:  # the tool is not good for the field or the agent has not tool
                            pass
                    else:  # there is no crop next to the agent that requires a task
                        # keep moving untill an interactable crop is found
                        return
                # the cell next to the agent contains the farm
                elif isinstance(cell, FarmAgent):
                    # get or return a tool from the farm
                    cell.interact(cell, self.target, self.current_tool)
        # if the agent is moving to the farm or to the goal crop
            # it should keep moving and not perform the checks above^

        elif self.protocol == "Helper-Based protocol":
            # Safety perception check
            if self.stepCount == 0:
                self.update_perception()
                self.stepCount += 1
            else:
                if self.target == None:
                    listOfFieldsFromKnowledge = [
                        obj for obj in self.model.knowledgeMap.navigationGrid if isinstance(obj, PassiveAgentPerception)]
                    queue = list()
                    for obj in listOfFieldsFromKnowledge:
                        pointOfInterest = self.model.schedule.getPassiveAgent(
                            obj.unique_id)
                        if self.toolVSfield(pointOfInterest.machine.current_state.value):
                            queue = prioritizeQueue(
                            queue, (heuristic(pointOfInterest.pos, self.pos), pointOfInterest))
                    if len(queue) == 0:
                        queue = prioritizeQueue(
                        queue, (heuristic(self.model.farmPos, self.pos), self.model.farmObject))

                    # Decide which is the closest point you can attend and that is free
                    while queue:
                        possibleTarget = queue.pop(0)
                        near = list()

                        # In here we calculate all possible points the agent can go
                        # It depends where the PassiveAgent is located and there are some special cases
                        # like the line on the right or the top/bottom of each line (as there are 3 spots the agent can go)
                        if possibleTarget[1] == self.model.farmObject:
                            self.target = possibleTarget[1].pos

                            # These are the two possible locations for every field
                            near.append(
                                (possibleTarget[1].pos[0]-1, possibleTarget[1].pos[1]))
                            near.append(
                                (possibleTarget[1].pos[0]+1, possibleTarget[1].pos[1]))

                            # If there is a top or bottom field, there is also an alternitve point it can go
                            if possibleTarget[1].pos[1] == 1:
                                near.append((possibleTarget[1].pos[0], 0))
                            elif possibleTarget[1].pos[1] == 48:
                                near.append((possibleTarget[1].pos[0], 49))

                            # Calculate the shortest path based on agents point and the other possible points
                            steps = astar.solve(self.pos, near)

                            temp = 0
                            if steps:
                                for step in steps:
                                    temp = temp + 1
                                    new_plan = ActiveAgentPlanning(
                                        self, step, temp)
                                    self.model.knowledgeMap.update(new_plan)
                                    self.model.schedule.add(new_plan)

                            near.clear()
                            queue.clear()
                            break
                        elif possibleTarget[1].taken == 0 and self.toolVSfield(possibleTarget[1].machine.current_state.value):
                            possibleTarget[1].taken = 1
                            self.target = possibleTarget[1].pos

                            # These are the two possible locations for every field
                            near.append(
                                (possibleTarget[1].pos[0]-1, possibleTarget[1].pos[1]))
                            near.append(
                                (possibleTarget[1].pos[0]+1, possibleTarget[1].pos[1]))

                            # If there is a top or bottom field, there is also an alternitve point it can go
                            if possibleTarget[1].pos[1] == 1:
                                near.append((possibleTarget[1].pos[0], 0))
                            elif possibleTarget[1].pos[1] == 48:
                                near.append((possibleTarget[1].pos[0], 49))

                            # Calculate the shortest path based on agents point and the other possible points
                            steps = astar.solve(self.pos, near)

                            temp = 0
                            if steps:
                                for step in steps:
                                    temp = temp + 1
                                    new_plan = ActiveAgentPlanning(
                                        self, step, temp)
                                    self.model.knowledgeMap.update(new_plan)
                                    self.model.schedule.add(new_plan)

                            near.clear()
                            queue.clear()
                            break

            self.tryNeighboors = 0

        elif self.protocol == "Coordination Cooperative protocol":
            return

    # This function is used for the advance phase due to the Simultaneous Activation schedule

    def advance(self):
        # First, execute the move, if any
        self.executeMove()

        # Then remove the moved step from the knowledgeMap, if any
        self.model.knowledgeMap.removeOneStep(self.unique_id)

        # Then update the perception of the agent(s)
        self.update_perception()

        # Then check if this was the last step. If it was, check if the agent is next to the target and perform the action.
        plan_count = len(self.model.knowledgeMap.planAgents[self.unique_id])
        if plan_count == 0:
            if self.target is not None:
                neighbors = self.model.grid.get_neighborhood(
                    self.pos, True, False)
                for neighbor in neighbors:
                    cell = self.model.grid.get_cell_list_contents([neighbor])
                    passive = [obj for obj in cell if isinstance(
                        obj, PassiveAgent)]
                    if len(passive) > 0 and passive[0].pos == self.target:
                        passive[0].interact(self)
                        passive[0].taken = 0
                        self.target = None
                        break
                    elif self.target == self.model.farmPos:
                        self.model.farmObject.interact(self)
                        self.target = None

        # And finally update the perception of the agent(s) once more to check in the knowledgeMap that the action has been performed
        self.update_perception()


'''
*** ActiveAgentPlanning is an object which represents a plan of a particular ActiveAgentPlanning
*** Place on AgentKnowledgeMap.planGrid
*** Expires when particular stage is reached through sample_stage -> passive_stage
'''
# This class is used to post agent plan on the AgentKnowledgeMap.planGrid


class ActiveAgentPlanning(Agent):
    # The plan will have a unique id of the agent who made the plan
    def __init__(self, agent, pos, steps=0):
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


'''
The FarmAgent function will be the starting point for the active agents
and will be used as the location where active agents can switch their tools.
---> In the current implementation, this function is not yet used <---
'''


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
        self.sprayer = 5
        self.wacker = 5
        self.harvester = 5
        self.seeder = 5

    def sample_stage(self):
        return

    def interact(self, agent):
        print("Updating agent tool")
        tool = agent.current_tool
        if tool != None:
            if tool == 'irrigator':
                self.irrigator += 1
            elif tool == 'plow':
                self.plow += 1
            elif tool == 'spray':
                self.spray += 1
            elif tool == 'wacker':
                self.wacker += 1
            elif tool == 'harvester':
                self.harvester += 1
            elif tool == 'seeder':
                self.seeder += 1
        agent.current_tool = None
        plantCount = [0,0,0,0,0,0] #Plow, seed, water, weeds, cure, harvest
        for passiveAgent in self.model.knowledgeMap.perceptionAgents:
            fieldState = self.model.knowledgeMap.perceptionAgents[passiveAgent].state.value
            if fieldState == "start" and self.plow > 0:
                plantCount[0]+=1
            elif  fieldState == "plowed" and self.seeder > 0:
                plantCount[1]+=1
            elif  (fieldState == "seed_dry" or fieldState == "growing_dry" or fieldState == "flowering_dry") and self.irrigator > 0:
                plantCount[2]+=1
            elif (fieldState == "seed_weeds" or fieldState == "growing_weeds" or fieldState == "flowering_weeds") and self.wacker > 0:
                plantCount[3]+=1
            elif (fieldState == "seed_sick" or fieldState == "growing_sick" or fieldState == "flowering_sick") and self.sprayer > 0:
                plantCount[4]+=1
            elif fieldState == "harvestable" and self.harvester > 0:
                plantCount[5]+=1
        f = lambda i: plantCount[i]
        argmax = max(range(len(plantCount)), key=f)
        if argmax == 0: #Plower
            self.plow -= 1
            agent.current_tool = "plow"
        elif argmax == 1: #Seeder
            self.seeder -= 1
            agent.current_tool = "seeder"
        elif argmax == 2: #Irrigator
            self.irrigator -= 1
            agent.current_tool == "irrigator"
        elif argmax == 3: #Whacker
            self.wacker -= 1
            agent.current_tool == "wacker"
        elif argmax == 4: #sprayer
            self.sprayer -= 1
            agent.current_tool == "sprayer"
        elif argmax == 5: #Harvester
            self.harvester -= 1
            agent.current_tool == "harvester"
        print(agent.unique_id)
        print("Now has")
        print(agent.current_tool)


    def interact(self, target, tool):  # for the taking and returning of farm equipment
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
