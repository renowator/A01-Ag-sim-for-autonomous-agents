from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.UserParam import UserSettableParameter

from ag_sim.model import AgSimulator
from ag_sim.agents import PassiveAgent, ActiveAgent

def ag_sim_portrayal(agent):
    portrayal = {}
    if agent is None:
        return
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

canvas = CanvasGrid(ag_sim_portrayal, 50, 50, 500, 500)

model_params = {
    "active_agents": UserSettableParameter("slider", "Number of active agents", 5, 1, 20)
}

server = ModularServer(AgSimulator, [canvas], "Agriculture Simulation", model_params)
server.port = 8521
