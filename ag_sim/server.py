from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.UserParam import UserSettableParameter

from ag_sim.model import AgSimulator

server = ModularServer(AgSimulator, [], "Agriculture Simulation", {})
server.port = 8521
