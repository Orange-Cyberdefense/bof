Notice
======

This section is intended for contributors, either for improving existing parts
(core, existing implementation) or adding new protocol implementations.  Before
going further, please consider the following notice.

Code quality requirements
-------------------------

:Quality: 

   We like clean code and expect contributions to be PEP-8 compliant as much as
   possible (even though we don't test for it). New code should be readable easily
   and maintainable. And remember: if you need to use "and" while explaining what
   your function does, then you can probably split it.

:Genericity:

   Part of the code (the "core") is used by all protocol implementations.  When
   you add code to the core, please make sure that it does not cause issues in
   protocol-specific codes. Also, if you write or find out that code in
   implementations can be made generic and added to the core, feel free to do
   it.

:Unit tests:

   We use Python's ``unittest`` to write unit tests. When working on BOF, please
   write or update unit tests!  They are in ``tests/``. You can run all unit tests
   with: ``python -m unittest discover -s tests``.

Comments and documentation
--------------------------

:Docstrings:

  Modules, functions, classes, methods start with docstrings written in 
  ReStructuredText. Docstrings are extracted to build the ReadTheDocs source
  code documentation using Sphinx. We use a not-so-strict format, but you
  should at least make sure that docstrings are useful to the reader, contain
  the appropriate details and have a valid and consistent format. You can also
  rely on the following model::

    """Brief description of the module, function, class, method.

    A few details on how, where, when and why to use it.

    :param first: Description of param "first": type, usage, origin
		  Second line of description if one isn't enough.
    :param second: Description of param "second"
    :returns: The value that is returned, if any.
    :raises BOFProgrammingError: if misused

    Usage example::

      if there is any interest in adding such example, please do so.
    """

Git branching
-------------

We follow the "successful git branching model" described `here
<https://nvie.com/posts/a-successful-git-branching-model/>`_. In a nutshell:

* Branch from ``master`` for hotfixes
* Work on ``dev`` for small changes
* Create specific ``feature`` branches from ``dev`` for big changes
* Don't work on ``master``

Report issues
-------------

Report bugs, ask questions or request for missing documentation and new features
by submitting an issue on GitHub. For bugs, please describe your problem as
clearly as you can.

Architecture
============

> TODO

Extend BOF
==========

> TODO
