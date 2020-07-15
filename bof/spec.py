"""BOF should not contain code that is bound to a specific version of a
protocol's specifications. Therefore, message structures, error codes,
block contents, field names, etc. should be written to an external JSON
file and called within the code. Data from the specification should then
be stored within a protocol's implementation in a ``BOFSpec`` object or
in a class inherited from ``BOFSpec``.

A specification file is a JSON file with the following format::

    {
        "category1": [
            {"name": "1-1", "attr1": "attr1-1", "attr2": "attr1-1"},
            {"name": "1-2", "attr1": "attr1-2", "attr2": "attr1-2"}
        ],
        "category2": [
            {"name": "2-1", "type": "type1", "attr1": "attr2-1", "attr2": "attr2-1"},
            {"name": "2-2", "type": "type2", "attr1": "attr2-2", "attr2": "attr2-2"}
        ],
    }

``categories`` can be accessed from this object using attributes. Ex::

    for template in BOFSpec().category1:
        print(template.name)
"""

import json

from .base import BOFLibraryError, to_property

#-----------------------------------------------------------------------------#
# JSON file management functions                                              #
#-----------------------------------------------------------------------------#

def load_json(filename:str) -> dict:
    """Loads a JSON file and returns the associated dictionary.

    :raises BOFLibraryError: if the file cannot be opened.
    """
    try:
        with open(filename, 'r') as jsonfile:
            return json.load(jsonfile)
    except Exception as e:
        raise BOFLibraryError("JSON File {0} cannot be used.".format(filename)) #from None

#-----------------------------------------------------------------------------#
# BOF Specification object                                                    #
#-----------------------------------------------------------------------------#

class BOFSpec(object):
    """Singleton containing the data related to a protocol's specification,
    retrieved as a JSON file. The object should be instantiated whenever 
    protocol-specific data is required in an implementation, in order not to
    bound the code to the specification too tightly.
    """
    __instance = None
    __is_init = False
 
    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    def __init__(self, filepath:str=None):
        """Iniatialize the specification object with a JSON file.
        If file is not specified, we create an empty instance which can be
        filled later with the method ``load``.

        :param filepath: Absolute path to the JSON file.
        """
        if not self.__is_init:
            if filepath:
                self.load(filepath)
            self.__is_init = True

    def load(self, filepath):
        """Loads the content of a JSON file and adds its categories as attributes
        to this class.
        
        If a file was loaded previously, the content will be added to previously
        added content, unless the ``clear()`` method is called first.

        :param filepath: Absolute path of a JSON file to load.
        :raises BOFLibraryError: If file cannot be used as JSON spec file.

        Usage::

            spec.load("knxnet.json")
        """
        content = load_json(filepath)
        for key in content.keys():
            setattr(self, to_property(key), content[key])

    def clear(self):
        """Remove all content loaded in class previously, and associated
        attributes.

        Usage::

            spec.clear()
            spec.load("knxnet.json")
        """
        # We need to save the dict first as it changes in the loop
        attributes = list(self.__dict__.keys()).copy()
        for key in attributes:
            delattr(self, key)
