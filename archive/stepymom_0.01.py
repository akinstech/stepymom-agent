import json
import os
import platform

from log import *
from pushbullet import Pushbullet

osPlatform = platform.system().lower()

fileConfig = "./config.json"

# Create logger
logger = createLog('system','./stepymom.log')

logger.info('StePyMom Started')

def ping(host):
    # Ping parameters as function of OS
    parameters = "-n 1" if osPlatform == "windows" else "-c 1"
    redirect = " > nul" if osPlatform == "windows" else " > /dev/null"
    cmd = "ping " + parameters + " " + host + redirect
    
    
    # Ping
    return os.system(cmd) == 0

# Read host list
logger.info('Reading config: ' + fileConfig)
with open(fileConfig) as jsonConfig:    
    config = json.load(jsonConfig)


pb = Pushbullet(config['pbAPIKey'])

txtError = ''
bError = False


for host in config['hosts']:
    logger.info('Checking host ' + host['host'])
    if ping(host['host']):
        logger.info(' . OK')
    else:
        logger.error('Unable to ping host: ' + host['description'] + '(' + host['host'] + ')')
        txtError += 'Unable to ping host: ' + host['description'] + '(' + host['host'] + ') \n'
        bError = True
#print(pb.devices)

if bError == True:
    logger.info('Sending PushBullet Notifcation')
    push = pb.push_note("StePyMOM Error", txtError)

logger.info('StePyMom Exiting')