from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.UserParam import UserSettableParameter
from collections import defaultdict
from ag_sim.model import AgSimulator
from ag_sim.agents import PassiveAgent, ActiveAgent

class AgSimGrid(CanvasGrid):
    def __init__(self,portrayal_method,grid_width,grid_height,canvas_width=500,canvas_height=500):
        super().__init__(portrayal_method, grid_width,grid_height, canvas_width, canvas_height)

    def render(self, model):
        grid_state = defaultdict(list)
        for x in range(model.grid.width):
            for y in range(model.grid.height):
                cell_objects = model.grid.get_cell_list_contents([(x, y)])
                if (len(cell_objects) > 0):
                    for obj in cell_objects:
                        portrayal = self.portrayal_method(obj)
                        portrayal["x"] = x
                        portrayal["y"] = y
                        if portrayal:
                            grid_state[portrayal["Layer"]].append(portrayal)
                else:
                    portrayal = self.portrayal_method(None)
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
        switcher = {agent.machine.start: ['#abb6c6', '#abb6c6', '#abb6c6'], agent.machine.plowed: ['#734b10', '#734b10', '#734b10'], agent.machine.baby: ["#84e184", "#adebad", "#d6f5d6"], agent.machine.growing : ["#00FF00", "#00CC00", "#009900"], agent.machine.flowering : ['#ffd700', '#ffd700', '#ffd700'], agent.machine.harvest : ['#f5821f','#f5821f', '#f5821f'], agent.machine.end: ['#abb6c6', '#abb6c6', '#abb6c6']}
        color = switcher.get(agent.machine.current_state,  None)
        portrayal["Color"] = ['#abb6c6', '#abb6c6', '#abb6c6']
        if (color is not None):
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
    return portrayal

canvas = AgSimGrid(ag_sim_portrayal, 50, 50, 500, 500)

model_params = {
    "active_agents": UserSettableParameter("slider", "Number of active agents", 5, 1, 20)
}

server = ModularServer(AgSimulator, [canvas], "Agriculture Simulation", model_params)
server.port = 8521
