from sys import path, argv
path.append('../')

from bof import BOFNetworkError, knx

def all_frames() -> knx.KnxFrame:
    specs = knx.KnxSpec()
    for sid in specs.service_identifiers: 
        # If the frame has a cEMI block, we try all cEMI possibilities
        if "cemi" in [template["type"] for template in specs.bodies[sid]]: 
            for cemi_type in specs.cemis:
                yield knx.KnxFrame(type=sid, cemi=cemi_type)
        else:
            yield knx.KnxFrame(type=sid)

# RUN
if len(argv) < 2:
    print("Usage: python {0} IP_ADDRESS".format(argv[0]))
else:
    knxnet = knx.KnxNet()
    knxnet.connect(argv[1], 3671)
    for frame in all_frames():
        try:
            print("[SEND] {0}".format(frame))
            response = knxnet.send_receive(frame)
            print("[RECV] {0}".format(response))
        except BOFNetworkError:
            print("[NO RESPONSE]")
        finally
    knxnet.disconnect()
