from collections import defaultdict
from mesa.time import *
from ag_sim.agents import ActiveAgent, ActiveAgentPlanning

class ActivePassiveAgentActivation(SimultaneousActivation):

    def __init__(self, model):
        super().__init__(model)
        # TODO: Specify agent dictionary and stage parameters
        self._plan_agents = []

    def add(self, agent):
        """
        Add an Agent object to the schedule

        Args:
            agent: An Agent to be added to the schedule.
        """
        if (isinstance(agent, ActiveAgentPlanning)):
            self._plan_agents.append(agent)
        else:
            self._agents[agent.unique_id] = agent
        # TODO: Add agent to appropriate dictionary

    def remove(self, agent):
        """
        Remove all instances of a given agent from the schedule.
        """
        if (isinstance(agent, ActiveAgentPlanning)):
            self._plan_agents.remove(agent)
        else:
            del self._agents[agent.unique_id]

    def getPassiveAgent(self, id):
        return self._agents[id]

    def getPassiveAgentOnPos(self, pos):
        for each in self._agents:
            if self._agents[each].pos == pos:
                return self._agents[each]