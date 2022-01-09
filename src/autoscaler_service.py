from multiprocessing.dummy import Pool as ThreadPool
import threading
import time
import statistics
import logging
from discovery import Discovery

from docker_service import DockerService

class AutoscalerService(threading.Thread):
    def __init__(self, swarmService: DockerService, discovery: Discovery, checkInterval: int, minPercentage: int, maxPercentage: int):
        threading.Thread.__init__(self)
        self.swarmService = swarmService
        self.discovery = discovery
        self.checkInterval = checkInterval
        self.minPercentage = minPercentage
        self.maxPercentage = maxPercentage
        self.autoscaleServicePool = ThreadPool(8)
        self.logger = logging.getLogger("AutoscalerService")
 
    def run(self):
        """
        Run the thread
        """
        while True:
            try:
                if(not self.swarmService.isLeader()):
                    self.logger.warning("Instance running not on manager or not on leader")
                    time.sleep(60*10) # Wait 10 minute
                    continue
                services = self.swarmService.getAutoscaleServices()
                services = services if services != None else []
                self.logger.debug("Services len: %s", len(services))
                self.autoscaleServicePool.map(self.__autoscale, services)    
            except Exception as e:
                self.logger.error("Error in autoscale thread", exc_info=True)
            time.sleep(self.checkInterval)

    def __autoscale(self, service):
        cpuLimit = self.swarmService.getServiceCpuLimitPercent(service)
        containers = self.swarmService.getServiceContainersId(service)
        stats = []
        for id in containers:
            containerStats = self.discovery.getContainerStats(id, cpuLimit)
            if(containerStats != None):
                stats.append(containerStats['cpu'])
        if(len(stats) > 0):
            self.__scale(service, stats)

    def __scale(self, service, stats):
        """
            Method where calculate mean cpu percentage of service replicas and inc or dec replicas count
        """
        meanCpu = statistics.mean(stats)
        self.logger.debug("Mean cpu for service=%s : %s",service.name,meanCpu)
        try:
            if(meanCpu > self.maxPercentage):
                self.swarmService.scaleService(service, True)
            elif(meanCpu < self.minPercentage):
                self.swarmService.scaleService(service, False)
            else:
                self.logger.debug("Service %s not needed to scale", service.name)
        except Exception as e:
            self.logger.error("Error while try scale service", exc_info=True)