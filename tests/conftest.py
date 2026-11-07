import os

# Tests always run on synthetic terrain so they never depend on downloaded data or the network.
os.environ["EWS_TERRAIN"] = "mock"
