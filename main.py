from flask import Flask
from docker_service import DockerService
from discovery import Discovery
from datetime import datetime
import os
import threading
import time
import statistics
import logging

MIN_PERCENTAGE = 25.0
MAX_PERCENTAGE = 80.0
DISCOVERY_DNSNAME = os.getenv("AUTOSCALER_DNSNAME") if os.getenv("AUTOSCALER_DNSNAME") else 'tasks.autoscaler'
CHECK_INTERVAL = int(os.getenv("AUTOSCALER_INTERVAL")) if os.getenv("AUTOSCALER_INTERVAL") else 60*5 # Default 5 minutes

App = Flask(__name__)
SwarmService = DockerService()
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)

from container_controller import *

def autoscallerLoop():
    global DISCOVERY_DNSNAME, CHECK_INTERVAL
    logging.info("Running autoscale loop")
    discovery = Discovery(DISCOVERY_DNSNAME)
    while True:
        try:
            if(not SwarmService.isLeader()):
                logging.warning("Instance running not on manager or not on leader")
                time.sleep(60*10) # Wait 10 minute
                continue
            services = SwarmService.getAutoscaleServices()
            logging.debug("Services len: %s", len(services))
            for service in services:
                cpuLimit = SwarmService.getServiceCpuLimitPercent(service)
                containers = SwarmService.getServiceContainersId(service)
                stats = []
                for id in containers:
                    containerStats = discovery.getContainerStats(id, cpuLimit)
                    if(containerStats != None):
                        stats.append(containerStats['cpu'])
                if(len(stats) > 0):
                    tryScale(service, stats)
        except Exception as e:
            logging.error("Error in autoscale loop", exc_info=True)
        time.sleep(CHECK_INTERVAL)

def tryScale(service, stats):
    global MAX_PERCENTAGE, MIN_PERCENTAGE
    meanCpu = statistics.mean(stats)
    logging.debug("Mean cpu for service=%s : %s",service.name,meanCpu)
    try:
        if(meanCpu > MAX_PERCENTAGE):
            SwarmService.scaleService(service, True)
        if(meanCpu < MIN_PERCENTAGE):
            SwarmService.scaleService(service, False)
    except Exception as e:
        logging.error("Error while try scale service", exc_info=True)

if __name__ == "__main__":
    autoScaleThread = threading.Thread(target=autoscallerLoop, daemon=True)
    autoScaleThread.start()
    App.run(host='0.0.0.0', port=80)
