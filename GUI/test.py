import serial
ser = serial.Serial('/dev/cu.usbmodem21101', 9600)
cmd = 'Hi'
ser.write(cmd.encode('utf-8'))

