# StePyMom - Network Monitor

import json
import os
import platform
import datetime

from log import *
from pushbullet import Pushbullet
from pymongo import MongoClient

# Create logger
logger = createLog('system','./stepymom.log')
logger.info('StePyMom Started')

# Get script directory
script_dir = os.path.dirname(os.path.realpath(__file__))

# Check for test environment flag file
if os.path.exists('./testenv'):
    test_env = '.test'
else:
    test_env = ''

# Get host name and build config file accordingly
host_name = platform.node()

os_platform = platform.system().lower()
config_file = 'config/' + host_name + test_env + '.config.json'

# Read config file
logger.info('Reading config: ' + config_file)
with open(config_file) as config_json:    
    config = json.load(config_json)

# Set options from config file
bPBNotify = config['PBNotify']
bPBNotify = True
pb = Pushbullet(config['pbAPIKey'])
timeDailyStatus = config['dailyStatusTime']
maxNotifications = config['maxNotifications']

user_string = ''
if 'dbUser' in config:
    user_string = "{user}:{pwd}@".format(user = config['dbUser'], pwd = config['dbPass'])

conn_string = "mongodb://{userinfo}{host}:{port}".format(userinfo = user_string, host = config['dbHost'], port = config['dbPort'])

client = MongoClient(conn_string)
db = client[config['dbName']]
logger.info('Opening MongoDB database: ' + config['dbName'])

# Clear config collection and repopulate with contents of config JSON file
colConfig = db['config']
colConfig.remove({})
colConfig.insert_one(config)

colHostStatus = db['host_status']
colIncidents = db['incidents']


def ping(host):
    # Ping parameters as function of OS
    parameters = "-n 1" if os_platform == "windows" else "-c 1"
    redirect = " > nul" if os_platform == "windows" else " > /dev/null"
    cmd = "ping " + parameters + " " + host + redirect

    return os.system(cmd) == 0


txtError = ''
bError = False

class Incident():
   
    def __init__(self, host, operation, description):
        self.host = host
        self.operation = operation
        self.description = description
        self.last_check = str(datetime.datetime.now())
        self.existdb = False
                
    def exist(self):
        self.data = colIncidents.find_one({'host': self.host, 'operation': self.operation, 'date_cleared': None})
        
        if self.data != None:
            self.existdb = True
            self.load()
        
        return self.existdb

    def load(self):
        self.create_time = self.data['create_time']
        self.num = self.data['num']
        self.count = self.data['count']
        self.date_cleared = self.data['date_cleared']
        self.object_id = self.data['_id']

                
    def create(self):
            self.create_time = str(datetime.datetime.now())
            self.num = self.create_time
            self.date_cleared = None
            self.count = 0
            

    def save(self):
        incidentData = {
            'create_time': self.create_time,
            'host': self.host,
            'operation': self.operation,
            'description': self.description,
            'last_check': self.last_check,
            'num': self.num,
            'count': self.count,
            'date_cleared': self.date_cleared
        }
        if self.existdb:
            result = colIncidents.update_one({'_id':self.object_id}, {"$set": incidentData}, upsert=False)
        else:
            result = colIncidents.insert_one(incidentData)

    def clearAll(self):
        colIncidents.remove({})
    
    def clear(self):
        pass
        colIncidents.remove({'_id':self.object_id})
        #os.remove(self.filename)

def pbNotify(subject, message):
    if bPBNotify == True:
        pass
        push = pb.push_note(subject, txtError)
    else:
        logger.info('[Pushbullet Notification Disabled] ' + subject + ' : ' + message)

for host in config['hosts']:
    hostStatus = "UNKNOWN"
    logger.info('Checking host ' + host['host'])
    incident = Incident(host['host'], 'ping', host['description'])

    # Get current timestamp
    checkTime = str(datetime.datetime.now())

    if ping(host['host']):
        logger.info(' . OK')
        hostStatus = "UP"
        if incident.exist() == True:
            logger.info('Incident Object ID: ' + str(incident.object_id))
            logger.info('Sending Incident Cleared Notification for Incident: ')
            
            txtClear = 'Incident number ' + incident.num + 'Initially logged at ' + incident.create_time + ' involving host ' + incident.host + ' operation ' + incident.operation + ' has been cleared.'
            pbNotify("StePyMOM Incident Cleared", txtClear)
            txtClear = None
            
            incident.clear()
        
    else:
        logger.error('Unable to ping host: ' + host['description'] + '(' + host['host'] + ')')
        logger.info('Checking for incident')
        hostStatus = "DOWN"
        
        if incident.exist():
            pass            
            logger.info('Incident Object ID: ' + str(incident.object_id))
        else:
            incident.create()
        
        incident.count += 1

        if incident.count < maxNotifications:
            txtError += '[Incident ' + incident.num + '] Unable to ping host: ' + host['description'] + '(' + host['host'] + ') \n'
            bError = True
        elif incident.count == maxNotifications:
            txtError += '[Incident ' + incident.num + '] Unable to ping host: ' + host['description'] + '(' + host['host'] + ') This is the final notification you will receive until this incident is cleared. \n'
            bError = True
        else:
            logger.info('Incident has occurred ' + str(incident.count) + ' times which exceeds the maximum notifcations of ' + str(maxNotifications) + ' notifications')
        
        incident.save()
    
    
    host_data = {
        'timestamp': checkTime,
        'host': host['host'],
        'description': host['description'],
        'status': hostStatus
    }
    result = colHostStatus.insert_one(host_data)
    #print('One post: {0}'.format(result.inserted_id))

if bError == True:
    logger.info('Sending PushBullet Notifcation')
    pbNotify("StePyMOM Error", txtError)

logger.info('StePyMom Exiting')