from part_placement_tool.part import Part

class Board (object):
    """
    Representation of a board
    """

    SPACING = 10.0 #1 cm between boards

    def __init__(self, row, column, width, height):
        """
        Initialize the board, given a row and column position (starting at 1) and a width and height in mm 
        """
        self._id = row*column
        self._row = row
        self._column = column
        self._width = width
        self._height = height

    def bottom_left_corner(self):
        """
        Returns the position of the bottom left corner of the board in mm.
        """
        return ( (self._column-1) * (self._width + self.SPACING), (self._row - 1) * (self._height + self.SPACING))

    def top_right_corner(self):
        """
        Returns the top left corner of the board in mm.
        """
        bl = self.bottom_left_corner()
        return (bl[0] + self._width, bl[1] + self._height)

    def locate_part (self, part):
        """
        Return the position of the part on the board in mm
        """
        if not isinstance(part, Part):
            raise RuntimeError("locate_part requires a part input.")

        bl = self.bottom_left_corner()
        pp = part.position
        return (bl[0] + pp[0], bl[1] + pp[1]) #matched kicad positions.
        
def generate_board_grid (row, column, width, height, num_boards):
    """
    This function returns a list of the boards in a grid.
    """
    if num_boards > row*column:
        raise RuntimeError ("Invalid board grid size,")
    if column == 0:
        raise RuntimeError ("Must have > 0 columns.")
    if row == 0:
        raise RuntimeError("Must have > 0 rows.")
    boards = [Board( int(num_boards/columns), int(num_boards % columns), width, height) for i in range(num_boards)]