TODOs
=====

- [ ] `KnxNet.source` (`UDP.source` property) returns 127.0.0.1 as source IP, is it normal? 
- [ ] Find a way to fill a known service with correct default values
- [ ] Correctly handle length fields so that they are updated when a value is changed in a structure
- [ ] `bof.byte` IPv4/bytes conversion unit tests (`tests/test_byte.py`)
- [ ] Should `KNXSPEC` be moved to a singleton class with parsing methods and properties instead ??
- [ ] `_TCP` and `TCP` classes in `bof/network.py` 
- [ ] Replace `DIB` type and `dibtype`s with distinct DIB structures
- [ ] DOCS: Move Overview and TL;DR from **source code documentation** to **user manual**
- [X] `KnxStructure.factory()` could be refactored / improved
- [X] `type` in knxnet dictionary could be used to generate structure directly if in `KNXSPEC[STRUCTURES]`
- [X] Script to simulate boiboite (just reply valid DESCRIPTION_RESPONSE when sending valid DESCRIPTION_REQUEST :))
