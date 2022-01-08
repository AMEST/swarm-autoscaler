from flask import Flask
from autoscaler_service import AutoscalerService
from docker_service import DockerService
from discovery import Discovery
from cache import Cache
import os
import logging

# Configuration
MIN_PERCENTAGE = float(os.getenv("AUTOSCALER_MIN_PERCENTAGE")) if os.getenv("AUTOSCALER_MIN_PERCENTAGE") else 25.0
MAX_PERCENTAGE = float(os.getenv("AUTOSCALER_MAX_PERCENTAGE")) if os.getenv("AUTOSCALER_MAX_PERCENTAGE") else 85.0
DISCOVERY_DNSNAME = os.getenv("AUTOSCALER_DNSNAME") if os.getenv("AUTOSCALER_DNSNAME") else 'tasks.autoscaler'
CHECK_INTERVAL = int(os.getenv("AUTOSCALER_INTERVAL")) if os.getenv("AUTOSCALER_INTERVAL") else 60*5 # Default 5 minutes
DRY_RUN = bool(os.getenv("AUTOSCALER_DRYRUN"))

# Initialize
App = Flask(__name__)
MemoryCache = Cache()
SwarmService = DockerService(DRY_RUN)
DiscoveryService = Discovery(DISCOVERY_DNSNAME, MemoryCache, CHECK_INTERVAL)
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', level=logging.DEBUG)

# Import controllers
from container_controller import *

if __name__ == "__main__":
    autoscalerService = AutoscalerService(SwarmService, DiscoveryService, CHECK_INTERVAL, MIN_PERCENTAGE, MAX_PERCENTAGE)
    autoscalerService.setDaemon(True)
    autoscalerService.start()
    App.run(host='0.0.0.0', port=80)
