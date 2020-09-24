from mesa import Agent
from statemachine import State, StateMachine

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
    ready_to_harvest = flowering.to(harvestable)
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
    def __init__(self, unique_id, pos, model):
        super().__init__(unique_id, model)
        self.pos = pos
        self.agent_type = 'PASSIVE'
        self.machine = PassiveAgentStateMachine()
        self.time_at_current_state = 0

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
        switcher = {self.machine.baby: self.when_baby, self.machine.growing : self.when_growing, self.machine.flowering : self.when_flowering, self.machine.harvest : self.when_harvest}
        func = switcher.get(self.machine.current_state,  None)
        if (func is not None):
            func()

    # ---------------------------------------- Independent transitions start here
    def when_baby(self):
        if (self.time_at_current_state >= 10):
            self.time_at_current_state = 0
            self.machine.baby_grown()
        elif (self.random.random() < 0.001):
            self.time_at_current_state = 0
            self.machine.sick_baby()
        elif (self.random.random() < 0.005):
            self.time_at_current_state = 0
            self.machine.weeds_baby()

    def when_growing(self):
        return

    def when_flowering(self):
        return

    def when_harvest(self):
        return
    # ******************               THE INDEPENDENT TRANSITIONS END HERE             *******************

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
        if isinstance(agent, PassiveAgent):
            self.state = agent.machine.current_state
            self.time_at_current_state = agent.time_at_current_state

    def update(self, state = None, time_at_current_state = 0):
        if (state is not None):
            self.state = state
            self.time_at_current_state = time_at_current_state



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
        self.current_tool = self.random.choice(['PLOW', 'SOW'])
        self.plan = None


    '''
    # JUST LEAVE THAT HERE FOR NOW
    # This is a template on how to update the knowledgeMap in passive_stage
    def passive_stage(self):
        neighbors = self.model.grid.get_neighborhood(self.pos, True, True)
        for neighbor in neighbors:
            neighbor_obj = self.model.grid.get_cell_list_contents([neighbor])
            if (len(neighbor_obj) > 0):
                if isinstance(neighbor_obj[0], PassiveAgent):
                    self.model.knowledgeMap.update(PassiveAgentPerception(neighbor_obj[0]))
        my_plans = self.model.knowledgeMap.planAgents[self.unique_id]
        my_plans.sort(key=lambda x: x.steps_left, reverse=False)
        plan_count = len(my_plans)
        if plan_count > 0:
            furthest_plan = my_plans[plan_count-1]
            self.plan = my_plans[0]
        else:
            furthest_plan = ActiveAgentPlanning(self, self.pos, 0)
        for i in range(5-len(plan_count)):
            grid_at_state = self.model.knowledgeMap.getGridStateAtStep(furthest_plan.steps_left)
            neighbors = grid_at_state.get_neighborhood(furthest_plan.pos , True, True)
            empty_cells = [cell for cell in neighbors if self.model.grid.is_cell_empty(cell)]
            if len(empty_cells > 0):
                choice = self.random.choice(empty_cells)
                new_plan = ActiveAgentPlanning(self, choice.pos, furthest_plan.steps_left+1)
                self.AgentKnowledgeMap.update(new_plan)
                furthest_plan = new_plan
    '''

    '''
    *** sample_Stage is the stage used to debug the model
    *** It will not be used eventually
    *** All the below functionality will be divided in passive_stage and active_stage
    !!!!              NOTE:: There are some bugs in here
    '''

    def sample_stage(self):
        neighbors = self.model.grid.get_neighborhood(self.pos, True, False)
        my_plans = self.model.knowledgeMap.planAgents[self.unique_id]
        my_plans.sort(key=lambda x: x.steps_left, reverse=False)
        plan_count = len(my_plans)
        if (self.mode == 'TEST'):
            if plan_count > 0 and self.model.grid.is_cell_empty(my_plans[0].pos):
                self.model.grid.move_agent(self,my_plans[0].pos)
            for neighbor in neighbors:
                cell = self.model.grid.get_cell_list_contents([neighbor])
                passive = [obj for obj in cell if isinstance(obj, PassiveAgent)]
                if len(passive) > 0:
                    passive[0].interact(self)
        # This stage is for merely testing everything
        neighbors = self.model.grid.get_neighborhood(self.pos, True, False, 5)
        for neighbor in neighbors:
            neighbor_obj = self.model.grid.get_cell_list_contents([neighbor])
            if (len(neighbor_obj) > 0):
                if isinstance(neighbor_obj[0], PassiveAgent):
                    self.model.knowledgeMap.update(PassiveAgentPerception(neighbor_obj[0]))
        if plan_count > 0:
            furthest_plan = my_plans[plan_count-1]
            self.plan = my_plans[0]
        else:
            furthest_plan = ActiveAgentPlanning(self, self.pos, 0)
        for i in range(6-plan_count):
            grid_at_state = self.model.knowledgeMap.getGridStateAtStep(furthest_plan.steps_left+1)
            neighbors = grid_at_state.get_neighborhood(furthest_plan.pos , True, False)
            empty_cells = [cell for cell in neighbors if grid_at_state.is_cell_empty(cell)]
            if len(empty_cells) > 0:
                choice = self.random.choice(empty_cells)
                new_plan = ActiveAgentPlanning(self, choice, furthest_plan.steps_left+1)
                self.model.knowledgeMap.update(new_plan)
                self.model.schedule.add(new_plan)
                if new_plan.steps_left == 1:
                    self.plan = new_plan
                furthest_plan = new_plan


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

    def interact(target, tool): #for the taking and returning of farm equipment
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