from collections import defaultdict
from mesa.time import StagedActivation

class ActivePassiveAgentActivation(StagedActivation):

    def __init__(self, model, stage_list = None, shuffle = False, shuffle_between_stages = False):
        super().__init__(model, stage_list, shuffle, shuffle_between_stages)
        # TODO: Specify agent dictionary and stage parameters

    def add(self, agent):
        """
        Add an Agent object to the schedule

        Args:
            agent: An Agent to be added to the schedule.
        """
        self._agents[agent.unique_id] = agents
        # TODO: Add agent to appropriate dictionary

    def remove(self, agent):
        """
        Remove all instances of a given agent from the schedule.
        """
        del self._agents[agent.unique_id]

    def step(self):
        # TODO: implement stages: ["Active", "Passive"]
        if (self.stage_list is None):
            for agent in self._agents:
                agent.step()
