import serial
from serial.tools import list_ports
import time

class PrinterController:

    ## Constructor
    def __init__(self):
        self.x_pos = 1
        self.y_pos = 1
        self.z_pos = 1
        self.ser_dev = None
    
    def find_arduino(self):
        ## list ports 
        ports = list_ports.comports()

        for port in ports:
        ## VID/PID Arduino Uno 0x2341/0x043
            if port.vid == 0x2341 and port.pid == 0x0043:
                return port.device
        return None
    
    ################# Init Routines #################
    def set_steps_mm(self):
        print('Setting correct values of [steps per mm]')
        self.ser_dev.write("$100=6.25\n".encode()) ## x axis
        time.sleep(1)
        self.read_serial()
        self.ser_dev.write("$101=6.25\n".encode()) ## y axis 
        time.sleep(1)
        self.read_serial()
        self.ser_dev.write("$102=25\n".encode()) ## z axis 
        time.sleep(1)
        self.read_serial()
        return 
    
    def init_controller(self):
        ## find the arduino
        port = self.find_arduino()
        if not port:
            print('Arduino not found')
            return False
        ## open the serial port
        self.ser_dev = serial.Serial(port, 115200, timeout=1)
        time.sleep(2) ## wait for the serial port to open
        print('Serial Port Opened')
        self.read_serial()
        
        ## remind user to manually set the printer to 0,0,0
        _ = input('Is the printer in position 0,0?')
        self.send_command() ## init to position 1,1,1
        self.read_serial()
        self.set_steps_mm() ## set correct steps per mm
        return True


    ######### Serial communication routines #########
    def read_serial(self):
        while True:
            resp = self.ser_dev.readline()
            if not resp:
                return ## done reading data from serial port
            print(resp)
    
    def send_command(self):
        command = "G0 X" + str(self.x_pos) +" Y" +str(self.y_pos) + " Z" +str(self.z_pos) + '\n'
        print('Sending Command: ' + command)
        self.ser_dev.write(command.encode())
        time.sleep(1)
        self.read_serial()
        return

 
    ################# Movement Routines #################
    def move_up(self, num_steps):
        print('Moving Up')
        self.y_pos = self.y_pos + num_steps
        return 
    
    def move_down(self, num_steps):
        print('Moving Down')
        self.y_pos = self.y_pos - num_steps
        return

    def move_left(self, num_steps):
        print('Moving Left')
        self.x_pos = self.x_pos + num_steps
        return

    def move_right(self, num_steps):
        self.x_pos = self.x_pos - num_steps
        return 
    
    def table_up(self, num_steps):
        self.z_pos = self.z_pos + num_steps
        return
    
    def table_down(self, num_steps):
        self.z_pos = self.z_pos - num_steps
        return
    
    def finish_move(self):
        print('Finishing Move')
        self.x_pos = 1
        self.y_pos = 1
        self.z_pos = 1
        return

    ################# HIGH LEVEL ROUTINES #################
    def interactive_moves(self, single_step=False): 
        while True:
            print('Move up = w\nMove down = s\nMove left = a\nMove right = d\nTable up = x\nTable down = z\nFinish Move = k')
            key = input('Press a key to move [awsd]')
            key = key.lower()
            if single_step:
                num = 1
            else:
                num = input('Enter number of steps [in mm]')

            match key:
                case 'w': 
                    self.move_up(int(num))
                case 's':
                    self.move_down(int(num))
                case 'a':
                    self.move_left(int(num))
                case 'd':
                    self.move_right(int(num))
                case 'x':
                    self.table_up(int(num))
                case 'z':
                    self.table_down(int(num))
                case 'k':
                    self.finish_move()
                    self.send_command()
                    return
                case _:
                    print('Invalid Key')
            self.send_command()

