from mesa import Agent
from statemachine import State, StateMachine
import ag_sim.schedule
from queue import PriorityQueue
import astar
from copy import deepcopy
from multiprocessing import Pool


# Heuristic needed for movement cost to the goal
def heuristic(a, b):
    v1 = abs(a[0]-b[0])
    if v1 == 1:
        temp = v1 + abs(a[1]-b[1])
    else:
        temp1 = v1 + abs(0-a[1]) + abs(0-b[1])
        temp2 = v1 + abs(49-a[1]) + abs(49-b[1])
        temp = min(temp1, temp2)

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
    # end = State("end")
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
    sick_harvestable_recovery = harvestable_sick.to(harvestable)
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

        # State times that need to be saved
        self.time_at_current_state = 0
        self.time_at_prev_healthy_state = 0
        self.steps_in_dehydrated_state = 0
        self.steps_in_sick_state = 0
        self.steps_in_weeds_state = 0

        self.taken = 0

        # Set back a state some steps as a penalty <-- currently not used (set to 0)
        self.penalty_for_dry_sick_weeds = 0

        # Number of steps that a crop can live without getting dehydrated
        self.water_level = 0
        self.max_steps_dehydrated = model_params["max_steps_dehydrated"]
        self.max_water_level = model_params["max_water_level"]

        # Maximum number of steps in sick and weeds states
        self.max_steps_sick = model_params["max_steps_sick"]
        self.max_steps_weeds = model_params["max_steps_weeds"]

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
                        'irrigator': self.water, 'harvester': self.harvest(self.model)}
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
            self.water_level = self.max_water_level
            self.machine.sow()

    '''
    Interaction function for curing plants of diseases
    '''

    def cure(self):

        # Add the time spent in this sick state to the crop's total time in sick states
        self.steps_in_sick_state += self.time_at_current_state
        # Reset the state time to the time in the healthy state when it got sick, and potentially subtract a time penalty
        self.time_at_current_state = self.time_at_prev_healthy_state - \
            self.penalty_for_dry_sick_weeds

        # Seed
        if (self.machine.current_state == self.machine.seed_sick):
            self.machine.sick_seed_recovery()
        # growing
        if (self.machine.current_state == self.machine.growing_sick):
            self.machine.sick_growing_recovery()
        # Flowering
        if (self.machine.current_state == self.machine.flowering_sick):
            self.machine.sick_flowering_recovery()
        # Harvestable
        if (self.machine.current_state == self.machine.harvestable_sick):
            self.machine.sick_harvestable_recovery()

    '''
    Interaction function for the killing of weeds
    '''

    def kill_weeds(self):

        # Add the time spent in this weeds state to the crop's total time in weeds states
        self.steps_in_weeds_state += self.time_at_current_state
        # Reset the state time to the time in the healthy state when it got weeds, and potentially subtract a time penalty
        self.time_at_current_state = self.time_at_prev_healthy_state - \
            self.penalty_for_dry_sick_weeds

        # Seed
        if self.machine.current_state == self.machine.seed_weeds:
            self.machine.weeds_seed_recovery()
        # growing
        if self.machine.current_state == self.machine.growing_weeds:
            self.machine.weeds_growing_recovery()
        # Flowering
        if self.machine.current_state == self.machine.flowering_weeds:
            self.machine.weeds_flowering_recovery()
        # Harvestable
        if self.machine.current_state == self.machine.harvestable_weeds:
            self.machine.weeds_harvestable_recovery()

    '''
    Interaction function for the watering of crops
    '''

    def water(self):
        # Add the time spent in this dehydrated state to the crop's total time in dehydrated states
        self.steps_in_dehydrated_state += self.time_at_current_state
        # Reset the state time to the time in the healthy state when it got dehydrated, and potentially subtract a time penalty
        self.time_at_current_state = self.time_at_prev_healthy_state - \
            self.penalty_for_dry_sick_weeds
        # Reset the water level to the maximum
        self.water_level = self.max_water_level

        # Seed
        if self.machine.current_state == self.machine.seed_dry:
            self.machine.dry_seed_recovery()
        # growing
        if self.machine.current_state == self.machine.growing_weeds:
            self.machine.dry_growing_recovery()
        # Flowering
        if self.machine.current_state == self.machine.flowering_weeds:
            self.machine.dry_flowering_recovery()
        # Harvestable
        if self.machine.current_state == self.machine.harvestable_weeds:
            self.machine.dry_harvestable_recovery()

    '''
    Interaction function for the harvesting of crops
    '''

    def harvest(self, model):
        if (self.machine.current_state == self.machine.harvestable):

            # Increase the harvest and quality measurements
            model.increase_harvest_score()
            model.increase_total_steps_dehydrated(
                self.steps_in_dehydrated_state)
            model.increase_total_steps_sick(self.steps_in_sick_state)
            model.increase_total_steps_weeds(self.steps_in_weeds_state)

            # Reset the state time and go to the harvested state
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
        switcher = {
            # Seed
            self.machine.seed: self.when_seed,
            self.machine.seed_dry: self.when_drying,
            self.machine.seed_sick: self.when_sick,
            self.machine.seed_weeds: self.when_weeds,
            # Growing
            self.machine.growing: self.when_growing,
            self.machine.growing_dry: self.when_drying,
            self.machine.growing_sick: self.when_sick,
            self.machine.growing_weeds: self.when_weeds,
            # Flowering
            self.machine.flowering: self.when_flowering,
            self.machine.flowering_dry: self.when_drying,
            self.machine.flowering_sick: self.when_sick,
            self.machine.flowering_weeds: self.when_weeds,
            # Harvestable
            self.machine.harvestable: self.when_harvestable,
            self.machine.harvestable_dry: self.when_drying,
            self.machine.harvestable_sick: self.when_sick,
            self.machine.harvestable_weeds: self.when_weeds,
        }
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
        elif (self.water_level <= 0):
            self.time_at_prev_healthy_state = self.time_at_current_state
            self.time_at_current_state = 0
            self.machine.dry_seed()
        # Randomly get sick
        elif (self.random.random() < self.seed_sick_probability):
            self.time_at_prev_healthy_state = self.time_at_current_state
            self.time_at_current_state = 0
            self.machine.sick_seed()
        # Randomly get weeds
        elif (self.random.random() < self.seed_weeds_probability):
            self.time_at_prev_healthy_state = self.time_at_current_state
            self.time_at_current_state = 0
            self.machine.weeds_seed()

    def when_growing(self):
        # If enough time has passed, go to the flowering state
        if (self.time_at_current_state >= self.steps_growing_to_flowering):
            self.time_at_current_state = 0
            self.machine.growing_to_flowering()
        # Dry out if there is not enough water
        elif (self.water_level <= 0):
            self.time_at_prev_healthy_state = self.time_at_current_state
            self.time_at_current_state = 0
            self.machine.dry_growing()
        # Randomly get sick
        elif (self.random.random() < self.growing_sick_probability):
            self.time_at_prev_healthy_state = self.time_at_current_state
            self.time_at_current_state = 0
            self.machine.sick_growing()
        # Randomly get weeds
        elif (self.random.random() < self.growing_weeds_probability):
            self.time_at_prev_healthy_state = self.time_at_current_state
            self.time_at_current_state = 0
            self.machine.weeds_growing()

    def when_flowering(self):
        # If enough time has passed, go to the harvestable state
        if (self.time_at_current_state >= self.steps_flowering_to_harvestable):
            self.time_at_current_state = 0
            self.machine.flowering_to_harvestable()
        # Dry out if there is not enough water
        elif (self.water_level <= 0):
            self.time_at_prev_healthy_state = self.time_at_current_state
            self.time_at_current_state = 0
            self.machine.dry_flowering()
        # Randomly get sick
        elif (self.random.random() < self.flowering_sick_probability):
            self.time_at_prev_healthy_state = self.time_at_current_state
            self.time_at_current_state = 0
            self.machine.sick_flowering()
        # Randomly get weeds
        elif (self.random.random() < self.flowering_weeds_probability):
            self.time_at_prev_healthy_state = self.time_at_current_state
            self.time_at_current_state = 0
            self.machine.weeds_flowering()

    def when_harvestable(self):
        # Die if too much time has passed without being harvested
        if (self.time_at_current_state >= self.steps_harvestable_to_dead):
            self.time_at_current_state = 0
            self.machine.harvestable_to_dead()
        # Dry out if there is not enough water
        elif (self.water_level <= 0):
            self.time_at_prev_healthy_state = self.time_at_current_state
            self.time_at_current_state = 0
            self.machine.dry_harvestable()
        # Randomly get sick
        elif (self.random.random() < self.harvestable_sick_probability):
            self.time_at_prev_healthy_state = self.time_at_current_state
            self.time_at_current_state = 0
            self.machine.sick_harvestable()
        # Randomly get weeds
        elif (self.random.random() < self.harvestable_weeds_probability):
            self.time_at_prev_healthy_state = self.time_at_current_state
            self.time_at_current_state = 0
            self.machine.weeds_harvestable()

    '''
    Independent transition function for drying out
    '''

    def when_drying(self):
        dying_because_dehydrated = False

        # Die if the crop is dry for too long
        if self.time_at_current_state > self.max_steps_dehydrated:
            dying_because_dehydrated = True

        # Seed
        if self.machine.current_state == self.machine.seed_dry:
            if dying_because_dehydrated:
                self.time_at_current_state = 0
                self.machine.dry_seed_death()
        # Growing
        if self.machine.current_state == self.machine.growing_dry:
            if dying_because_dehydrated:
                self.time_at_current_state = 0
                self.machine.dry_growing_death()
        # Flowering
        if self.machine.current_state == self.machine.flowering_dry:
            if dying_because_dehydrated:
                self.time_at_current_state = 0
                self.machine.dry_flowering_death()
        # Harvestable
        if self.machine.current_state == self.machine.harvestable_dry:
            if dying_because_dehydrated:
                self.time_at_current_state = 0
                self.machine.dry_harvestable_death()

    '''
    Independent transition function for sick states
    '''

    def when_sick(self):
        dying_because_sick = False

        # Die if the crop is sick for too long
        if self.time_at_current_state >= self.max_steps_sick:
            dying_because_sick = True

        # Seed
        if self.machine.current_state == self.machine.seed_sick:
            if dying_because_sick:
                self.time_at_current_state = 0
                self.machine.sick_seed_death()
        # Growing
        if self.machine.current_state == self.machine.growing_sick:
            if dying_because_sick:
                self.time_at_current_state = 0
                self.machine.sick_growing_death()
        # Flowering
        if self.machine.current_state == self.machine.flowering_sick:
            if dying_because_sick:
                self.time_at_current_state = 0
                self.machine.sick_flowering_death()
        # Harvestable
        if self.machine.current_state == self.machine.harvestable_sick:
            if dying_because_sick:
                self.time_at_current_state = 0
                self.machine.sick_harvestable_death()

    '''
    Independent transition function for weeds states
    '''

    def when_weeds(self):

        # Die if the crop has weeds for too long
        dying_because_weeds = False
        if self.time_at_current_state >= self.max_steps_weeds:
            dying_because_weeds = True

        # Seed
        if self.machine.current_state == self.machine.seed_weeds:
            if dying_because_weeds:
                self.time_at_current_state = 0
                self.machine.weeds_seed_death()
        # Growing
        if self.machine.current_state == self.machine.growing_weeds:
            if dying_because_weeds:
                self.time_at_current_state = 0
                self.machine.weeds_growing_death()
        # Flowering
        if self.machine.current_state == self.machine.flowering_weeds:
            if dying_because_weeds:
                self.time_at_current_state = 0
                self.machine.weeds_flowering_death()
        # Harvestable
        if self.machine.current_state == self.machine.harvestable_weeds:
            if dying_because_weeds:
                self.time_at_current_state = 0
                self.machine.weeds_harvestable_death()

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
        self.fieldsToAttend = list()
        self.recalculateHeur = 0

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
        else:
            self.target = None

    # Check if the tool is good for the field next to me
    # TODO: Add other tools and other field states

    def recalculateHeuristics(self):
        if len(self.fieldsToAttend) > 0:
            queue = list()
            for element in self.fieldsToAttend:
                queue = prioritizeQueue(
                    queue, (heuristic(element[1].pos, self.pos), element[1]))

            self.fieldsToAttend.clear()
            self.fieldsToAttend = queue

    def toolVSfield(self, fieldState):
        if self.current_tool == "plow" and fieldState == "start":
            return True
        elif self.current_tool == "seeder" and fieldState == "plowed":
            return True
        elif self.current_tool == "irrigator" and (fieldState == "seed_dry" or fieldState == "growing_dry" or fieldState == "flowering_dry" or fieldState == "harvestable_dry"):
            return True
        elif self.current_tool == "wacker" and (fieldState == "seed_weeds" or fieldState == "growing_weeds" or fieldState == "flowering_weeds" or fieldState == "harvestable_weeds"):
            return True
        elif self.current_tool == "sprayer" and (fieldState == "seed_sick" or fieldState == "growing_sick" or fieldState == "flowering_sick" or fieldState == "harvestable_sick"):
            return True
        elif self.current_tool == "harvester" and fieldState == "harvestable":
            return True
        return False

    def calculatePath(self, moveTo):
        near = list()
        # These are the two possible locations for every field
        near.append(
            (moveTo.pos[0]-1, moveTo.pos[1]))
        near.append(
            (moveTo.pos[0]+1, moveTo.pos[1]))

        # If there is a top or bottom field, there is also an alternitve point it can go
        if moveTo.pos[1] == 1:
            near.append((moveTo.pos[0], 0))
        elif moveTo.pos[1] == 48:
            near.append((moveTo.pos[0], 49))

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

    def calculatePriorityTool(self):
        irrigator = 0
        plow = 0
        sprayer = 0
        wacker = 0
        harvester = 0
        seeder = 0

        listOfFieldsFromKnowledge = [
            obj for obj in self.model.knowledgeMap.navigationGrid if isinstance(obj, PassiveAgentPerception)]

        for obj in listOfFieldsFromKnowledge:
            pointOfInterest = self.model.schedule.getPassiveAgent(
                obj.unique_id)
            if pointOfInterest.machine.current_state.value == "start":
                plow += 1
            elif pointOfInterest.machine.current_state.value == "plowed":
                seeder += 1
            elif pointOfInterest.machine.current_state.value == "seed_dry" or pointOfInterest.machine.current_state.value == "growing_dry" or pointOfInterest.machine.current_state.value == "flowering_dry" or pointOfInterest.machine.current_state.value == "harvestable_dry":
                irrigator += 1.2
            elif pointOfInterest.machine.current_state.value == "seed_weeds" or pointOfInterest.machine.current_state.value == "growing_weeds" or pointOfInterest.machine.current_state.value == "flowering_weeds" or pointOfInterest.machine.current_state.value == "harvestable_weeds":
                wacker += 1.1
            elif pointOfInterest.machine.current_state.value == "seed_sick" or pointOfInterest.machine.current_state.value == "growing_sick" or pointOfInterest.machine.current_state.value == "flowering_sick" or pointOfInterest.machine.current_state.value == "harvestable_sick":
                sprayer += 1.3
            elif pointOfInterest.machine.current_state.value == "harvestable":
                harvester = 1.5

        priority = list()
        priority = prioritizeQueue(priority, (plow, "plow"))
        priority = prioritizeQueue(priority, (seeder, "seeder"))
        priority = prioritizeQueue(priority, (irrigator, "irrigator"))
        priority = prioritizeQueue(priority, (wacker, "wacker"))
        priority = prioritizeQueue(priority, (sprayer, "sprayer"))
        priority = prioritizeQueue(priority, (harvester, "harvester"))

        return priority

    def step(self):
        if self.protocol == "Simple protocol":
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

        elif self.protocol == "Helper-Based protocol":
            # Safety perception check
            if self.stepCount == 0:
                self.update_perception()
                self.stepCount += 1
            else:
                if len(self.fieldsToAttend) == 0:
                    self.recalculateHeur = 0
                    # Get all passiveAgents from the KnowledgeMap
                    listOfFieldsFromKnowledge = [
                        obj for obj in self.model.knowledgeMap.navigationGrid if isinstance(obj, PassiveAgentPerception)]
                    queue = list()
                    for obj in listOfFieldsFromKnowledge:
                        pointOfInterest = self.model.schedule.getPassiveAgent(
                            obj.unique_id)
                        if self.toolVSfield(pointOfInterest.machine.current_state.value):
                            queue = prioritizeQueue(
                                queue, (heuristic(pointOfInterest.pos, self.pos), pointOfInterest))

                    # Check the status of all agents from the knowledge map
                    while queue:
                        possibleTarget = queue[0]
                        queue.remove(possibleTarget)

                        if possibleTarget[1].taken == 0 and self.toolVSfield(possibleTarget[1].machine.current_state.value):
                            # If there are no points to attend in the agent's knowledge, add it to its knowledge
                            if len(self.fieldsToAttend) == 0:
                                possibleTarget[1].taken = 1
                                self.fieldsToAttend.append(
                                    (possibleTarget[0], possibleTarget[1]))

                            # If there is at least a point to attend in the agent's knowledge, get all points it can attend on that row based on the first point he added
                            elif len(self.fieldsToAttend) != 0 and possibleTarget[1].pos[0] == self.fieldsToAttend[0][1].pos[0]:
                                possibleTarget[1].taken = 1
                                self.fieldsToAttend = prioritizeQueue(
                                    self.fieldsToAttend, (possibleTarget[0], possibleTarget[1]))

                if len(self.model.knowledgeMap.planAgents[self.unique_id]) == 0:
                    # If there is at least a field it can attend with the current tool, go there.
                    if len(self.fieldsToAttend) > 0:
                        moveTo = self.fieldsToAttend[0]
                        self.calculatePath(moveTo[1])

                    # Else, change the tool
                    else:
                        self.fieldsToAttend.append(
                            tuple((0, self.model.farmObject)))
                        self.calculatePath(self.model.farmObject)

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
        if self.protocol == "Helper-Based protocol":
            # Then check if this was the last step. If it was, check if the agent is next to the target and perform the action.
            plan_count = len(
                self.model.knowledgeMap.planAgents[self.unique_id])
            if plan_count == 0:
                # Recalculate all heuristics after I have reached the first point of interest (ONLY ONCE until fieldsToAttend is empty again)
                if self.recalculateHeur == 0 and len(self.fieldsToAttend) > 1:
                    self.recalculateHeuristics()
                    self.recalculateHeur = 1
                neighbors = self.model.grid.get_neighborhood(
                    self.pos, False, False)
                for neighbor in neighbors:
                    neighborAgent = self.model.schedule.getPassiveAgentOnPos(
                        neighbor)
                    if isinstance(neighborAgent, PassiveAgent) and self.toolVSfield(neighborAgent.machine.current_state.value):
                        neighborAgent.interact(self)
                        neighborAgent.taken = 0
                    # Get only passive aggents in neighborhood
                    if len(self.fieldsToAttend) > 1:
                        for item in self.fieldsToAttend:
                            if item[1].pos == neighbor:
                                neighborPassive = self.model.schedule.getPassiveAgentOnPos(
                                    neighbor)
                                neighborPassive.interact(self)
                                neighborPassive.taken = 0
                                self.fieldsToAttend.remove(
                                    self.fieldsToAttend[0])
                                break
                    elif len(self.fieldsToAttend) == 1:
                        if self.fieldsToAttend[0][1].pos == neighbor:
                            # If I am at the farm, change the tool
                            if self.fieldsToAttend[0][1].pos == self.model.farmObject.pos:
                                priority = self.calculatePriorityTool()
                                # print(priority)
                                temp = len(priority) - 1
                                self.model.farmObject.return_tool(
                                    self.current_tool)
                                self.current_tool = None
                                while temp >= 0:
                                    test = self.model.farmObject.take_tool(
                                        priority[temp][1])
                                    if test == True:
                                        self.current_tool = priority[temp][1]
                                        self.fieldsToAttend.clear()
                                        # print(self.current_tool)
                                        break

                                    temp -= 1

                            # Else, interact with the field
                            else:
                                neighborPassive = self.model.schedule.getPassiveAgentOnPos(
                                    neighbor)
                                neighborPassive.interact(self)
                                neighborPassive.taken = 0
                                self.fieldsToAttend.clear()

        elif self.protocol == "Simple protocol":
            neighbors = self.model.grid.get_neighborhood(
                self.pos, False, False)
            for neighbor in neighbors:
                neighborPassive = self.model.schedule.getPassiveAgentOnPos(
                    neighbor)
                if isinstance(neighborPassive, PassiveAgent) and self.toolVSfield(neighborPassive.machine.current_state.value):
                    neighborPassive.interact(self)
                    break
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
        self.irrigator = 10
        self.plow = 10
        self.sprayer = 10
        self.wacker = 10
        self.harvester = 10
        self.seeder = 10

    def sample_stage(self):
        return

    def interact(self, agent):
        # print("Updating agent tool")
        tool = agent.current_tool
        if tool != None:
            if tool == 'irrigator':
                self.irrigator += 1
            elif tool == 'plow':
                self.plow += 1
            elif tool == 'spray':
                self.sprayer += 1
            elif tool == 'wacker':
                self.wacker += 1
            elif tool == 'harvester':
                self.harvester += 1
            elif tool == 'seeder':
                self.seeder += 1
        agent.current_tool = None
        # Plow, seed, water, weeds, cure, harvest
        plantCount = [0, 0, 0, 0, 0, 0]
        for passiveAgent in self.model.knowledgeMap.perceptionAgents:
            fieldState = self.model.knowledgeMap.perceptionAgents[passiveAgent].state.value
            if fieldState == "start" and self.plow > 0:
                plantCount[0] += 1
            elif fieldState == "plowed" and self.seeder > 0:
                plantCount[1] += 1
            elif (fieldState == "seed_dry" or fieldState == "growing_dry" or fieldState == "flowering_dry" or fieldState == "harvestable_dry") and self.irrigator > 0:
                plantCount[2] += 1
            elif (fieldState == "seed_weeds" or fieldState == "growing_weeds" or fieldState == "flowering_weeds" or fieldState == "harvestable_weeds") and self.wacker > 0:
                plantCount[3] += 1
            elif (fieldState == "seed_sick" or fieldState == "growing_sick" or fieldState == "flowering_sick" or fieldState == "harvestable_sick") and self.sprayer > 0:
                plantCount[4] += 1
            elif fieldState == "harvestable" and self.harvester > 0:
                plantCount[5] += 1

        def f(i): return plantCount[i]
        argmax = max(range(len(plantCount)), key=f)
        if argmax == 0:  # Plower
            self.plow -= 1
            agent.current_tool = "plow"
        elif argmax == 1:  # Seeder
            self.seeder -= 1
            agent.current_tool = "seeder"
        elif argmax == 2:  # Irrigator
            self.irrigator -= 1
            agent.current_tool = "irrigator"
        elif argmax == 3:  # Whacker
            self.wacker -= 1
            agent.current_tool = "wacker"
        elif argmax == 4:  # sprayer
            self.sprayer -= 1
            agent.current_tool = "sprayer"
        elif argmax == 5:  # Harvester
            self.harvester -= 1
            agent.current_tool = "harvester"
        # print(agent.unique_id)
        # print("Now has")
        # print(agent.current_tool)

    def interact2(self, target, tool):  # for the taking and returning of farm equipment
        if tool != None:
            if tool == 'irrigator':
                self.irrigator += 1
                return True
            elif tool == 'plow':
                self.plow += 1
                return True
            elif tool == 'spray':
                self.sprayer += 1
                return True
        elif target == 'watering' and self.irrigator > 0:
            self.irrigator -= 1
            return True
        elif target == 'plowing' and self.plow > 0:
            self.plow -= 1
            return True
        elif target == 'spraying' and self.sprayer > 0:
            self.sprayer -= 1
            return True
        else:
            return False

    def return_tool(self, tool):
        if tool != None:
            if tool == 'irrigator':
                self.irrigator += 1
            elif tool == 'plow':
                self.plow += 1
            elif tool == 'sprayer':
                self.sprayer += 1
            elif tool == 'wacker':
                self.wacker += 1
            elif tool == 'harvester':
                self.harvester += 1
            elif tool == 'seeder':
                self.seeder += 1

    def take_tool(self, requestedTool):
        if requestedTool == 'irrigator' and self.irrigator > 0:
            self.irrigator -= 1
            return True
        elif requestedTool == 'plow' and self.plow > 0:
            self.plow -= 1
            return True
        elif requestedTool == 'sprayer' and self.sprayer > 0:
            self.sprayer -= 1
            return True
        elif requestedTool == 'wacker' and self.wacker > 0:
            self.wacker -= 1
            return True
        elif requestedTool == 'harvester' and self.harvester > 0:
            self.harvester -= 1
            return True
        elif requestedTool == 'seeder' and self.seeder > 0:
            self.seeder -= 1
            return True
        else:
            return False
