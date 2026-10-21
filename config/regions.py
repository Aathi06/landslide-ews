"""Study regions. To add one, add an entry to REGIONS: nothing else changes."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Region:
    key: str
    name: str
    south: float
    north: float
    west: float
    east: float

    @property
    def center(self) -> tuple[float, float]:
        """(lon, lat) of the box centre, used as the map's starting view."""
        return ((self.west + self.east) / 2, (self.south + self.north) / 2)


REGIONS = {
    "nilgiris": Region("nilgiris", "Nilgiris, Tamil Nadu", 11.25, 11.55, 76.55, 76.95),
    "wayanad": Region("wayanad", "Wayanad, Kerala", 11.55, 11.90, 75.90, 76.35),
}
DEFAULT_REGION = "nilgiris"
