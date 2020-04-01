TODOs
=====

- [ ] Add a few default values for fields from the spec
- [ ] Add missing structures/bodies in `knxnet.json`
- [ ] Implement `repeat` keyword in spec (one or more fields repeated, as in `supp svc families`
- [ ] `KnxNet.source` (`UDP.source` property) returns 127.0.0.1 as source IP, is it normal? 
- [ ] `bof.byte` IPv4/bytes conversion unit tests (`tests/test_byte.py`)
- [ ] `_TCP` and `TCP` classes in `bof/network.py` 
- [ ] Gather details about exchanges from Wireshark traces
- [ ] Write discovery script
- [ ] Write simple script for "write" actions on all KNX objects on range
- [ ] DOCS: Move Overview and TL;DR from **source code documentation** to **user manual**

- [X] Fill a known service with correct default values # DROP, we let the user do it, that's a framework
- [X] Handle `optional` key from `knxnet.json`
- [X] Rename dup field names so that they don't have the same names # DROP, we don't care (for now)
- [X] Test `CONNECT RESPONSE`, as it does not start with a length field and the code handling such case has not been tested
- [X] Move `KNXSPEC` to a singleton class with dictionary names == properties
- [X] Write unittest for fields resizing and structure length updates
- [X] Replace `DIB` type and `dibtype`s with distinct DIB structures
- [X] Correctly handle length fields so that they are updated when a value is changed in a structure
- [X] Handle total length update at frame level, don't care about manual structure builds
- [X] `KnxStructure.factory()` could be refactored / improved
- [X] `type` in knxnet dictionary could be used to generate structure directly if in `KNXSPEC[STRUCTURES]`
- [X] Script to simulate boiboite (just reply valid DESCRIPTION_RESPONSE when sending valid DESCRIPTION_REQUEST :))
- [X] Write methods to add and remove fields (properties) from a structure / frame
