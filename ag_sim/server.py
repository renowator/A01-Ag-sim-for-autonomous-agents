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
        if agent.machine.is_start:
            portrayal["Color"] = ["#00FF00", "#00CC00", "#009900"]
        else:
            portrayal["Color"] = ["#84e184", "#adebad", "#d6f5d6"]
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
