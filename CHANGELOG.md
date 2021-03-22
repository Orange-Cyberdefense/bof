Changelog 0.3.0 to 0.4.0
========================

Network
-------

* Bug fix in exception handing for `asyncio` transport objects
* New method `sr` as a shortcut for `send_receive` in protocol implementations
* Refactoring: `UDP()` and `TCP()` classes now inherit an internal `_Transport()` class

Tests
-----

* Unit tests for `base.py` and `network.py` have been updated.
