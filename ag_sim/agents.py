from mesa import Agent
from statemachine import State, StateMachine


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





class PassiveAgent(Agent):
    grid = None
    x = None
    y = None

    def __init__(self, unique_id, pos, model):
        super().__init__(unique_id, model)
        self.pos = pos
        self.agent_type = 'PASSIVE'
        self.machine = PassiveAgentStateMachine()
        self.time_at_current_state = 0

    def interact(self, agent):
        if (agent.agent_type == 'ACTIVE'):
            switcher = {'PLOW' : self.plow, 'SOW' : self.sow, 'CURE' : self.cure, 'PESTICIDES' : self.kill_weeds,
            'WATERING_TOOL' : self.water, 'HARVESTING_TOOL' : self.harvest}
            func = switcher.get(agent.current_tool, lambda: None)
            if (func is not None):
                func()

    # Interaction functions for interactions between active and passive agents
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



    # Here only elements essential to the plants itself are updated (random growing of weeds or spread of disease, check if enough energy to survive, etc)
    def sample_stage(self):
        self.time_at_current_state += 1
        # TODO: Implement random variability in state transitions
        switcher = {self.machine.baby: self.when_baby, self.machine.growing : self.when_growing, self.machine.flowering : self.when_flowering, self.machine.harvest : self.when_harvest}
        func = switcher.get(self.machine.current_state,  None)
        if (func is not None):
            func()

    # TODO: Implement switches of state with random element to it
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

# This class is used to track PassiveObjects on the AgentKnowledgeMap.navigationGrid
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




class ActiveAgent(Agent):
    grid = None
    x = None
    y = None

    def __init__(self, unique_id, pos, model):
        super().__init__(unique_id, model)
        self.pos = pos
        self.agent_type = 'ACTIVE'
        self.targets = None
        self.mode = 'TEST'
        self.current_tool = self.random.choice(['PLOW', 'SOW'])
        self.plan = None
    '''
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
