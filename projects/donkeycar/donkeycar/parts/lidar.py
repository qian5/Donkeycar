"""
Lidar
"""

import time
import math
import pickle
import serial
import numpy as np
from donkeycar.utils import norm_deg, dist, deg2rad, arr_to_img
from PIL import Image, ImageDraw

class RPLidar(object):
    '''
    https://github.com/SkoltechRobotics/rplidar
    '''
    def __init__(self, port='/dev/ttyUSB0'):
        from rplidar import RPLidar
        self.port = port
        self.distances1 = 0
        self.angles1 = 0 
        self.distances2 = 0 
        self.angles2 = 0
        self.distances3 = 0
        self.angles3 = 0
        self.lidar = RPLidar(self.port)
        self.lidar.clear_input()
        time.sleep(1)
        self.on = True
        #print(self.lidar.get_info())
        #print(self.lidar.get_health())


    def update(self):
        scans = self.lidar.iter_scans(550)
        while self.on:
            try:
                d1=0
                d1_num=0
                a1=0
                a1_num=0
                d2=0
                d2_num=0
                a2=0
                a2_num=0
                d3=0
                d3_num=0
                a3=0
                a3_num=0
                for scan in scans:
                    for index in range(len(scan)):                      
                        if scan[index][1]>=90 and scan[index][1]<150:
                            d1 += scan[index][2]
                            d1_num=d1_num+1
                            a1 += scan[index][1]
                            a1_num=d1_num+1
                        elif scan[index][1]>=150 and scan[index][1]<210:
                            d2 += scan[index][2]
                            d2_num=d1_num+1
                            a2 += scan[index][1]
                            a2_num=d1_num+1
                        elif scan[index][1]>=210 and scan[index][1]<270:
                            d3 += scan[index][2]
                            d3_num=d1_num+1
                            a3 += scan[index][1]
                            a3_num=d1_num+1
                        elif (int(scan[index][1]))==359 and d1_num!=0:
                            self.distances1 = d1/d1_num
                            self.angles1 = a1/a1_num
                            self.distances2 = d2/d2_num
                            self.angles2 = a2/a2_num
                            self.distances3 = d3/d3_num
                            self.angles3 = a3/a3_num
                            d1=0
                            d1_num=0
                            a1=0
                            a1_num=0
                            d2=0
                            d2_num=0
                            a2=0
                            a2_num=0
                            d3=0
                            d3_num=0
                            a3=0
                            a3_num=0
                            '''
                            print ("angles: ",self.angles2)
                            print ("distances: ",self.distances2)
                            '''
                    '''
                    self.distances = [item[2] for item in scan]
                    self.angles = [item[1] for item in scan]
                  '''
            except serial.serialutil.SerialException:
                print('serial.serialutil.SerialException from Lidar. common when shutting down.')

    def run_threaded(self):
        return self.distances1, self.angles1,self.distances2, self.angles2,self.distances3, self.angles3

    def run(self):
        return self.distances1, self.angles1
    
    def shutdown(self):
        self.on = False
        time.sleep(2)
        self.lidar.stop()
        self.lidar.stop_motor()
        self.lidar.disconnect()


class LidarPlot(object):
    '''
    takes the raw lidar measurements and plots it to an image
    '''
    PLOT_TYPE_LINE = 0
    PLOT_TYPE_CIRC = 1
    def __init__(self, resolution=(500,500),
        max_dist=1000, #mm
        radius_plot=3,
        plot_type=PLOT_TYPE_CIRC):
        self.frame = Image.new('RGB', resolution)
        self.max_dist = max_dist
        self.rad = radius_plot
        self.resolution = resolution
        if plot_type == self.PLOT_TYPE_CIRC:
            self.plot_fn = self.plot_circ
        else:
            self.plot_fn = self.plot_line
            

    def plot_line(self, img, dist, theta, max_dist, draw):
        '''
        scale dist so that max_dist is edge of img (mm)
        and img is PIL Image, draw the line using the draw ImageDraw object
        '''
        center = (img.width / 2, img.height / 2)
        max_pixel = min(center[0], center[1])
        dist = dist / max_dist * max_pixel
        if dist < 0 :
            dist = 0
        elif dist > max_pixel:
            dist = max_pixel
        theta = np.radians(theta)
        sx = math.cos(theta) * dist + center[0]
        sy = math.sin(theta) * dist + center[1]
        ex = math.cos(theta) * (dist + self.rad) + center[0]
        ey = math.sin(theta) * (dist + self.rad) + center[1]
        fill = 128
        draw.line((sx,sy, ex, ey), fill=(fill, fill, fill), width=1)
        
    def plot_circ(self, img, dist, theta, max_dist, draw):
        '''
        scale dist so that max_dist is edge of img (mm)
        and img is PIL Image, draw the circle using the draw ImageDraw object
        '''
        center = (img.width / 2, img.height / 2)
        max_pixel = min(center[0], center[1])
        dist = dist / max_dist * max_pixel
        if dist < 0 :
            dist = 0
        elif dist > max_pixel:
            dist = max_pixel
        theta = np.radians(theta)
        sx = int(math.cos(theta) * dist + center[0])
        sy = int(math.sin(theta) * dist + center[1])
        ex = int(math.cos(theta) * (dist + 2 * self.rad) + center[0])
        ey = int(math.sin(theta) * (dist + 2 * self.rad) + center[1])
        fill = 128

        draw.ellipse((min(sx, ex), min(sy, ey), max(sx, ex), max(sy, ey)), fill=(fill, fill, fill))

    def plot_scan(self, img, distances, angles, max_dist, draw):
        for dist, angle in zip(distances, angles):
            self.plot_fn(img, dist, angle, max_dist, draw)
            
    def run(self, distances, angles):
        '''
        takes two lists of equal length, one of distance values, the other of angles corresponding to the dist meas 
        '''
        self.frame = Image.new('RGB', self.resolution, (255, 255, 255))
        draw = ImageDraw.Draw(self.frame)
        self.plot_scan(self.frame, distances, angles, self.max_dist, draw)
        return self.frame

    def shutdown(self):
        pass


class BreezySLAM(object):
    '''
    https://github.com/simondlevy/BreezySLAM
    '''
    def __init__(self, MAP_SIZE_PIXELS=500, MAP_SIZE_METERS=10):
        from breezyslam.algorithms import RMHC_SLAM
        from breezyslam.sensors import Laser

        laser_model = Laser(scan_size=360, scan_rate_hz=10., detection_angle_degrees=360, distance_no_detection_mm=12000)
        MAP_QUALITY=5
        self.slam = RMHC_SLAM(laser_model, MAP_SIZE_PIXELS, MAP_SIZE_METERS, MAP_QUALITY)
    
    def run(self, distances, angles, map_bytes):
        
        self.slam.update(distances, scan_angles_degrees=angles)
        x, y, theta = self.slam.getpos()

        if map_bytes is not None:
            self.slam.getmap(map_bytes)

        #print('x', x, 'y', y, 'theta', norm_deg(theta))
        return x, y, deg2rad(norm_deg(theta))

    def shutdown(self):
        pass



class BreezyMap(object):
    '''
    bitmap that may optionally be constructed by BreezySLAM
    '''
    def __init__(self, MAP_SIZE_PIXELS=500):
        self.mapbytes = bytearray(MAP_SIZE_PIXELS * MAP_SIZE_PIXELS)

    def run(self):
        return self.mapbytes

    def shutdown(self):
        pass

class MapToImage(object):

    def __init__(self, resolution=(500, 500)):
        self.resolution = resolution

    def run(self, map_bytes):
        np_arr = np.array(map_bytes).reshape(self.resolution)
        return arr_to_img(np_arr)

    def shutdown(self):
        pass


if __name__ == "__main__":
    rplidar = RPLidar()
    iter =0
    while iter<100:
        data=rplidar.run()
        angles=data[0]
        distances=data[1]
        iter += 1
        print ("angles: ",angles)
        print ("distances: ",distances)
