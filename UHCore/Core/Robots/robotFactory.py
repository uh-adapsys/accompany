import sys, os
# For testing
if __name__ == '__main__':
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../')
    sys.path.append(path)

from Data.dataAccess import Robots, Locations
from config import robot_config

class Factory(object):
    """Factory methods for creating Robot classes"""

    @staticmethod
    def getCurrentRobot():
        """ Retrieves the current Robot type from the database, given the active experiment location from the """
        """ session control table and constructs the appropriate class """ 
        activeLocation = Locations().getActiveExperimentLocation()
        if activeLocation == None:
            print "No experiment location set"
        elif activeLocation['activeRobot'] != None and activeLocation['activeRobot'] != '':
            robotData = Robots().getRobot(activeLocation['activeRobot'])
            if robotData != None and robotData['robotName'] != '':
                return Factory.getRobot(robotData['robotName'])
            else:
                print >> sys.stderr, "No data retrieved for robot ID %s" % activeLocation['activeRobot']
        else:
            print >> sys.stderr, "No robots set for experiment location %s" % activeLocation['location']
        
        return None

    @staticmethod
    def getRobot(robotName=None, spawn=False):
        """ Retrieves the named robot type from the database and constructs the appropriate class """
        """ if robotName is None or Empty, acts like getCurrentRobot() """
        if robotName == None or robotName == '':
            return Factory.getCurrentRobot()
        
        print "Building class for robot named: %s" % robotName
        # care-o-bot shortened to make 'in' easier to handle (only check first 9 characters)
        rosRobots = ['care-o-bo', 'sunflower']
        if robotName.lower()[:9] in rosRobots:
            if robotName.lower().startswith('care-o-bot'):
                if robot_config.has_key(robotName) and robot_config[robotName].has_key('hostname'):
                    rosMaster = 'http://%s:11311'
                else:
                    cobVersion = robotName[11:].replace('.', '-')
                    rosMaster = "http://cob%s-pc1:11311" % cobVersion
                imports = ['from careobot import CareOBot']
                args = (robotName, rosMaster, )
                kwargs = {}
                className = 'CareOBot'
            elif robotName.lower().startswith('sunflower'):
                if robot_config.has_key(robotName) and robot_config[robotName].has_key('hostname'):
                    rosMaster = 'http://%s:11311'
                else:
                    cobVersion = robotName[10:].replace('.', '-')
                    rosMaster = "http://sunflower%s-pc1:11311" % cobVersion
                imports = ['from sunflower import Sunflower']
                args = (robotName, rosMaster, )
                kwargs = {}
                className = 'Sunflower'

            # Set the LD_LIBRARY_PATH before forking
            from rosHelper import ROS
            rosENV = ROS._parseBashEnviron()
            rosLD = rosENV.get('LD_LIBRARY_PATH', '')
            curLD = os.environ.get('LD_LIBRARY_PATH')
            os.environ['LD_LIBRARY_PATH'] = curLD + ',' + rosLD
            
            if spawn:
                # Create the wrapper (runs the named class in a sub-process)
                from subProcessWrapper import SubProcessWrapper
                robot = SubProcessWrapper(imports, className, *args, **kwargs)
            
                # Now revert LD_LIBRARY_PATH for this process
                os.environ['LD_LIBRARY_PATH'] = curLD
            else:
                for import_ in imports:
                    exec(import_, globals())
                print globals().keys()
                robot = globals()[className](*args, **kwargs)
        elif robotName.lower().startswith('dummy'):
            import dummy
            robot = dummy.DummyRobot(robotName)
        else:
            print >> sys.stderr, "Unknown robot %s" % robotName
            return None

        print "Finished building class %s" % robot.__class__.__name__
        return robot

if __name__ == '__main__':
    c = Factory.getRobot('Care-O-Bot 3.2')
    s = Factory.getRobot('Sunflower 1-1')
    
    print c.getPID()
    print s.getPID()
    
    import time
    time.sleep(1000)
    c.join()
