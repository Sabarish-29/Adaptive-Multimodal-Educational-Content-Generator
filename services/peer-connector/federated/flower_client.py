"""Flower federated learning client."""

from typing import Dict, Any


class FlowerClient:
    """
    Flower (flwr) federated learning client.
    Allows each student's model updates to remain local while
    participating in global model improvement.
    """

    def __init__(self, server_address: str = "flower-server:8080"):
        self._server = server_address
        self._client = None

    async def start(self):
        """Connect to the Flower server and begin FL participation."""
        # TODO: implement flwr.client.NumPyClient subclass
        pass

    def get_parameters(self) -> Dict[str, Any]:
        """Return local model parameters for aggregation."""
        return {"parameters": [], "num_examples": 0}

    def fit(self, parameters, config) -> tuple:
        """Train on local data and return updated parameters."""
        # TODO: local training step
        return parameters, 0, {}

    def evaluate(self, parameters, config) -> tuple:
        """Evaluate model on local data."""
        return 0.0, 0, {"accuracy": 0.0}
