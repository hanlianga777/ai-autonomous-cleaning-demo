"""Approved destination registry, independent of model-generated coordinates."""
from typing import Protocol

from spatial.spatial_data import MAPS

POIS = {
    "a1-lobby": {"label": "A栋1F大堂待命点", "map_id": "A_1F", "x": 52, "y": 29},
    "a1-delivery": {"label": "A栋1F配送取件点", "map_id": "A_1F", "x": 72, "y": 30},
    "a2-corridor": {"label": "A栋2F通道交接点", "map_id": "A_2F", "x": 57, "y": 26},
    "b1-lobby": {"label": "B栋1F大堂待命点", "map_id": "B_1F", "x": 51, "y": 28},
    "b2-lobby": {"label": "B栋2F连廊交接点", "map_id": "B_2F", "x": 57, "y": 26},
    "outdoor-standby": {"label": "室外道路待命点", "map_id": "OUTDOOR", "x": 24, "y": 40},
}

# Explicit deployment permissions for the native delivery PoC. These describe
# the simulator's allowed topology, not production elevator/access credentials.
DELIVERY_DEPLOYMENT_POLICY = {"robot-d": {"service_scope": "indoor", "elevator": True, "skybridge": True, "source": "POC_SIMULATION"}}


def poi(key):
    if key not in POIS:
        raise ValueError("Destination must be an approved POI; arbitrary x/y is forbidden.")
    value = POIS[key]
    spatial_map = next(item for item in MAPS if item["map_id"] == value["map_id"])
    return {"poi_id": key, **value, "building": spatial_map["building"], "floor": spatial_map["floor"]}


class ExternalDeliveryAdapter(Protocol):
    def status(self) -> dict: ...
    def submit(self, task: dict) -> dict: ...


class AuthorizationRequiredAdapter:
    def __init__(self, platform):
        self.platform = platform

    def status(self):
        return {"platform": self.platform, "adapter": "ADAPTER READY", "authorization": "AUTH REQUIRED", "connected": False}

    def submit(self, task):
        raise ValueError("External platform authorization is not configured; no order was submitted.")


DELIVERY_ADAPTERS = {name: AuthorizationRequiredAdapter(name) for name in ("美团", "饿了么", "京东", "淘宝闪购")}
