from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid, ChartModule, TextElement
from mesa.visualization.UserParam import UserSettableParameter
from collections import defaultdict
from ag_sim.model import AgSimulator
from ag_sim.agents import PassiveAgent, ActiveAgent, PassiveAgentPerception, ActiveAgentPlanning, PassiveAgentStateMachine, FarmAgent


'''
*** AgSimGrid is a visualizer class for AgSimulator
*** It visualizes the Model.grid as well as the knowledgeMap of Agents
*** CanvasGrid.render is overriden to loop through more grids, nothing else
*** Refer to CanvasGrid
'''


class AgSimGrid(CanvasGrid):
    def __init__(self, portrayal_method, grid_width, grid_height, canvas_width=500, canvas_height=500):
        super().__init__(portrayal_method, grid_width,
                         grid_height*2, canvas_width, canvas_height*2)

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
                        portrayal["y"] = y + model.grid.height
                        if portrayal:
                            grid_state[portrayal["Layer"]].append(portrayal)
                else:
                    portrayal = self.portrayal_method(None)
                    portrayal["x"] = x
                    portrayal["y"] = y + model.grid.height
                    if portrayal:
                        grid_state[portrayal["Layer"]].append(portrayal)
        # Display navigationGrid from ActiveAgentKnowledgeMap
        for x in range(model.grid.width):
            for y in range(model.grid.height):
                cell_objects = model.knowledgeMap.navigationGrid.get_cell_list_contents([
                                                                                        (x, y)])
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
                cell_objects = model.knowledgeMap.planGrid.get_cell_list_contents([
                                                                                  (x, y)])
                if (len(cell_objects) > 0):
                    for obj in cell_objects:
                        portrayal = self.portrayal_method(obj)
                        portrayal["x"] = x
                        portrayal["y"] = y
                        if portrayal:
                            grid_state[portrayal["Layer"]].append(portrayal)

        return grid_state

# How colors for the agents are determined


def ag_sim_portrayal(agent):
    portrayal = {}
    if agent is None:
        portrayal["Color"] = ["#d4ccbe", "#d4ccbe", "#d4ccbe"]
        portrayal["Shape"] = "rect"
        portrayal["Filled"] = "true"
        portrayal["Layer"] = 1
        portrayal["w"] = 1
        portrayal["h"] = 1
    elif type(agent) is FarmAgent:
        portrayal["Color"] = ["#8a0000", "#8a0000", "#8a0000"]
        portrayal["Shape"] = "rect"
        portrayal["Filled"] = "true"
        portrayal["Layer"] = 1
        portrayal["w"] = 1
        portrayal["h"] = 1
    elif type(agent) is PassiveAgent:
        # Tints for sick and weeds states
        sick_tint = "#0043fc"  # Blue
        weeds_tint = "#ff00f2"  # Pink
        dehydrated_tint = "#49007a"  # Purple

        switcher = {
            # Start state colors
            # light brown
            PassiveAgentStateMachine.start: ['#8f713c', '#8f713c', '#8f713c'],
            # Plowed state colors
            # dark brown
            PassiveAgentStateMachine.plowed: ['#734b10', '#734b10', '#734b10'],
            # Seed state colors
            # light green
            PassiveAgentStateMachine.seed: ["#84e184", "#adebad", "#d6f5d6"],
            PassiveAgentStateMachine.seed_sick: ["#84e184", "#adebad", sick_tint],
            PassiveAgentStateMachine.seed_weeds: ["#84e184", "#adebad", weeds_tint],
            PassiveAgentStateMachine.seed_dry: ["#84e184", "#adebad", dehydrated_tint],
            # Growing state colors
            # dark green
            PassiveAgentStateMachine.growing: ["#00FF00", "#00CC00", "#009900"],
            PassiveAgentStateMachine.growing_sick: ["#00FF00", "#00CC00", sick_tint],
            PassiveAgentStateMachine.growing_weeds: ["#00FF00", "#00CC00", weeds_tint],
            PassiveAgentStateMachine.growing_dry: ["#00FF00", "#00CC00", dehydrated_tint],
            # Flowering state colors
            # yellow
            PassiveAgentStateMachine.flowering: ['#fffd73', '#faf743', '#f7f416'],
            PassiveAgentStateMachine.flowering_sick: ['#fffd73', '#faf743', sick_tint],
            PassiveAgentStateMachine.flowering_weeds: ['#fffd73', '#faf743', weeds_tint],
            PassiveAgentStateMachine.flowering_dry: ['#fffd73', '#faf743', dehydrated_tint],

            # Harvestable state colors
            # Orange
            PassiveAgentStateMachine.harvestable: ['#ffd06b', '#ffc240', '#ffb10a'],
            PassiveAgentStateMachine.harvestable_sick: ['#ffd06b', '#ffc240', sick_tint],
            PassiveAgentStateMachine.harvestable_weeds: ['#ffd06b', '#ffc240', weeds_tint],
            PassiveAgentStateMachine.harvestable_dry: ['#ffd06b', '#ffc240', dehydrated_tint],
            # End state colors
            PassiveAgentStateMachine.dead: ['#000000', '#000000', '#000000'],
            PassiveAgentStateMachine.harvested: [
                '#FFFFFF', '#FFFFFF', '#FFFFFF']
        }
        color = switcher.get(agent.machine.current_state,  [
                             '#abb6c6', '#abb6c6', '#abb6c6'])
        portrayal["Color"] = color
        portrayal["Shape"] = "rect"
        portrayal["Filled"] = "true"
        portrayal["Layer"] = 1
        portrayal["w"] = 1
        portrayal["h"] = 1
    elif type(agent) is ActiveAgent:
        portrayal["Color"] = ["#FF3300", "#FF3300", "#FF3300"]
        portrayal["Shape"] = "circle"
        portrayal["Filled"] = "true"
        portrayal["Layer"] = 1
        portrayal["r"] = 1
    elif type(agent) is ActiveAgentPlanning:
        switcher = {0: ['#97649e', '#97649e', '#97649e'], 1: ['#aa68af', '#aa68af', '#aa68af'], 2: ["#bd6dc1", "#bd6dc1", "#bd6dc1"], 3: [
            "#cf72d2", "#cf72d2", "#cf72d2"], 4: ['#e276e4', '#e276e4', '#e276e4'], 5: ['#f57bf5', '#f57bf5', '#f57bf5'], 6: ['#ea317b', '#ea317b', '#ea317b']}
        color = switcher.get(agent.steps_left,   [
                             '#ea317b', '#ea317b', '#ea317b'])
        portrayal["Color"] = color
        portrayal["Shape"] = "rect"
        portrayal["Filled"] = "true"
        portrayal["Layer"] = 1
        portrayal["w"] = 1
        portrayal["h"] = 1
    elif type(agent) is PassiveAgentPerception:
        switcher = {PassiveAgentStateMachine.start: ['#abb6c6', '#abb6c6', '#abb6c6'], PassiveAgentStateMachine.plowed: ['#734b10', '#734b10', '#734b10'], PassiveAgentStateMachine.seed: ["#84e184", "#adebad", "#d6f5d6"], PassiveAgentStateMachine.growing: [
            "#00FF00", "#00CC00", "#009900"], PassiveAgentStateMachine.flowering: ['#ffd700', '#ffd700', '#ffd700'], PassiveAgentStateMachine.harvest: ['#f5821f', '#f5821f', '#f5821f'], PassiveAgentStateMachine.dead: ['#abb6c6', '#abb6c6', '#abb6c6']}
        color = switcher.get(agent.state,   ['#008080', '#008080', '#008080'])
        portrayal["Color"] = color
        portrayal["Shape"] = "rect"
        portrayal["Filled"] = "true"
        portrayal["Layer"] = 1
        portrayal["w"] = 1
        portrayal["h"] = 1
    return portrayal

# Class for representing the legend


class ag_sim_legend(TextElement):
    def __init__(self):
        self.legend_dict = {
            "Farm": "#8a0000",
            "Active farming agent": "#FF3300",
            "Road": "#d4ccbe",
            "Starting field": "#8f713c",
            "Plowed field": "#734b10",
            "Seed crop": "#adebad",
            "Growing crop": "#00CC00",
            "Flowering crop": "#faf743",
            "Harvestable crop": "#ffc240",
            "Infected with weeds": "#ff00f2",
            "Sick": "#0043fc",
            "Dehydrated": "#4f1e8f",
            "Death crop": "#000000",
            "Harvested crop": "#FFFFFF"
        }

    def create_legend_row(self, name, color):
        return "<ul><div class='input-color'><input type='text' value='" + name + "' disabled/><div class='color-box' style='background-color: " + color + ";'></div></div></ul>"

    def render(self, model):
        css = "<style>ul{display: inline-block;} .input-color {position: relative; margin:0px;}.input-color input {padding-left: 20px; font-size:small;}.input-color .color-box {width: 10px;height: 10px; margin-top: 7px; display: inline-block;background-color: #ccc;position: absolute;left: 5px;top: 5px;}</style>"

        title = "<hr><div><h4>Legend</h4></div>"

        all_legend_rows = ""
        for name, color in self.legend_dict.items():
            all_legend_rows += self.create_legend_row(name, color)

        return css + "<div style='background-color:whitesmoke;padding:5px;'" + title + "<ul style='position:relative; left:-80px;'>" + all_legend_rows + "</ul></div>"


canvas = AgSimGrid(ag_sim_portrayal, 50, 50, 500, 500)

# Create the legend
legend = ag_sim_legend()

# The parameters that can be changed in the browser are defined here
model_params = {

    "static_text": UserSettableParameter('static_text', value="<b>About</b><br>Shown below are all settable agent parameters. The legend shown on the right pertains only to the first map, which shows the position and states of all agents. The second map represents the knowledgemap of the active agents. "),
    "active_agents": UserSettableParameter("slider", "Number of active agents", 6, 6, 30),
    "com_protocol": UserSettableParameter("choice", "Communication protocol", value="Helper-Based protocol", choices=["Simple protocol", "Helper-Based protocol", "Coordination Cooperative protocol"]),

    # Water, sick, and weeds states
    "max_water_level": UserSettableParameter("number", "A crops maximum water level (in steps)", 750, 1, 100000),
    "max_steps_dehydrated": UserSettableParameter("number", "Maximum number of steps in a dehydrated state", 500, 1, 100000),
    "max_steps_sick": UserSettableParameter("number", "Maximum number of steps in the sick state", 500, 1, 100000),
    "max_steps_weeds": UserSettableParameter("number", "Maximum number of steps in the weeds state", 500, 1, 100000),
    # Seed crop parameters
    "seed_sick_probability": UserSettableParameter("number", "Probability of seed getting sick", 0.0005, 0, 1),
    "seed_weeds_probability": UserSettableParameter("number", "Probability of seed getting weeds", 0.0005, 0, 1),
    "steps_seed_to_growing": UserSettableParameter("number", "Steps between a crop's seed and growing state", 1000, 1, 100000),
    # Growing crop parameters
    "growing_sick_probability": UserSettableParameter("number", "Probability of growing getting sick", 0.0005, 0, 1),
    "growing_weeds_probability": UserSettableParameter("number", "Probability of growing getting weeds", 0.0005, 0, 1),
    "steps_growing_to_flowering": UserSettableParameter("number", "Steps between a crop's growing and flowering state", 1000, 1, 100000),
    # Flowering crop parameters
    "flowering_sick_probability": UserSettableParameter("number", "Probability of flowering getting sick", 0.0005, 0, 1),
    "flowering_weeds_probability": UserSettableParameter("number", "Probability of flowering getting weeds", 0.0005, 0, 1),
    "steps_flowering_to_harvestable": UserSettableParameter("number", "Steps between a crop's flowering and harvestable state", 1000, 1, 100000),
    # Harvestable crop parameters
    "harvestable_sick_probability": UserSettableParameter("number", "Probability of harvestable getting sick", 0.0005, 0, 1),
    "harvestable_weeds_probability": UserSettableParameter("number", "Probability of harvestable getting weeds", 0.0005, 0, 1),
    "steps_harvestable_to_dead": UserSettableParameter("number", "Maximum number of steps that a crop can be in the harvestable state before dying", 500, 1, 100000),
}

server = ModularServer(
    AgSimulator, [legend, canvas], "Agriculture Simulation", model_params)
server.port = 8521
