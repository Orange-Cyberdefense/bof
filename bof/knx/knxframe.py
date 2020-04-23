"""
KNX frame handling
------------------

KNXnet/IP frames handling implementation, implementing ``bof.network``'s
``UDPStructure`` and ``UDPField`` classes.

A KNX frame (``KnxFrame``) is a byte array divided into a set of structures. A
frame always has the following format:

:Header: Single structure with basic data including the type of message.
:Content: One or more structures, depending on the type of message.

A structure (``KnxStructure``) is a byte array divided into a set of fields
(``KnxField``). A structure has the following data:

:Name: The name of the structure to be able to refer to it (using a property).
:Content: A set of fields and/or a set of sub-structures.

A field (``KnxField``) is a byte or a byte array with:

:Name: The name of the field to refer to it.
:Size: The number of bytes the field takes.
:Content: A byte or a byte array with the actual content.
"""

from os import path
from ipaddress import ip_address
from textwrap import indent

from ..base import BOFProgrammingError, load_json, to_property, log
from ..network import UDPField, UDPStructure
from .. import byte

###############################################################################
# KNX SPECIFICATION CONTENT                                                   #
###############################################################################

KNXSPECFILE = "knxnet.json"

class KnxSpec(object):
    """Singleton class for KnxSpec specification content usage.

    Specification file is a JSON file with the following format::

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

        for template in KnxSpec().category1:
            print(template.name)

    The default specification is ``knxnet.json`` however the end user is free
    to modify this file (add categories, contents and attributes) or create a
    new file following this format.
    """
    __instance = None
 
    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    def __init__(self, filepath:str=None):
        """If filepath is not specified, we load the default file."""
        if filepath:
            self.load(filepath)
        else:
            self.load(path.join(path.dirname(path.realpath(__file__)), "knxnet.json"))

    def load(self, filepath):
        """Loads the content of a JSON file and adds its categories as attributes
        to this class.

        If a file was loaded previously, the content will be added to previously
        added content, unless the ``clear()`` method is called first.

        :param filepath: Absolute path of a JSON file to load.
        :raises BOFLibraryError: If file cannot be used as JSON spec file.

        Usage::

            spec.load("knxpec_extention.json")
        """
        content = load_json(filepath)
        for key in content.keys():
            setattr(self, to_property(key), content[key])

    def clear(self):
        """Remove all content loaded in class KnxSpec previously, and associated
        attributes.

        Usage::

            KnxSpec
            spec.clear()
            spec.load("knxpec.json")
        """
        # Wee need to save the dict first as it changes in the loop
        attributes = list(self.__dict__.keys()).copy()
        for key in attributes:
            delattr(self, key)

###############################################################################
# KNX FRAME CONTENT                                                           #
###############################################################################

#-----------------------------------------------------------------------------#
# KNX fields (byte or byte array) representation                              #
#-----------------------------------------------------------------------------#

class KnxField(UDPField):
    """A ``KnxField`` is a set of raw bytes with a name, a size and a content
    (``value``).

    :param name: Name of the field, to be referred to using a property.
    :param size: Size of the field (number of bytes), from ``UDPField``.
    :param value: Value contained in the field (in bytes), from ``UDPFIield``.
    :param fixed_size: Set to ``True`` if the ``size`` should not be modified
                       automatically when changing the value (``UDPField``).
    :param fixed_value: Set to ``True`` if the ``value`` should not be
                        modified automatically inside the module (``UDPField``).
    :param is_length: This boolean states if the field is the length field of
                      the structure. If True, this value is updated when a field
                      in the structure changes (except if this field has arg
                      ``fixed_value`` set to True.

    Instantiate::

        KnxField(name="header length", size=1, default="06")

    **KNX Standard v2.1 03_08_02**
    """
    __name:str
    __is_length:bool

    def __init__(self, **kwargs):
        """Initialize the field according to a set of keyword arguments."""
        super().__init__(**kwargs)
        # Inherited from UDPField
        self._size = int(kwargs["size"]) if "size" in kwargs else self._size
        # KnxField initialization
        self.__name = kwargs["name"].lower() if "name" in kwargs else ""
        self.__is_length = kwargs["is_length"] if "is_length" in kwargs else False
        if "default" in kwargs:
            self._update_value(kwargs["default"])
        elif "value" in kwargs:
            self._update_value(kwargs["value"])
        else:
            self._update_value(bytes(self._size)) # Empty bytearray

    def __len__(self):
        return len(self._value)

    def __bytes__(self):
        return bytes(self._value)

    def __str__(self):
        return "<{0}: {1} ({2}B)>".format(self.__name, self.value, self.size)

    #-------------------------------------------------------------------------#
    # Properties                                                              #
    #-------------------------------------------------------------------------#

    @property
    def name(self) -> str:
        return self.__name
    @name.setter
    def name(self, name:str) -> None:
        if isinstance(name, str):
            self.__name = name.lower()
        else:
            raise BOFProgrammingError("Field name should be a string.")

    @property
    def value(self) -> bytes:
        return self._value
    @value.setter
    def value(self, content) -> None:
        """Set ``content`` to value according to 3 types of data: byte array,
        integer or string representation of an IPv4 address.
        
        Sets ``fixed_value`` to True to avoid rechanging the value automatically
        using length updated.

        Example::

            field.value = "192.168.1.1"
        """
        if isinstance(content, bytes):
            self._value = byte.resize(content, self.size)
        elif isinstance(content, str) and content.isdigit():
            self._value = bytes.fromhex(content)
            self._value = byte.resize(self._value, self.size)
        elif isinstance(content, str):
            # Check if IPv4:
            try:
                ip_address(content)
                self._value = byte.from_ipv4(content)
            except ValueError:
                self._value = content.encode('utf-8')
        elif isinstance(content, int):
            self._value = byte.from_int(content, size=self.size)
        else:
            raise BOFProgrammingError("Field value should be bytes, str or int.")
        self.fixed_value = True

    @property
    def is_length(self) -> bool:
        return self.__is_length
    @is_length.setter
    def is_length(self, value:bool) -> None:
        self.__is_length = value

    #-------------------------------------------------------------------------#
    # Internal (should not be used by end users)                              #
    #-------------------------------------------------------------------------#

    def _update_value(self, content) -> None:
        """Change the value according to automated updated from within the code
        si that nothing is changed in ``fixed_value`` is set to True.

        :param content: A byte array, an integer, or an IPv4 string.
        """
        if self.fixed_value:
            log("Tried to modified field {0} but value is fixed.".format(self.__name))
            return
        self.value = content
        self.fixed_value = False # Property changes this value, we switch back

#-----------------------------------------------------------------------------#
# KNX structures (set of fields) representation                               #
#-----------------------------------------------------------------------------#

class KnxStructure(UDPStructure):
    """A ``KnxStructure`` contains an ordered set of other structures and/or
    an ordered set of fields (``KnxField``) of one or more bytes.

    A structure has the following properties:

    - According to **KNX Standard v2.1 03_08_02**, the first byte of the
      structure should contain the length of the structure.
    - A non-terminal ``KnxStructure`` contains a set of other ``KnxStructure``.
    - A terminal ``KnxStructure`` contains a set of ``KnxField``.
    - A ``KnxStructure`` can also contain a mix of structures and fields.

    :param name: Name of structure, so that it can be accessed by its name
                 using a property.
    :param structure: List of structures, fields or both.

    Instantiate::

        descr_resp = KnxStructure(name="description response")
        descr_resp.append(KnxStructure.build_from_type("DIB_DEVICE_INFO"))
        descr_resp.append(KnxStructure.build_from_type("DIB_SUPP_SVC_FAMILIES"))
    """
    __name:str
    __structure:list

    def __init__(self, **kwargs):
        """Initialize the ``KnxStructure`` with a mandatory name and optional
        arguments to fill in the structure list (with fields or substructures).

        KnxStructure can be pre-filled according to a type or to a cemi
        structure as defined in the specification file.

        Available keyword arguments:

        :param name: String to refer to the structure using a property.
        :param type: Type of structure. Cannot be used with ``cemi``.
        :param cemi: Type of structure if this is a cemi structure. Cannot be used
                     with ``type``.

        Some other keywords arguments depend on the type given (``size``,
        ``dibtype``, ``default``, etc.).

        """
        self.name = kwargs["name"] if "name" in kwargs else ""
        self.__structure = []
        specs = KnxSpec()
        if "type" in kwargs:
            if not kwargs["type"].upper() in specs.structures.keys():
                raise BOFProgrammingError("Unknown structure type ({0})".format(kwargs["type"]))
            self.name = self.name if len(self.name) else kwargs["type"]
            self.append(self.factory(structure=specs.structures[kwargs["type"].upper()]))
        elif "cemi" in kwargs:
            if not kwargs["cemi"] in specs.cemis.keys():
                raise BOFProgrammingError("cEMI is unknown ({0})".format(kwargs["cemi"]))
            self.name = self.name if len(self.name) else "cemi"
            self.append(self.factory(structure=specs.structures[specs.cemis[kwargs["cemi"]]["type"]]))
            self.message_code.value = bytes.fromhex(specs.cemis[kwargs["cemi"]]["id"])

    def __bytes__(self):
        raw = b''
        for item in self.__structure:
            raw += bytes(item)
        return raw

    def __len__(self):
        """Return the size of the structure in total number of bytes."""
        return len(bytes(self))

    def __str__(self):
        ret = ["{0}: {1}".format(self.__class__.__name__, self.__name)]
        for item in self.__structure:
            ret += [indent(str(item), "    ")]
        return "\n".join(ret)
        
    #-------------------------------------------------------------------------#
    # Public                                                                  #
    #-------------------------------------------------------------------------#

    @classmethod
    def factory(cls, **kwargs) -> object:
        if "structure" in kwargs:
            cemi = kwargs["cemi"] if "cemi" in kwargs else None
            optional = kwargs["optional"] if "optional" in kwargs else False
            return cls.create_from_structure(kwargs["structure"], cemi, optional)
        if "type" in kwargs:
            return cls(type=kwargs["type"], name=name)
        if "cemi" in kwargs:
            optional = kwargs["optional"] if "optional" in kwargs else False
            return cls(cemi=kwargs["cemi"], name="cEMI")
        return None

    @classmethod
    def create_from_structure(cls, structure, cemi:str=None, optional:bool=False) -> list:
        """Creates a list of ``KnxStructure``-inherited object according to the
        list of templates specified in parameter ``structure``.

        :param structure: template dictionary or list of template dictionaries
                          for ``KnxStructure`` object instantiation.
        :param cemi: when a structure is a cEMI, we need to know what type of
                     cEMI it is to build it accordingly.
        :param optional: build optional templates (default: no/False)
        :returns: A list of ``KnxStructure`` object (one by item in ``structure``).
        :raises BOFProgrammingError: If the value of argument "type" in a
                                     structure dictionary is unknown.

        Example::

            structure = KnxStructure(name="structure")
            structure.append(KnxStructure.factory(structure=KnxSpec().structures["structure"]))
        """
        structlist = []
        specs = KnxSpec()
        if isinstance(structure, list):
            for item in structure:
                structlist += cls.create_from_structure(item, cemi, optional)
        elif isinstance(structure, dict):
            if "optional" in structure.keys() and structure["optional"] == True and not optional:
                return structlist
            if not "type" in structure or structure["type"] == "structure":
                structlist.append(cls(**structure))
            elif structure["type"] == "field":
                structlist.append(KnxField(**structure))
            elif structure["type"] == "cemi":
                structlist.append(cls(cemi=cemi))
            elif structure["type"] in specs.structures.keys():
                substructure = cls(name=structure["name"])
                content = specs.structures[structure["type"]]
                substructure.append(cls.create_from_structure(content, cemi, optional))
                structlist.append(substructure)
            else:
                raise BOFProgrammingError("Unknown structure type ({0})".format(structure))
        return structlist

    def fill(self, frame:bytes) -> bytes:
        """Fills in the fields in object with the content of the frame.

        The frame is read byte by byte and used to fill the field in ``fields()``
        order according to each field's size. Hopefully, the frame is the same
        size as what is expected for the format of this structure.
        
        :param frame: A raw byte array corresponding to part of a KNX frame.
        :returns: The remainder of the frame (if any) or 0
        """
        cursor = 0
        for field in self.fields:
            field.value = frame[cursor:cursor+field.size]
            cursor += field.size

    def append(self, structure) -> None:
        """Appends a structure, a field of a list of structures and/fields to
        current structure's content. Adds the name of the structure to the list
        of current's structure properties. Ex: if ``structure.name`` is ``foo``,
        it could be referred to as ``self.foo``.

        :param structure: ``KnxStructure``, ``KnxField`` or a list of such objects.

        Example::

            structure = KnxStructure(name="atoll")
            structure.append(KnxField(name="pom"))
            structure.append(KnxStructure(name="galli"))
        """
        if isinstance(structure, KnxField) or isinstance(structure, KnxStructure):
            self.__structure.append(structure)
            # Add the name of the structure as a property to this instance
            if len(structure.name) > 0:
                setattr(self, to_property(structure.name), structure)
        elif isinstance(structure, list):
            for item in structure:
                self.append(item)
        self.update()

    def update(self):
        """Update all fields corresponding to structure lengths. Ex: if a
        structure has been modified, the update will change the value of
        the structure length field to match (unless this field's ``fixed_value``
        boolean is set to True.

        Example::

            header.service_identifier.value = b"\x01\x02\x03"
            header.update()
            print(header.header_length.value)
        """
        for item in self.__structure:
            if isinstance(item, KnxStructure):
                item.update()
            elif isinstance(item, KnxField):
                if item.is_length:
                    item._update_value(len(self))

    def remove(self, name:str) -> None:
        """Remove the field ``name`` from the structure (or substructure).
        If several fields have the same name, only the first one is removed.
        
        :param name: Name of the field to remove.
        :raises BOFProgrammingError: if there is no corresponding field.

        Example::

            body = knx.KnxStructure()
            body.append(knx.KnxField(name="abitbol", size=30, value="monde de merde"))
            body.append(knx.KnxField(name="francky", size=30, value="cest oit"))
            body.remove("abitbol")
            print([x.name for x in body.fields])
        """
        name = name.lower()
        for item in self.__structure:
            if isinstance(item, KnxStructure):
                delattr(self, to_property(name))
                item.remove(name)
            elif isinstance(item, KnxField):
                if item.name == name or to_property(item.name) == name:
                    self.__structure.remove(item)
                    delattr(self, to_property(name))
                    del(item)
                    break

    #-------------------------------------------------------------------------#
    # Properties                                                              #
    #-------------------------------------------------------------------------#

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, name:str):
        if isinstance(name, str):
            self.__name = name.lower()
        else:
            raise BOFProgrammingError("Structure name should be a string.")

    @property
    def fields(self) -> list:
        self.update()
        fieldlist = []
        for item in self.__structure:
            if isinstance(item, KnxStructure):
                fieldlist += item.fields
            elif isinstance(item, KnxField):
                fieldlist.append(item)
        return fieldlist

    @property
    def attributes(self) -> list:
        """Gives the list of attributes added to the structure (field names)."""
        self.update()
        return [x for x in self.__dict__.keys() if not x.startswith("_KnxStructure__")]

    @property
    def structure(self) -> list:
        return self.__structure

    #-------------------------------------------------------------------------#
    # Internal (should not be used by end users)                              #
    #-------------------------------------------------------------------------#

    def _add_property(self, name:str, pointer:object) -> None:
        """Add a property to the object using ``setattr``, should not be used
        outside module.

        :param name: Property name
        :param pointer: The object the property refers to.
        """
        setattr(self, to_property(name), pointer)

#-----------------------------------------------------------------------------#
# KNX frames / datagram representation                                        #
#-----------------------------------------------------------------------------#

class KnxFrame(object):
    """Object representation of a KNX message (frame) with methods to build
    and read KNX datagrams.

    A frame contains a set of byte arrays (structures) so that:

    - It always starts with a header with a defined format.
    - The frame body contains one or more structures and varies according to
      the type of KNX message (defined in header).

    :param source: Source address of the frame with format tuple 
                   ``(ip:str, port:int)``.
    :param raw: Raw byte array used to build a KnxFrame object.
    :param header: Frame header as a ``KnxStructure`` object.
    :param body: Frame body as a ``KnxStructure`` which can also contain a set
                 of other ``KnxStructure`` objects.

    Instantiate::

        KnxFrame(sid="DESCRIPTION REQUEST")
        KnxFrame(frame=data, source=address)

    **KNX Standard v2.1 03_08_02**
    """
    __source:tuple
    __header:KnxStructure
    __body:KnxStructure
    __specs:KnxSpec

    def __init__(self, **kwargs):
        """Initialize a KnxFrame object from various origins using values from
        keyword argument (kwargs).

        Available frame initialization methods:
        
        :Empty frame: Using no argument, a user can then define the content of
                      the frame manually (or keep an empty frame).
        :Byte array: Build the object from a raw byte array (e.g. received from
                     a KNX object).
        :Template: Build the object from a template of existing KNX message,
                   using a service identifier (sid). Templates can be found,
                   modified, removed or added in the KNX spec JSON file.

        Keywords arguments:

        :param sid: Service identifier as a string or bytearray (2 bytes),
                    sid is used to build a frame according to the structure
                    template associated to this service identifier.
        :param optional: Boolean, set to True if we want to create a frame with
                         optional fields (from spec).
        :param frame: Raw bytearray used to build a KnxFrame object.
        :param source: Source address of a frame, as a tuple (ip;str, port:int)
                       Only used is param `frame` is set.
        """
        # Empty frame (no parameter)
        self.__source = ("",0)
        self.__header = KnxStructure(type="header")
        self.__body = KnxStructure(name="body")
        self.__specs = KnxSpec()
        # Fill in the frame according to parameters
        if "source" in kwargs:
            self.__source = kwargs["source"]
        if "sid" in kwargs:
            cemi = kwargs["cemi"] if "cemi" in kwargs else None
            optional = kwargs["optional"] if "optional" in kwargs else False
            self.build_from_sid(kwargs["sid"], cemi, optional)
            log("Created new frame from service identifier {0}".format(kwargs["sid"]))
        elif "frame" in kwargs:
            self.build_from_frame(kwargs["frame"])
            log("Created new frame from byte array {0} (source: {1})".format(kwargs["frame"],
                                                                             kwargs["source"]))
        # Update total frame length in header
        self.update()

    def __bytes__(self):
        """Overload so that bytes(frame) returns the raw KnxFrame bytearray."""
        self.update()
        return self.raw

    def __len__(self):
        """Return the size of the structure in total number of bytes."""
        self.update()
        return len(self.raw)

    def __str__(self):
        ret = ["{0} object: {1}".format(self.__class__.__name__, repr(self))]
        ret += ["[HEADER]"]
        for attr in self.header.structure:
            ret += [indent(str(attr), "    ")]
        ret += ["[BODY]"]
        for attr in self.body.structure:
            ret += [indent(str(attr), "    ")]
        return "\n".join(ret)

    #-------------------------------------------------------------------------#
    # Public                                                                  #
    #-------------------------------------------------------------------------#

    def build_from_sid(self, sid, cemi:str=None, optional:bool=False) -> None:
        """Fill in the KnxFrame object according to a predefined frame format
        corresponding to a service identifier. The frame format (structures
        and field) can be found or added in the KNX specification JSON file.

        :param sid: Service identifier as a string (service name) or as a
                    byte array (normally on 2 bytes but, whatever).
        :param cemi: Type of cEMI if the structure associated to ``sid`` has
                     a cEMI field/structure.
        :param optional: Boolean, set to True if we want to build the optional
                         structures/fields as stated in the specs.
        :raises BOFProgrammingError: If the service identifier cannot be found
                                     in given JSON file.

        Example::

            frame = KnxFrame()
            frame.build_from_sid("DESCRIPTION REQUEST")
        """
        # If sid is bytes, replace the id (as bytes) by the service name
        if isinstance(sid, bytes):
            for service in self.__specs.service_identifiers:
                if bytes.fromhex(self.__specs.service_identifiers[service]["id"]) == sid:
                    sid = service
                    break
        # Now check that the service id exists and has an associated body
        if isinstance(sid, str):
            if sid not in self.__specs.bodies:
                # Try with underscores (Ex: DESCRIPTION_REQUEST)
                if sid in [to_property(x) for x in self.__specs.bodies]:
                    for body in self.__specs.bodies:
                        if sid == to_property(body):
                            sid = body
                            break
                else:
                    raise BOFProgrammingError("Service {0} does not exist.".format(sid))
        else:
            raise BOFProgrammingError("Service id should be a string or a bytearray.")
        self.__body.append(KnxStructure.factory(structure=self.__specs.bodies[sid],
                                                cemi=cemi,
                                                optional=optional))
        # Add substructure fields names as properties to body :)
        for field in self.__body.fields:
            self.__body._add_property(field.name, field)
            if sid in self.__specs.service_identifiers.keys():
                value = self.__specs.service_identifiers[sid]["id"]
                self.__header.service_identifier._update_value(value)
        self.update()

    def build_from_frame(self, frame:bytes) -> None:
        """Fill in the KnxFrame object using a frame as a raw byte array. This
        method is used when receiving and parsing a file from a KNX object.

        The parsing relies on the structure lengths stated in first byte of
        each part (structure) of the frame.

        :param frame: KNX frame as a byte array (or anything, whatever)

        Example::

            data, address = knx_connection.receive()
            frame = KnxFrame(frame=data, source=address)
        """
        # HEADER
        self.__header = KnxStructure(type="HEADER", name="header")
        self.__header.fill(frame[:frame[0]])
        for service in self.__specs.service_identifiers:
            attributes = self.__specs.service_identifiers[service]
            if bytes(self.__header.service_identifier) == bytes.fromhex(attributes["id"]):
                structurelist = self.__specs.bodies[service]
                break
        # BODY
        cursor = frame[0] # We start at index len(header) (== 6)
        for structure in structurelist:
            if cursor >= len(frame):
                break
            # factory returns a list but we only expect one item
            structure_object = KnxStructure.factory(structure=structure)[0]
            if isinstance(structure_object, KnxField):
                structure_object.value = frame[cursor:cursor+structure_object.size]
                cursor += structure_object.size
            else:
                structure_object.fill(frame[cursor:cursor+frame[cursor]])
                cursor += frame[cursor]
            self.__body.append(structure_object)

    def remove(self, name:str) -> None:
        """Remove the structure ``name`` from the header or body, as long as
        name is in the frame's attributes.

        If several fields have the same name, only the first one is removed.
        
        :param name: Name of the field to remove.
        :raises BOFProgrammingError: if there is no corresponding field.

        Example::

            frame.remove("control_endpoint")
            print([x for x in frame.attributes])
        """
        name = name.lower()
        for structure in [self.__header, self.__body]:
            for item in structure.attributes:
                if item == to_property(name):
                    item = getattr(structure, item)
                    if isinstance(item, KnxStructure):
                        for field in item.fields:
                            item.remove(to_property(field.name))
                            delattr(structure, to_property(field.name))
                        delattr(structure, to_property(name))
                        del item

    def update(self):
        """Update all fields corresponding to structure lengths. Ex: if a
        structure has been modified, the update will change the value of
        the structure length field to match (unless this field's ``fixed_value``
        boolean is set to True.

        For frames, the ``update()`` methods also update the ``total length``
        field in header, which requires an additional operation.
        """
        self.__body.update()
        self.__header.update()
        if "total_length" in self.__header.attributes:
            self.__header.total_length._update_value(byte.from_int(len(self.__header) + len(self.__body)))

    #-------------------------------------------------------------------------#
    # Properties                                                              #
    #-------------------------------------------------------------------------#

    @property
    def header(self):
        """Builds the raw byte set and returns it."""
        self.update()
        return self.__header

    @property
    def body(self):
        """Builds the raw byte set and returns it."""
        self.update()
        return self.__body

    @property
    def raw(self):
        """Builds the raw byte set and returns it."""
        self.update()
        return bytes(self.__header) + bytes(self.__body)

    @property
    def fields(self) -> list:
        """Build an array with all the fields in header + body."""
        self.update()
        return self.__header.fields + self.__body.fields

    @property
    def attributes(self) -> list:
        """Builds an array with the names of all attributes in header + body."""
        self.update()
        return self.__header.attributes + self.__body.attributes
