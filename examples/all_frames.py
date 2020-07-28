from sys import path, argv
path.append('../')

from bof import BOFNetworkError, knx

def all_frames() -> knx.KnxFrame:
    spec = knx.KnxSpec()
    for sid, block in spec.codes["service identifier"].items(): 
        # If the frame has a cEMI block, we try all cEMI possibilities
        if "CEMI" in [template["type"] for template in spec.blocks[block] \
                      if "type" in template]:
            for cid, cemi in spec.codes["message code"].items():
                print(block, cemi)
                yield knx.KnxFrame(type=block, cemi=cemi)
        else:
            yield knx.KnxFrame(type=block)

# RUN
if len(argv) < 2:
    print("Usage: python {0} IP_ADDRESS".format(argv[0]))
else:
    knxnet = knx.KnxNet()
    knxnet.connect(argv[1], 3671)
    for frame in all_frames():
        print(frame.sid)
        try:
            print("[SEND] {0}".format(frame))
            response = knxnet.send_receive(frame)
            print("[RECV] {0}".format(response))
        except BOFNetworkError:
            print("[NO RESPONSE]")
    knxnet.disconnect()
