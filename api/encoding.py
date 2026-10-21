import base64

import numpy as np


def b64_uint8(a: np.ndarray) -> str:
    """Pack an array of small ints into base64 so a whole frame is one short string."""
    return base64.b64encode(a.astype(np.uint8).tobytes()).decode()
