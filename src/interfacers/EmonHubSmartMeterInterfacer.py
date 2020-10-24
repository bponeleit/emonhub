import serial
import time, datetime
from emonhub_interfacer import EmonHubInterfacer

import Cargo
import re
"""class EmonhubSmartMeterInterfacer

Monitors the serial port for data

"""

class EmonHubSmartMeterInterfacer(EmonHubInterfacer):

    def __init__(self, name, com_port='', com_baud=9600, option_select='\x06000\r\n', obis_codes='1.8.0', node_id='-1', wait='0.5'):
        """Initialize interfacer

        com_port (string): path to COM port

        """

        # Initialization
        super().__init__(name)

        # Open serial port
        self._ser = self._open_serial_port(com_port, com_baud)

        # Initialize RX buffer
        self._rx_buf = ''
        self._request_message = "/?!\r\n"
        self._option_select = option_select
        self._obis_codes = obis_codes
        self._node_id = node_id
        self._pattern = re.compile( r'(\d+-\d+:)?(\w+\.\w+.\d+)(\*\d+)?\((\w+(?:\.\w+)?)(\*)?([A-Za-z]+)?.*' )
        self._wait = wait
        self._log.debug("wait: " + self._wait)

    def close(self):
        """Close serial port"""

        # Close serial port
        if self._ser is not None:
            self._log.debug("Closing serial port")
            self._ser.close()

    def _open_serial_port(self, com_port, com_baud):
        """Open serial port

        com_port (string): path to COM port

        """

        #if not int(com_baud) in [75, 110, 300, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]:
        #    self._log.debug("Invalid 'com_baud': " + str(com_baud) + " | Default of 9600 used")
        #    com_baud = 9600

        try:
            s = serial.Serial(
#com_port, com_baud, timeout=10)
              port=com_port,
              baudrate=com_baud,
              parity=serial.PARITY_EVEN,
              stopbits=serial.STOPBITS_ONE,
              bytesize=serial.SEVENBITS,
              timeout=0.1
            )
            self._log.debug("Opening serial port: " + str(com_port) + " @ " + str(com_baud) + " bits/s")
        except serial.SerialException as e:
            self._log.error(e)
            s = False
            # raise EmonHubInterfacerInitError('Could not open COM port %s' % com_port)
        return s

    def read(self):
        """Read data from serial port and process if complete line received.

        Return data as a list: [NodeID, val1, val2]

        """

        if not self._ser:
            return False
        """
        # Read serial RX
        self._rx_buf = self._rx_buf + self._ser.readline().decode()

        # If line incomplete, exit
        if '\r\n' not in self._rx_buf:
            return

        # Remove CR,LF
        f = self._rx_buf[:-2]
        
        """
#        time.sleep(2)
        self._rx_buf = ''
        self._ser.write(self._request_message.encode())
#        self._log.info("wait: " + self._wait)
        time.sleep(float(self._wait))

#        if int(self._wait) > 1:
#             self._id = self._ser.readline().rstrip()
#             self._log.info("ID: " + self._id.decode())

#        time.sleep(float(self._wait))
        self._ser.write(self._option_select.encode()) #.decode("unicode-escape"))
        #self._log.debug(self._option_select.decode("string-escape"))
        #self._log.debug(self._option_select)
#        if (int(self._wait)) > 1:
#            time.sleep(0.5)
        
        # Read serial RX
        reads = 0
        while "\03" not in self._rx_buf:
            reads += 1
            #mystring = self._ser.read().decode()
            #self._log.debug(str(reads) + ": " + mystring + ":")
            #self._log.debug("_rx_buf: " + str(reads) + "|" + self._rx_buf)
            #self._rx_buf = self._rx_buf + self._ser.read().decode()
            self._rx_buf = self._rx_buf + self._ser.read().decode()
            #self._log.debug("_rx_buf: " + str(reads) + "|" + str(self._rx_buf))
            if reads > 300:
                break

        #self._log.info("after loop: " + self._rx_buf)
        self._ser.read()
        
        f = self._rx_buf[:-2]
        
        if f[4:] == "/PAF":
           self._log.info("\r\nPAF found")
        self._log.debug("f: " + f)

       # Reset buffer
        self._rx_buf = ''

        f = self._process_frame(f)
        f = str(f[0]) + " " + str(f[1:][0]) + " " + str(f[1:][1])

        # Create a Payload object
        c = Cargo.new_cargo(rawdata=f)

        f = f.split()

        if int(self._settings['nodeoffset']):
            c.nodeid = int(self._settings['nodeoffset'])
            c.realdata = f
        else:
            c.nodeid = int(f[0])
            c.realdata = f[1:]

        return c

    def _process_frame(self, f):
        """Process a frame of data
        
        f (string): 'NodeID val1 val2 ...'
        This function splits the string into numbers and check its validity.
        'NodeID val1 val2 ...' is the generic data format. If the source uses 
        a different format, override this method.
        
        Return data as a list: [NodeID, val1, val2]
        """

        # Log data
        self._log.info("Serial RX: " + f)
        
        # Get an array out of the space separated string
        received = f.strip().splitlines()
        
        # Discard if frame not of the form [node, val1, ...]
        # with number of elements at least 2
        if (len(received) < 2):
            self._log.warning("1 Misformed RX frame: " + str(received))
        
        # Else, process frame
        else:
            try:
                self._log.debug("Begin process")
                #self._log.debug(self._obis_codes)
                #test1 = [self._pattern.match( line ) for line in f.strip().splitlines()]
                #self._log.debug(test1)
                #test = [val.group( 2, 4 ) for val in test1 if val <> None]
                #self._log.debug(test)
                #test2 = [val[1] for val in test if val[0] in self._obis_codes]
                #self._log.debug(test2)
                received = [str(self._node_id)]
                received.extend([float(val[1]) for val in (match.group( 2, 4 ) for match in filter(bool, map(self._pattern.match, f.strip().splitlines()))) if val[0] in self._obis_codes])
                #received = [float(val) for val in received]
            except Exception as e:
                self._log.warning("Misformed RX frame: " + str(received))
                self._log.warning(str(e))
            else:
                self._log.debug("Node: " + str(received[0]))
                self._log.debug("Values: " + str(received[1:]))
                return received
