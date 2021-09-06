from part_placement_tool.board import Board, generate_board_grid
from part_placement_tool.part import Part
from part_placement_tool.serial_interface import SerialInterface
import asyncio
import curses
import curses.textpad
 
import argparse

parts = []
parts_map = {}
boards = []

class PartPickerInterface:

    SUPPORTED_CMDS = [
        "Home",
        "Zero",
        "Move",
        "Pen Up",
        "Pen Down",
        "Show Board Corner",
        "Start Part Place"
    ]

    _status = {
        "Homed": [False, False],
        "POS File": "",
        "Position": (None, None),
        "Part Name": "",
        "Part Value": "",
        "Current Board": 0,
    }

    def __init__(self, from_serial_queue, to_serial_queue):
        """
        Initialize the interface with some default values and set up the communication queues.
        """
        self.speed = 5000
        self._is_part_running = False
        self._current_part = 0
        self._is_board_running = False
        self._current_board = 0
        self._screen = curses.initscr()
        self._from_serial_q = from_serial_queue
        self._to_serial_q = to_serial_queue
        self._height, self._width = self._screen.getmaxyx()
        self._data_window = curses.newwin(self._height-2, int(self._width/3)-3, 1, int(self._width*2/3))
        self._cmd_window = curses.newwin(self._height-2, int(self._width/3)-3, 1, 1)
        self._status_window = curses.newwin(self._height-2, int(self._width/3)-3, 1, int(self._width/3))
        curses.noecho()
        curses.cbreak()
        self._screen.nodelay(True)
        # Start colors in curses
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
        self._screen.keypad(True)
        self._update = True
        self._current_selection = 0
        self._current_part = 1
        self._showing_tr = False
        self._current_board = 1

        self._message_data = []

        self.add_log_message ("Program Started.")
        self._refresh()

    def _draw_screen(self):
        self._screen.clear()
        self._screen.border(0)
        self._screen.addstr(self._height-1, 0, "Part Placer, press q to exit.", curses.color_pair(3))
        self._screen.refresh()

        self._data_window.clear()
        self._data_window.border(0)
        self._draw_data_window()
        self._data_window.refresh()
        
        self._cmd_window.clear()
        self._cmd_window.border(0)
        self._draw_cmd_window()
        self._cmd_window.refresh()

        self._status_window.clear()
        self._status_window.border(0)
        self._draw_status_window()
        self._status_window.refresh()
        self._show_part()
        self._show_board()

    def _draw_data_window(self):
        self._data_window.addstr(0, 0, "MESSAGES", curses.A_BOLD)
        for (i, line) in enumerate(self._message_data):
            self._data_window.addstr(i+1, 1, line)

    def _draw_cmd_window(self):
        self._cmd_window.addstr(0, 0, "CHOOSE A COMMAND:", curses.A_BOLD)
        for (i, cmd) in enumerate (self.SUPPORTED_CMDS):
            if i == self._current_selection:
                self._cmd_window.addstr(i+1, 1, cmd, curses.A_STANDOUT)
            else:
                self._cmd_window.addstr(i+1, 1, cmd)

    def _draw_status_window(self):
        buffer = []
        self._status_window.addstr(0, 0, "STATUS", curses.A_BOLD)
        for key, item in self._status.items():
            line = f"{key}: {item}"
            while (len(line) > 0):
                buffer.append(line[0:min(len(line), self._status_window.getmaxyx()[1]-2)])
                line = line[min(len(line), (self._status_window.getmaxyx()[1]-2)): ]

        for (i, line) in enumerate(buffer):
            self._status_window.addstr(i+1, 1, line)

    def _refresh(self):
        """
        Refresh the screen.
        """
        self._draw_screen()
    
    def add_log_message(self, message):
        while (len(message) > 0):
            self._message_data.append(message[0:min(len(message), self._data_window.getmaxyx()[1]-2)])
            message = message[min(len(message), (self._data_window.getmaxyx()[1]-2)): ]
        self._message_data = self._message_data[max(0, len(self._message_data) + 2 - self._data_window.getmaxyx()[0]):]

    async def get_key(self):
        while (self.k != 'q'):
            try:
                self.k = self._screen.getkey()
                if self.k == 'q':
                    break 
            except:
                pass
            await asyncio.sleep(0.1)

    def _show_part(self):
        global parts, boards, parts_map
        current_part = parts[self._current_part-1]
        current_board = boards[self._current_board-1]
        if self._is_part_running:
            self._status["Part Name"] = current_part.name
            self._status["Part Value"] = current_part.value
            self._status["Current Board"] = self._current_board
            self._status["Position"] = current_board.locate_part(current_part)
        else:
            self._status["Part Name"] = current_part.name
            self._status["Part Value"] = current_part.value    

    def _show_board(self):
        global boards
        current_board = boards[self._current_board-1]
        self._status["Current Board"] = self._current_board


    async def run(self):
        """
        Main loop for checking and refreshing the display.
        """
        global parts, boards, parts_map
        self.k = 0
        self._refresh()
        while (self.k != 'q'):
            await asyncio.sleep(0.1)
            if (self.k != 0 or not self._from_serial_q.empty()):

                if self.k == 'q':
                    break

                while not self._from_serial_q.empty():
                    data = await self._from_serial_q.get()
                    #process the packet and update the state.
                    self.add_log_message(data)
                    self._from_serial_q.task_done()

                self._height, self._width = self._screen.getmaxyx()
                self._refresh()

                if self.k == "KEY_DOWN":
                    self._current_selection = min (self._current_selection + 1, len(self.SUPPORTED_CMDS)-1)
                    self._update = True
                elif self.k == "KEY_UP":
                    self._current_selection = max (0, self._current_selection - 1)
                    self._update = True
                elif self.k == "KEY_RIGHT":
                    data = None
                    if self._is_part_running:
                        self._current_part += 1
                        if self._current_part <= len(parts):
                            current_part = parts[self._current_part-1]
                            current_board = boards[self._current_board-1]
                            (x, y) = current_board.locate_part(current_part)
                            data = f"G1 X{x} Y{y} F{self.speed}\n"
                            self._status["Position"] = (x, y)
                        else:
                            self._current_part = 1
                            self._is_part_running = False

                    if self._is_board_running:
                        if self._showing_tr:
                            self._current_board += 1
                        self._showing_tr = not self._showing_tr
                        if self._current_board <= len(boards):
                            current_board = boards[self._current_board-1]
                            if self._showing_tr:
                                (x, y) = current_board.top_right_corner()
                            else:
                                (x, y) = current_board.bottom_left_corner()
                            data = f"G1 X{x} Y{y} F{self.speed}\n"
                            self._status["Position"] = (x, y)
                        else:
                            self._current_board = 1
                            self._showing_tr = False
                            self._is_board_running = False
                    self._update = True
                    if data != None:
                        await self._to_serial_q.put(bytes(data.encode("utf-8")))
                elif self.k == "KEY_LEFT":
                    data = None
                    if self._is_part_running:
                        self._current_part -= 1
                        if self._current_part >= 1:
                            current_part = parts[self._current_part-1]
                            current_board = boards[self._current_board-1]
                            (x, y) = current_board.locate_part(current_part)
                            data = f"G1 X{x} Y{y} F{self.speed}\n"
                            self._status["Position"] = (x, y)
                        else:
                            self._current_part = 1
                            self._is_part_running = False
                    if self._is_board_running:
                        if not self._showing_tr:
                            self._current_board -= 1
                        self._showing_tr = not self._showing_tr
                        if self._current_board >= 1:
                            current_board = boards[self._current_board-1]
                            if self._showing_tr:
                                (x, y) = current_board.top_right_corner()
                            else:
                                (x, y) = current_board.bottom_left_corner()
                            data = f"G1 X{x} Y{y} F{self.speed}\n"
                            self._status["Position"] = (x, y)
                        else:
                            self._current_board = 1
                            self._is_board_running = False
                    self._update = True
                    if data != None:
                        await self._to_serial_q.put(bytes(data.encode("utf-8")))
                elif self.k == "\n":
                    #Send a command.
                    cmd_name = self.SUPPORTED_CMDS[self._current_selection]
                    data = None
                    if cmd_name == "Home":
                        self._status["Homed"][0] = True
                        data = "$H\n"
                    elif cmd_name == "Zero":
                        self._status["Homed"][1] = True
                        self._status["Position"] = (0, 0)
                        data = "G92 X0 Y0\n"
                    elif cmd_name == "Move":
                        x, y = self._get_xy()
                        self._status["Position"] = (x, y)
                        data = f"G1 X{x} Y{y} F{self.speed}\n"
                        self.add_log_message(data)
                    elif cmd_name == "Pen Up":
                        data = "M3 S90\n"
                    elif cmd_name == "Pen Down":
                        data = "M5\n"
                    elif cmd_name == "Show Board Corner":
                        self._is_board_running = True
                        self._showing_tr = False
                        self._current_board = 1
                        current_board = boards[self._current_board-1]
                        (x, y) = current_board.bottom_left_corner()
                        self._status["Position"] = (x, y)
                        data = f"G1 X{x} Y{y} F{self.speed}\n"
                    elif cmd_name == "Start Part Place":
                        self._is_part_running = True
                        self._current_board = 1
                        self._current_part = 1
                        current_part = parts[self._current_part-1]
                        current_board = boards[self._current_board-1]
                        (x, y) = current_board.locate_part(current_part)
                        data = f"G1 X{x} Y{y} F{self.speed}\n"
                        self._status["Position"] = (x, y)
                    else:
                        #Shouldn't get here.
                        data = None


                    if data != None:
                        await self._to_serial_q.put(bytes(data.encode("utf-8")))
                self.k = 0
                self._refresh()
        
        #send the quit signal.
        await self._to_serial_q.put("q")
        curses.endwin()

    def _get_xy(self):
        self._screen.clear()
        self._pause_input = True

        self._screen.addstr(0, 0, "Enter X (0->225):")

        editwin = curses.newwin(1,10, 2,1)
        curses.textpad.rectangle(self._screen, 1,0, 1+1+1, 1+10+1)
        self._screen.refresh()

        box = curses.textpad.Textbox(editwin)

        # Let the user edit until Ctrl-G is struck.
        box.edit()

        # Get resulting contents
        x = box.gather()
        x = int(x.strip())
        x = min(x, 225)
        x = max(x, 0) 

        self._screen.clear()
        self._screen.addstr(0, 0, "Enter Y (0->250):")

        editwin = curses.newwin(1,10, 2,1)
        curses.textpad.rectangle(self._screen, 1,0, 1+1+1, 1+10+1)
        self._screen.refresh()
        
        box = curses.textpad.Textbox(editwin)

        # Let the user edit until Ctrl-G is struck.
        box.edit()

        # Get resulting contents
        y = box.gather()
        y = int(y.strip())
        y = min(y, 250)
        y = max(y, 0) 

        curses.noecho()
        self._pause_input = False

        return (x, y)

    def _process_packet(self, data):
        try:
            self.add_log_message(f"Recieved data: {bytearray(data).hex()}")
        except:
            self.add_log_message("ERROR: unhandled packet.")
            return

        self.add_log_message(f"Recieved Packet: {str(packet)}")  

def load_pos_file (filename, offsets):
    """
    Load the filename and adjust the positions from the Kicad bottom left corner, x positive right, y positive up.
    """
    with open(filename) as fid:
        _ = fid.readline() #Skip the first line.
        for line in fid.readlines():
            elements = line.split(",")
            a_part = Part()
            a_part._position = ((float(elements[3]) - offsets[0]), float(elements[4]) - offsets[1] )
            a_part._name = elements[0].strip('"')
            a_part._value = elements[1].strip('"')
            parts.append(a_part)
    return parts



async def main_async():
    global parts, boards
    parser = argparse.ArgumentParser(description="This tool is used to highlight part positions.")

    parser.add_argument("position_file", type=str, help="part position file.")
    parser.add_argument("serial_port", type=str, help="COM port for the plotter.")
    parser.add_argument("--bx", default=1, type=int, help="Number of boards in the x direction.")
    parser.add_argument("--by", default=1, type=int, help="Number of boards in the y direction.")
    parser.add_argument("--width", default = 52.1, type=float, help="Width of board in mm")
    parser.add_argument("--height", default=49.6, type=float, help = "Height of board in mm.")
    parser.add_argument("--xoff", default = 115.6, type=float, help="0 of the board GRBL's in x")
    parser.add_argument("--yoff", default= -128.9, type=float, help = "0 of the board GRBL's in y")

    args = parser.parse_args()

    parts = load_pos_file(args.position_file, (args.xoff, args.yoff))
    parts.sort(key= lambda x: x.value)

    boards = []
    for i in range(1, args.bx * args.by+1):
        boards.append(Board(int(i / args.bx), int (i % args.bx)+1, args.width, args.height))

    from_queue = asyncio.Queue()
    to_queue = asyncio.Queue()
    interface = PartPickerInterface(from_queue, to_queue)
    serial = SerialInterface(args.serial_port, from_queue, to_queue)

    interface._status["POS File"] = args.position_file

    interface.add_log_message(f"Connected to {args.serial_port}.")

    await asyncio.gather(serial.reader(), serial.writer(), interface.run(), interface.get_key())

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()



