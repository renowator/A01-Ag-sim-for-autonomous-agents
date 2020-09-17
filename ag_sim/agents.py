from mesa import Agent
from statemachine import State, StateMachine

class PassiveAgentStateMachine(StateMachine):
    start = State("start", initial=True)
    end = State("end")
    transition = start.to(end)
    reset = start.from_(end)
    # TODO: Design a sophisticated StateMachine for piece of land

    def on_transition(self):
        print("Hurray")

class StateTracker(object):
    def __init__(self, state):
        self.state = state

class PassiveAgent(Agent):
    grid = None
    x = None
    y = None

    def __init__(self, unique_id, pos, model):
        super().__init__(unique_id, model)
        self.pos = pos
        self.agent_type = 'PASSIVE'
        self.current_state = StateTracker("start")
        self.machine = PassiveAgentStateMachine(self.current_state)

    def interact(agent):
        if (agent.type == 'ACTIVE'):
            switcher = {}
            func = switcher.get(agent.current_tool, lambda: None)
            if (func is not None):
                func()

    # TODO: implement interaction functions


    def sample_stage(self):
        # TODO: Implement random variability in state transitions

        if (self.machine.is_start):
            self.start()
        else:
            self.end()
        # Better but could not get to work
        #switcher = {self.machine.start: self.start, self.machine.end : self.end}
        #func = switcher.get(state,  None)
        #if (func is not None):
        #    func()

    # TODO: Implement switches of state with random element to it
    def start(self):
        self.machine.transition()

    def end(self):
        self.machine.reset()


class ActiveAgent(Agent):
    grid = None
    x = None
    y = None

    def __init__(self, unique_id, pos, model):
        super().__init__(unique_id, model)
        self.pos = pos
        self.agent_type = 'ACTIVE'
        self.targets = None
        self.mode = 'MOVE'
        self.current_tool = None

    def sample_stage(self):
        if (self.mode == 'MOVE'):
            next_moves = self.model.grid.get_neighborhood(self.pos, True, True)
            empty_cells = [cell for cell in next_moves if self.model.grid.is_cell_empty(cell)]
            if (empty_cells):
                self.model.grid.move_agent(self,self.random.choice(empty_cells))
        else:
            neighbors = self.model.grid.get_neighborhood(self.pos, True, True)
            for neighbor in neighbors:
                cell = self.model.grid.get_cell_list_contents([neighbor.pos])
                passive = [obj for obj in this_cell if isinstance(obj, PassiveAgent)]
                if len(passive) > 0:
                    passive[0].interact(self)
