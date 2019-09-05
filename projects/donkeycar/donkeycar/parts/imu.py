import time

class Mpu6050:
    '''
    Installation:
    sudo apt install python3-smbus
    or
    sudo apt-get install i2c-tools libi2c-dev python-dev python3-dev
    git clone https://github.com/pimoroni/py-smbus.git
    cd py-smbus/library
    python setup.py build
    sudo python setup.py install

    pip install mpu6050-raspberrypi
    '''

    def __init__(self, addr=0x68, poll_delay=0.0166):
        from mpu6050 import mpu6050
        self.sensor = mpu6050(addr)
        self.accel = { 'x' : 0., 'y' : 0., 'z' : 0. }
        self.gyro = { 'x' : 0., 'y' : 0., 'z' : 0. }
        self.temp = 0.
        self.poll_delay = poll_delay
        self.on = True

    def update(self):
        while self.on:
            self.poll()
            time.sleep(self.poll_delay)
                
    def poll(self):
        try:
            self.accel, self.gyro, self.temp = self.sensor.get_all_data()
        except:
            print('failed to read imu!!')
            
    def run_threaded(self):
        return self.accel['x'], self.accel['y'], self.accel['z'], self.gyro['x'], self.gyro['y'], self.gyro['z'], self.temp
    def run(self):
        self.poll()
        return self.accel['x'], self.accel['y'], self.accel['z'], self.gyro['x'], self.gyro['y'], self.gyro['z'], self.temp

    def shutdown(self):
        self.on = False


if __name__ == "__main__":
    iter = 0
    p = Mpu6050()
    accelxSigma=0
    accelySigma=0
    accelzSigma=0
    gyroxSigma=0
    gyroySigma=0
    gyrozSigma=0
    while iter < 100:
        data = p.run()
        accelxSigma+=data[0]
        accelySigma+=data[1]
        accelzSigma+=data[2]
        gyroxSigma+=data[3]
        gyroySigma+=data[4]
        gyrozSigma+=data[5]
        #print(data)
        time.sleep(0.1)
        iter += 1
    accelxSigma/=100
    accelySigma/=100
    accelzSigma/=100
    gyroxSigma=/100
    gyroySigma/=100
    gyrozSigma/=100
    print "accelx: ",accelxSigma
    print "accely: ",accelySigma
    print "accelz: ",accelzSigma
    print "gyrox: ",gyroxSigma
    print "gyroy: ",gyroySigma
    print "gyroz: ",gyrozSigma
