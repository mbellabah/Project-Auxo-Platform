# TODO:


class Agent:
    def __init__(self, agent_id: int = 0):
        self.agent_id: int = agent_id

        self.logger.info(f"Starting Agent-{self.agent_id}")
