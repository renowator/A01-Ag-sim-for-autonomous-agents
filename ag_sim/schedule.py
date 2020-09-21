from collections import defaultdict
from mesa.time import StagedActivation
from ag_sim.agents import ActiveAgent, ActiveAgentPlanning

class ActivePassiveAgentActivation(StagedActivation):

    def __init__(self, model, stage_list = ["passive_stage", "sample_stage"], shuffle = False, shuffle_between_stages = False):
        super().__init__(model, stage_list, shuffle, shuffle_between_stages)
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

    def step(self):
        # TODO: implement stages: ["Active", "Passive"]
        if (len(self.stage_list) == 1):
            agent_keys = [uid for uid, a in self._agents.items()]
            # run stage for each agent in group
            for agent_key in agent_keys:
                getattr(self._agents[agent_key], self.stage_list[0])()
            for agent in self._plan_agents:
                getattr(agent, self.stage_list[0])()
