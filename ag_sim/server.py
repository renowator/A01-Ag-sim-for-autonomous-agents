from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.UserParam import UserSettableParameter
from collections import defaultdict
from ag_sim.model import AgSimulator
from ag_sim.agents import PassiveAgent, ActiveAgent, PassiveAgentPerception, ActiveAgentPlanning, PassiveAgentStateMachine

class AgSimGrid(CanvasGrid):
    def __init__(self,portrayal_method,grid_width,grid_height,canvas_width=500,canvas_height=500):
        super().__init__(portrayal_method, grid_width,grid_height*2, canvas_width, canvas_height*2)

    def render(self, model):
        grid_state = defaultdict(list)
        # Display simulation map
        for x in range(model.grid.width):
            for y in range(model.grid.height):
                cell_objects = model.grid.get_cell_list_contents([(x, y)])
                if (len(cell_objects) > 0):
                    for obj in cell_objects:
                        portrayal = self.portrayal_method(obj)
                        portrayal["x"] = x
                        portrayal["y"] = y+ model.grid.height
                        if portrayal:
                            grid_state[portrayal["Layer"]].append(portrayal)
                else:
                    portrayal = self.portrayal_method(None)
                    portrayal["x"] = x
                    portrayal["y"] = y+ model.grid.height
                    if portrayal:
                        grid_state[portrayal["Layer"]].append(portrayal)
        # Display navigationGrid from ActiveAgentKnowledgeMap
        for x in range(model.grid.width):
            for y in range(model.grid.height):
                cell_objects = model.knowledgeMap.navigationGrid.get_cell_list_contents([(x, y)])
                if (len(cell_objects) > 0):
                    for obj in cell_objects:
                        portrayal = self.portrayal_method(obj)
                        portrayal["x"] = x
                        portrayal["y"] = y
                        if portrayal:
                            grid_state[portrayal["Layer"]].append(portrayal)
        # Display planGrid for ActiveAgentKnowledgeMap
        for x in range(model.grid.width):
            for y in range(model.grid.height):
                cell_objects = model.knowledgeMap.planGrid.get_cell_list_contents([(x, y)])
                if (len(cell_objects) > 0):
                    for obj in cell_objects:
                        portrayal = self.portrayal_method(obj)
                        portrayal["x"] = x
                        portrayal["y"] = y
                        if portrayal:
                            grid_state[portrayal["Layer"]].append(portrayal)

        return grid_state


def ag_sim_portrayal(agent):
    portrayal = {}
    if agent is None:
        portrayal["Color"] = ["#D18F52", "#D18F52", "#D18F52"]
        portrayal["Shape"] = "rect"
        portrayal["Filled"] = "true"
        portrayal["Layer"] = 1
        portrayal["w"] = 1
        portrayal["h"] = 1
    elif type(agent) is PassiveAgent:
        switcher = {PassiveAgentStateMachine.start: ['#abb6c6', '#abb6c6', '#abb6c6'], PassiveAgentStateMachine.plowed: ['#734b10', '#734b10', '#734b10'], PassiveAgentStateMachine.baby: ["#84e184", "#adebad", "#d6f5d6"], PassiveAgentStateMachine.growing : ["#00FF00", "#00CC00", "#009900"], PassiveAgentStateMachine.flowering : ['#ffd700', '#ffd700', '#ffd700'], PassiveAgentStateMachine.harvest : ['#f5821f','#f5821f', '#f5821f'], PassiveAgentStateMachine.end: ['#abb6c6', '#abb6c6', '#abb6c6']}
        color = switcher.get(agent.machine.current_state,  ['#abb6c6', '#abb6c6', '#abb6c6'])
        portrayal["Color"] = color
        portrayal["Shape"] = "rect"
        portrayal["Filled"] = "true"
        portrayal["Layer"] = 1
        portrayal["w"] = 1
        portrayal["h"] = 1
    elif type(agent) is ActiveAgent:
        portrayal["Color"] = ["#FF3300", "#FF3300", "#FF3300"]
        portrayal["Shape"] = "rect"
        portrayal["Filled"] = "true"
        portrayal["Layer"] = 1
        portrayal["w"] = 1
        portrayal["h"] = 1
    elif type(agent) is ActiveAgentPlanning:
        switcher = {0: ['#97649e', '#97649e', '#97649e'], 1: ['#aa68af', '#aa68af', '#aa68af'], 2: ["#bd6dc1", "#bd6dc1", "#bd6dc1"], 3 : ["#cf72d2", "#cf72d2", "#cf72d2"], 4 : ['#e276e4', '#e276e4', '#e276e4'],5 : ['#f57bf5','#f57bf5', '#f57bf5']}
        color = switcher.get(agent.steps_left,   ['#008080', '#008080', '#008080'])
        portrayal["Color"] = color
        portrayal["Shape"] = "rect"
        portrayal["Filled"] = "true"
        portrayal["Layer"] = 1
        portrayal["w"] = 1
        portrayal["h"] = 1
    elif type(agent) is PassiveAgentPerception:
        switcher = {PassiveAgentStateMachine.start: ['#abb6c6', '#abb6c6', '#abb6c6'], PassiveAgentStateMachine.plowed: ['#734b10', '#734b10', '#734b10'], PassiveAgentStateMachine.baby: ["#84e184", "#adebad", "#d6f5d6"], PassiveAgentStateMachine.growing : ["#00FF00", "#00CC00", "#009900"], PassiveAgentStateMachine.flowering : ['#ffd700', '#ffd700', '#ffd700'], PassiveAgentStateMachine.harvest : ['#f5821f','#f5821f', '#f5821f'], PassiveAgentStateMachine.end: ['#abb6c6', '#abb6c6', '#abb6c6']}
        color = switcher.get(agent.state,   ['#008080', '#008080', '#008080'])
        portrayal["Color"] = color
        portrayal["Shape"] = "rect"
        portrayal["Filled"] = "true"
        portrayal["Layer"] = 1
        portrayal["w"] = 1
        portrayal["h"] = 1
    return portrayal

canvas = AgSimGrid(ag_sim_portrayal, 50, 50, 500, 500)

model_params = {
    "active_agents": UserSettableParameter("slider", "Number of active agents", 5, 1, 20)
}

server = ModularServer(AgSimulator, [canvas], "Agriculture Simulation", model_params)
server.port = 8521
