from flask import Flask
from docker_service import DockerService
from discovery import Discovery
from datetime import datetime
import os
import threading
import time
import statistics
import logging

# Configuration
MIN_PERCENTAGE = float(os.getenv("AUTOSCALER_MIN_PERCENTAGE")) if os.getenv("AUTOSCALER_MIN_PERCENTAGE") else 25.0
MAX_PERCENTAGE = float(os.getenv("AUTOSCALER_MAX_PERCENTAGE")) if os.getenv("AUTOSCALER_MAX_PERCENTAGE") else 85.0
DISCOVERY_DNSNAME = os.getenv("AUTOSCALER_DNSNAME") if os.getenv("AUTOSCALER_DNSNAME") else 'tasks.autoscaler'
CHECK_INTERVAL = int(os.getenv("AUTOSCALER_INTERVAL")) if os.getenv("AUTOSCALER_INTERVAL") else 60*5 # Default 5 minutes
DRY_RUN = bool(os.getenv("AUTOSCALER_DRYRUN"))

# Initialize
App = Flask(__name__)
SwarmService = DockerService(DRY_RUN)
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', level=logging.DEBUG)

# Import controllers
from container_controller import *


def autoscallerLoop():
    """
        Main loop where getting services with enabled autoscale mode and calculate cpu utilization for scale service
    """
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
    """
        Method where calculate mean cpu percentage of service replicas and inc or dec replicas count
    """
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
