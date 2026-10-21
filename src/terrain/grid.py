"""The regular lat/lon grid that every feature and every prediction lives on."""
import math
from dataclasses import dataclass

from config.regions import Region


@dataclass(frozen=True)
class Grid:
    region: Region
    cell_m: int
    rows: int           # south to north
    cols: int           # west to east
    dlat: float         # cell height in degrees
    dlon: float         # cell width in degrees

    @classmethod
    def from_region(cls, region: Region, cell_m: int) -> "Grid":
        mid_lat = (region.south + region.north) / 2
        dlat = cell_m / 111_320
        dlon = cell_m / (111_320 * math.cos(math.radians(mid_lat)))
        rows = int((region.north - region.south) / dlat)
        cols = int((region.east - region.west) / dlon)
        return cls(region, cell_m, rows, cols, dlat, dlon)

    @property
    def n_cells(self) -> int:
        return self.rows * self.cols

    def cell_lonlat(self, row: int, col: int) -> tuple[float, float]:
        """Centre of a cell. Cell index i = row * cols + col."""
        return (self.region.west + (col + 0.5) * self.dlon,
                self.region.south + (row + 0.5) * self.dlat)
