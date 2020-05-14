from sys import path
path.append('../')

from random import randint
from bof import knx, byte

def all_frames() -> knx.KnxFrame:
    """Generator for all existing types of frames based on the JSON
    specifications file.
    """
    specs = knx.KnxSpec()
    for sid in specs.service_identifiers:
        # If the frame has a cEMI block, we try all cEMI possibilities
        if "cemi" in [template["type"] for template in specs.bodies[sid]]: 
            for cemi_type in specs.cemis:
                yield knx.KnxFrame(type=sid, cemi=cemi_type)
        else:
            yield knx.KnxFrame(type=sid)

def mutate(frame:bytes) -> (bytes, list):
    """Randomly change bytes in frame.
    Saves the index on modified ones to keep track.
    """
    changelog = []
    frame = bytearray(frame) # Use a mutable object instead
    for _ in range(randint(0,len(frame)-1)): # Random number of times
        idx = randint(0,len(frame)-2) # Random position
        frame[idx:idx+1] = [randint(0,255)] # Random value
        changelog.append(str(idx)) # We save the position with changed bytes
    return bytes(frame), changelog

def generate_inputs(frame:bytes, trials:int=10) -> bytes:
    """Generate a number of ``inputs` inputs for each type of frame."""

def fuzz(generator:object, trials:int=10):
    """Retrieve the complete list of inputs"""
    for frame in generator():
        for _ in range(trials):
            mutated_frame, changelog = mutate(bytes(frame))
            yield mutated_frame, frame, changelog


# For each existing type of frame (in specification file), create 10 different
# frames with random mutations and send them to the tested device.

for trial, original, changelog in fuzz(all_frames, 10):
    print("+ Sending: {0}".format(trial))
    print("++ Type: {0} - Modified fields: {1}".format(original.sid, ",".join(changelog)))
