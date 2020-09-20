from mesa import Agent
from statemachine import State, StateMachine

class PassiveAgentStateMachine(StateMachine):
    # All Possible states of a soil patch
    start = State("start", initial=True)
    baby = State("baby")
    baby_diseased = State("baby_diseased")
    baby_weeds = State("baby_weeds")
    growth = State("growth")
    growth_diseased = State("growth_diseased")
    growth_weeds = State("growth_weeds")
    unhappy_growth = State("unhappy_growth")
    flowering = State("flowering")
    flowering_diseased = State("flowering_diseased")
    flowering_weeds = State("flowering_weeds")
    harvest = State("harvest")
    end = State("end")
    # The transitions for soil state machine
    plow_and_seed = start.to(baby)
    # Baby plant transitions
    diseased_baby = baby.to(baby_diseased)
    diseased_baby_death = baby_diseased.to(end)
    diseased_baby_recovery = baby_diseased.to(baby)

    weeds_baby = baby.to(baby_weeds)
    kill_weeds_baby = baby_weeds.to(baby)
    weeds_baby_death = baby_weeds.to(end)

    baby_grown = baby.to(growth)
    # Grown plant transitions
    diseased_growth = growth.to(growth_diseased)
    diseased_growth_death = growth_diseased.to(end)
    diseased_growth_recovery = growth_diseased.to(growth)
    weeds_growth = growth.to(growth_weeds)
    kill_weeds_growth = growth_weeds.to(growth)
    weeds_growth_death = growth_weeds.to(end)
    low_nutrition = growth.to(unhappy_growth)
    death_from_low_nutrition = unhappy_growth.to(end)

    growth_to_flower = growth.to(flowering)
    # Flowering plant transitions
    diseased_flower = flowering.to(flowering_diseased)
    diseased_flower_death = flowering_diseased.to(end)
    diseased_flower_recovery = flowering_diseased.to(flowering)
    weeds_flower = flowering.to(flowering_weeds)
    kill_weeds_flower = flowering_weeds.to(flowering)
    weeds_flower_death = flowering_weeds.to(end)
    # Harvest
    ready_to_harvest = flowering.to(harvest)
    finish = harvest.to(end)
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
            switcher = {'PLOW' : self.plow}
            func = switcher.get(agent.current_tool, lambda: None)
            if (func is not None):
                func()

    # TODO: implement interaction functions (interaction functions are what the active agent does to the soil)
    def plow(self):
        if ( self.machine.current_state == self.machine.start):
            self.machine.plow_and_seed()

    # Here only elements essential to the plants itself are updated (random growth of weeds or spread of disease, check if enough energy to survive, etc)
    def sample_stage(self):
        self.time_at_current_state += 1
        # TODO: Implement random variability in state transitions
        switcher = {self.machine.baby: self.when_baby, self.machine.growth : self.when_growth, self.machine.flowering : self.when_flowering, self.machine.harvest : self.when_harvest}
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
            self.machine.diseased_baby()
        elif (self.random.random() < 0.05):
            self.time_at_current_state = 0
            self.machine.weeds_baby()

    def when_growth(self):
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
        self.current_tool = 'PLOW'

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
