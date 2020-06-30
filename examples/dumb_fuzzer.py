from sys import path, argv
path.append('../')

from random import randint
from bof import BOFNetworkError, knx, byte

def all_frames() -> knx.KnxFrame:
    specs = knx.KnxSpec()
    for sid in specs.service_identifiers: 
        # If the frame has a cEMI block, we try all cEMI possibilities
        if "cemi" in [template["type"] for template in specs.bodies[sid]]: 
            for cemi_type in specs.cemis:
                yield knx.KnxFrame(type=sid, cemi=cemi_type)
        else:
            yield knx.KnxFrame(type=sid)

def mutate(frame:bytes) -> (bytes, list):
    changelog = []
    frame = bytearray(frame) # We use a mutable object instead
    for _ in range(randint(1,len(frame)-1)): # Random number of times
        idx = randint(0,len(frame)-2) # Random location
        frame[idx:idx+1] = [randint(0,255)] # Random value
        changelog.append(str(idx)) # We save the location
    return bytes(frame), changelog

def fuzz(generator:object, trials:int=10) -> tuple:
    for frame in generator():
        for _ in range(trials):
            mutated_frame, changelog = mutate(bytes(frame))
            yield mutated_frame, frame, changelog

    def save(reason:str, trial:bytes, original:object, changelog:list,\
            response:object=None):
       # We print it but we should store it
       print("[{0}] Type: {1}".format(reason, original.sid))
       print("---- Original frame; {0}".format(original))
       print("---- Mutated frame;  {0}".format(trial))
       print("---- Modified fields: {0}".format(", ".join(changelog)))
       if response:
           print("---- Response: {0}".format(response))

# RUN
if len(argv) < 2:
    print("Usage: python {0} IP_ADDRESS".format(argv[0]))
else:
    knxnet = knx.KnxNet()
    knxnet.connect(argv[1], 3671)
    for trial, original, changelog in fuzz(all_frames, 100):
        print("+ Sending: {0} ({1})".format(trial,", ".join(changelog)))
        try:
            response = knxnet.send_receive(trial)
        except BOFNetworkError:
            # No response received, send_receive() timed out
            # We send a valid frame to check if the device is still alive
            heartbeat = knxnet.send_receive(knx.KnxFrame(type="DESCRIPTION REQUEST"))
            if not heartbeat:
                save("Target crashed", trial, original, changelog)
                break
        else:
            save("Response received", trial, original, changelog, response)
    knxnet.disconnect()
