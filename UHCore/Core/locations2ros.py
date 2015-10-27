#!/usr/bin/env python
import math

from Data.dataAccess import Sensors, Locations
from Robots.rosHelper import ROS
from extensions import PollingProcessor


class ROSLocationProcessor(PollingProcessor):
    """Abstract location processor, current concrete implementations are Human and Robot processors"""

    def __init__(self):
        super(ROSLocationProcessor, self).__init__()
        self._lastSensors = {}
        self._lastLocations = {}
        self._sensors = Sensors()
        self._locations = Locations()
        self._ros = ROS()

    def start(self):
        print "Started polling uh locations"
        self._addPollingProcessor('location_publish', self.checkUpdateLocations, (), 0.1)
        self._addPollingProcessor('sensor_publish', self.checkUpdateSensors, (), 0.1)

    def stop(self):
        print "Stopped polling uh locations"
        self._removePollingProcessor('location_publish')
        self._removePollingProcessor('sensor_publish')

    def checkUpdateLocations(self):
        locationData = self._locations.findLocations()
        locations = {}
        for location in locationData:
            locationParam = {
                'id': location['locationId'],
                'text': location['name'] or '',
                'color': {'r': float(not location['ValidRobotLocation'] and not location['ValidUserLocation']),
                          'g': float(location['ValidRobotLocation'] or 0),
                          'b': float(location['ValidUserLocation'] or 0),
                          'a': 1.0}
            }
            
            if location.get('xCoord', None) is not None:
                locationParam.setdefault('position', {})
                locationParam['position']['x'] = location.get('xCoord')
            
            if location.get('yCoord', None) is not None:
                locationParam.setdefault('position', {})
                locationParam['position']['y'] = location.get('yCoord')
            
            if location.get('zCoord', None) is not None:
                locationParam.setdefault('position', {})
                locationParam['position']['z'] = location.get('zCoord')

            if location.get('orientation', None) is not None:
                locationParam.setdefault('orientation', {})
                locationParam['orientation']['theta'] = math.radians(location['orientation'])
                
            locations[locationParam['id']] = locationParam

        if self._lastLocations != locations:
            self._lastLocations = locations
            self._ros.setParam('location_data', locations.values())

    def checkUpdateSensors(self):
        sensorData = self._sensors.findSensors()
        sensors = {}
        for sensor in sensorData:
            sensorParam = {
                'id': sensor['sensorId'],
                'text': sensor['name'] or '',
                'model': sensor['iconName'] or '',
                'color': {'r': 0,
                          'g': 0,
                          'b': 0,
                          'a': 0}
            }
            
            if sensor.get('xCoord', None) is not None:
                sensorParam.setdefault('position', {})
                sensorParam['position']['x'] = sensor.get('xCoord')
            
            if sensor.get('yCoord', None) is not None:
                sensorParam.setdefault('position', {})
                sensorParam['position']['y'] = sensor.get('yCoord')
            
            if sensor.get('zCoord', None) is not None:
                sensorParam.setdefault('position', {})
                sensorParam['position']['z'] = sensor.get('zCoord')

            if sensor['orientation'] is not None:
                sensorParam.setdefault('orientation', {})
                sensorParam['orientation']['theta'] = math.radians(sensor['orientation'])

            if sensor['isActive']:
                sensorParam['color']['r'] = 0
                sensorParam['color']['g'] = 1.0
                sensorParam['color']['b'] = 0
                sensorParam['color']['a'] = 1.0

            if sensor['xCoord'] is None and sensor['yCoord'] is None:
                sensorParam['position']['z'] = -1
                
            sensors[sensorParam['id']] = sensorParam

        if self._lastSensors != sensors:
            self._lastSensors = sensors
            self._ros.setParam('sensor_data', sensors.values())


if __name__ == '__main__':
    import sys
    lp = ROSLocationProcessor()
    lp.start()
    while True:
        try:
            sys.stdin.read()
        except KeyboardInterrupt:
            break
    lp.stop()
