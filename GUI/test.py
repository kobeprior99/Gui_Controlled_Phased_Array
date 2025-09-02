import serial,time
ser = serial.Serial('/dev/cu.usbmodem21201', 9600)
time.sleep(1)
cmd = 'Hi'
ser.write(cmd.encode('utf-8'))

