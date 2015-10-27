import io
import sys
import os
import math
import copy
from Data.dataAccess import Sensors
from xml.etree import ElementTree as et
from threading import RLock


class MapProcessor(object):
    """ Used to build the live image of the sensor network """
    _mapCache = {}
    _iconCache = {}
    _mapLock = RLock()
    _iconLock = RLock()

    def __init__(self, _map):
        self._root = os.path.dirname(os.path.realpath(__file__))
        self._baseFile = os.path.join(self._root, _map['base'])
        self._map = _map
        self._sensorTypes = {}
        self._dao = Sensors()

    @property
    def mapBase(self):
        """ Returns a copy of the base svg map file """
        """ Caches initial map for fast access in subsequent calls """
        if self._baseFile not in MapProcessor._mapCache:
            MapProcessor._mapLock.acquire()
            try:
                MapProcessor._mapCache[self._baseFile] = et.parse(self._baseFile)
            finally:
                MapProcessor._mapLock.release()

        return copy.deepcopy(MapProcessor._mapCache[self._baseFile])

    def getIcon(self, iconId, text=None, sensorOn=False):
        """ Returns the sensor icon (with option 'On' graphic') wrapped in a group node """
        """ Caches icon for fast access in subsequent calls """
        key = str(iconId) + str(sensorOn)
        if key not in MapProcessor._iconCache:
            MapProcessor._iconLock.acquire()
            try:
                if iconId not in self._sensorTypes:
                    self._sensorTypes[iconId] = self._dao.getSensorIcon(iconId)

                sensorDef = self._sensorTypes[iconId]

                imgFile = None
                imgPath = None
                imgName = None
                if sensorDef is not None:
                    imgName = sensorDef['name']
                    if sensorDef['icon'] is not None:
                        if sensorOn:
                            imgPath = sensorDef['icon'] + '_on' + ".svg"
                        else:
                            imgPath = sensorDef['icon'] + ".svg"

                        try:
                            imgFile = et.parse(os.path.join(self._root, imgPath))
                        except Exception as e:
                            if sensorOn:
                                print >> sys.stderr, "Error parsing sensor image (%(path)s): %(error)s" % {'error': e, 'path': imgPath}

                if imgFile is None:
                    if imgPath is not None:
                        print "Unable to load image from %(path)s, using default" % {'path': imgPath}
                    else:
                        print "Unable to load image for %(type)s, using default" % {'type': imgName}
                    imgPath = 'icons/default.svg'
                    imgFile = et.parse(os.path.join(self._root, imgPath))
                    imgFile.find('{http://www.w3.org/2000/svg}text').text = text or imgName or imgPath

                if sys.version_info >= (2, 7):
                    group = et.Element('g')
                else:
                    group = et.Element('ns0:g')

                for child in imgFile.getroot().getchildren():
                    group.append(et.fromstring(et.tostring(child)))

                height = float(imgFile.getroot().get('height', 0))
                width = float(imgFile.getroot().get('width', 0))

                MapProcessor._iconCache[key] = (group, height, width)
            finally:
                MapProcessor._iconLock.release()

        return copy.deepcopy(MapProcessor._iconCache[key])

    def buildMap(self, elements=[]):
        """elements=[{'state':'on', 'location':{'xCoord':2.3, 'yCoord':9.2', 'orientation':3.141}, 'id':12]"""
        """state must match from the sensor state=>sensor Icon mapping"""
        """state can be empty or missing to use a stateless icon"""
        """x and y are in meters"""
        """orientation is assumed in radians, use d or r suffix to use others (90d/6R)"""
        # TODO: when map is clicked, show RH coords

        if sys.version_info >= (2, 7):
            et.register_namespace("", "http://www.w3.org/2000/svg")

        root = self.mapBase.getroot()
        mapHeight = float(root.attrib['height'])
        cc = CoordinateConvertor(self._map)

        for element in elements:
            try:
                if element['on'] is None:
                    state = False
                else:
                    state = element['on']
            except:
                state = False
            (x, y, d) = cc.toScaled((element['xCoord'], element['yCoord'], element['orientation']))
            (img, height, width) = self.getIcon(element['icon'], element['name'], state)

            # svg y is from bottom corner
            My = mapHeight - y
            # be sure to translate first, which changes the local coordinate space to the group object
            # which is important for the rotation about the center
            transform = "translate(%(x)s, %(y)s) rotate(%(rotate)s, %(xCenter)s, %(yCenter)s)" % {
                'x': x,
                'y': My,
                'rotate': d,
                'xCenter': 0,
                'yCenter': 0
            }

            img.attrib['transform'] = transform
            img.attrib['id'] = str(element['id'])
            img.attrib['name'] = str(element['name'])
            root.append(img)

        # ElementTree.write() doesn't write the headers
        f = io.BytesIO()
        f.write('<?xml version=\"1.0\" standalone=\"no\"?>\n')
        f.write('<!DOCTYPE svg PUBLIC \"-//W3C//DTD SVG 1.1//EN\" \"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd\">\n')
        if sys.version_info >= (2, 7):
            f.write(et.tostring(root))
        else:
            f.write(et.tostring(root).replace('ns0:', '').replace(':ns0', ''))
        ret = f.getvalue()
        f.close()
        return ret


class CoordinateConvertor(object):
    """Convert between ROS MAP and SVG MAP coordinate systems"""

    def __init__(self, transform):
        self._scale = float(transform['svg_scale'])
        self._offset = transform['svg_offset']  # in sensorMapUnits
        self._rotation = transform['svg_rotation']
        self._rotation_direction = transform.get('svg_rotation_direction', -1)

    def toScaled(self, (x, y, theta)):
        """x and y are in meters"""
        """r is assumed in radians, use d or r suffix to use others (90d/3.14r)"""

        # Defaults for missing values
        x = x or 0
        y = y or 0
        theta = theta or 0

        scaledX = (x * self._scale) + self._offset['x']
        scaledY = (y * self._scale) + self._offset['y']
        
        scaledTheta = None
        if type(theta) == str:
            try:
                if theta.endswith('r'):
                    scaledTheta = math.degrees(float(theta.strip('r')))
                if theta.endswith('d'):
                    scaledTheta = float(theta.strip('d'))
            except:
                scaledTheta = 0

        scaledTheta = scaledTheta * self._rotation_direction
        scaledTheta = scaledTheta - self._rotation
        return (scaledX, scaledY, scaledTheta)
