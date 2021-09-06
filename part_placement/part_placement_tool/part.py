

class Part (object):
    """
    Representation of a single part.
    """

    def __init__(self):

        #X, Y position in mm
        self._position = ( 0.0, 0.0 )
        self._value = ""
        self._name = ""

    @property
    def position(self):
        return self._position

    @property
    def value(self):
        return self._value 
        
    @property
    def name (self):
        return self._name

