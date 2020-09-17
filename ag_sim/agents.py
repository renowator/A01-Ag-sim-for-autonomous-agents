from mesa import Agent
from statemachine import State, StateMachine

class PassiveAgentStateMachine(StateMachine):
    start = State("START", initial=True)
    end = State("END")
    transition = start.to(end)
    reset = start._from(end)
    # TODO: Design a sophisticated StateMachine for piece of land

    def on_transition(self):
        print("Hurray")

class PassiveAgent(Agent):
    grid = None
    x = None
    y = None

    def __init__(self, unique_id, pos, model):
        super().__init__(unique_id, model)
        self.pos = pos
        self.agent_type = 'PASSIVE'
        self.machine = PassiveAgentStateMachine()

    def interact(agent):
        if (agent.type == 'ACTIVE'):
            switcher = {}
            func = switcher.get(agent.current_tool, lambda: None)
            if (func is not None):
                func()

    # TODO: implement interaction functions


    def step(self):
        # TODO: Implement random variability in state transitions
        switcher = {"START" : self.start, "END" : self.end}
        func = switcher.get(self.machine.current_state, lambda: None)
        if(func is not None):
            func()
    # TODO: Implement random switches of state
    def start(self):
        self.machine.transition()

    def end(self):
        self.machine.restart()


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

    def step(self):
        if (self.mode == 'MOVE'):
            next_moves = self.model.grid.get_neighborhood(self.pos, True, True)
            if (len(next_moves)>0):
                self.model.grid.move_agent(self, next_moves[0])
        else:
            neighbors = self.model.grid.get_neighborhood(self.pos, True, True)
            for neighbor in neighbors:
                cell = self.model.grid.get_cell_list_contents([neighbor.pos])
                passive = [obj for obj in this_cell if isinstance(obj, PassiveAgent)]
                if len(passive) > 0:
                    passive[0].interact(self)

        
