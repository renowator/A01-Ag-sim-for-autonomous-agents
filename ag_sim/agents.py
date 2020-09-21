from mesa import Agent
from statemachine import State, StateMachine
import random

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
            self.machine.plow()
    
    def sow(self):
        if ( self.machine.current_state == self.machine.plowed):
            self.machine.sow()

    def cure(self):
        # Baby
        if ( self.machine.current_state == self.machine.baby_sick):
            self.machine.sick_baby_recovery()
        # growing
        if ( self.machine.current_state == self.machine.growing):
            self.machine.sick_growing_recovery()
        # Flowering
        if ( self.machine.current_state == self.machine.flowering_sick):
            self.machine.sick_flowering_recovery()

    def kill_weeds(self):
        # Baby
        if ( self.machine.current_state == self.machine.baby_weeds):
            self.machine.weeds_baby_recovery()
        # growing
        if ( self.machine.current_state == self.machine.growing_weeds):
            self.machine.weeds_growing_recovery()
        # Flowering
        if ( self.machine.current_state == self.machine.flowering_weeds):
            self.machine.weeds_flowering_recovery()

    def water(self):
        if ( self.machine.current_state in self.machine.waterable_states):
            return
            #TODO: Add watering effects

    def harvest(self):
        if ( self.machine.current_state == self.machine.harvestable):
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
        elif (self.random.random() < 0.01):
            self.time_at_current_state = 0
            self.machine.sick_baby()
        elif (self.random.random() < 0.05):
            self.time_at_current_state = 0
            self.machine.weeds_baby()

    def when_growing(self):
        return

    def when_flowering(self):
        return

    def when_harvest(self):
        return




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
        self.current_tool = random.choice(['PLOW'])

    def sample_stage(self):
        if (self.mode == 'MOVE'):
            next_moves = self.model.grid.get_neighborhood(self.pos, True, True)
            empty_cells = [cell for cell in next_moves if self.model.grid.is_cell_empty(cell)]
            if (empty_cells):
                self.model.grid.move_agent(self,self.random.choice(empty_cells))
                self.mode = 'TEST'
        else:
            neighbors = self.model.grid.get_neighborhood(self.pos, True, True)
            for neighbor in neighbors:
                cell = self.model.grid.get_cell_list_contents([neighbor])
                passive = [obj for obj in cell if isinstance(obj, PassiveAgent)]
                if len(passive) > 0:
                    passive[0].interact(self)
                self.mode = 'MOVE'
