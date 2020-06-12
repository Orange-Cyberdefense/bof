TODOs
=====

1. Bugs and things to check
---------------------------

- [ ] "Channel" could be stored directly in the KnxNet object, check if it can be done
- [ ] Review the doctring-generated documentation to update it (or make sure it is up-to-date)

2. Upper-level functions (abstraction of the specification)
-----------------------------------------------------------

- [ ] Discovery methods (search, discover)
- [ ] Implement `KnxDevice` class and submodule (`knxdevice.py`)
- [ ] Simple script for "read" and "write" actions on all KNX objects on range
- [ ] Service identifier frames implementations with content (ex: DESCRIPTION REQUEST, CONFIG REQUEST)
- [ ] Find a way to do more clever channel management (ex: `examples/cemi.py` has raw `communication channel id` definition)
- [ ] Add error code detection in `knxnet.json` or in a knx upper layer

3. Specification improvement
----------------------------

- [ ] Add a few default values for fields from the spec
- [ ] Add missing structures/bodies/cemis in `knxnet.json`
- [ ] Implement `repeat` keyword in spec (one or more fields repeated, as in `supp svc families`

4. Missing unit tests
---------------------

- [ ] Frames with cEMI blocks (inspired from `cemi.py`)
- [ ] Subfields in fields (bit list management), mostly located in cEMI blocks
- [ ] `bof.byte` IPv4/bytes conversion unit tests (`tests/test_byte.py`)

5. Future
---------

- [ ] `_TCP` and `TCP` classes in `bof/network.py` 

6. Done
-------

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
- [X] DOCS: Move Overview and TL;DR from **source code documentation** to **user manual**
- [X] The `init` parameter from `KnxNet.connect()` should be false by default
- [X] Rename and refactor KnxStructure factories
- [X] Write unittest for `KnxFrame.remove()` (use `examples/frame_building.py`)
- [X] Fill a known service with correct default values # DROP, we let the user do it, that's a framework
- [X] Handle `optional` key from `knxnet.json`
- [X] Implement cEMI management frames content (property id, etc.) and parsing (KNX 03_06_01 - 4.1.7.3)
- [X] cEMI's "number of elements" and "start index" should not be on a complete byte (NoE is 4bits, index is 12)
- [X] cEMI frame fuzzer demo
- [X] Fix JSON spec loading bug after too many requests
- [X] Optional field "data" is not filled in when receiving configuration request from the boiboite (should be 2 empty bytes)
- [X] Fix socket error after too many requests ("too many open files"), test with `examples/cemi_fuzzer.py`
