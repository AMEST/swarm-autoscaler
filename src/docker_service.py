#!/bin/python
import docker
import logging
from cache import Cache

class DockerService(object):
    AutoscaleLabel = 'swarm.autoscale'
    MaxReplicasLabel = 'swarm.autoscale.max'
    MinReplicasLabel = 'swarm.autoscale.min'
    DisableManualReplicasControlLabel = 'swarm.autoscale.disable-manual-replicas'

    def __init__(self, memoryCache: Cache, dryRun: bool):
        self.memoryCache = memoryCache
        self.dryRun = dryRun
        self.dockerClient = docker.from_env()
        self.nodeInfo = self.dockerClient.info()

    def isManager(self):
        try:
            self.dockerClient.nodes.list()
            return True
        except:
            return False

    def isLeader(self):
        if(not self.isManager()):
            return False
        nodeList = self.dockerClient.nodes.list(filters={'role': 'manager'})
        nodeAddr = self.nodeInfo['Swarm']['NodeAddr']
        managerLeader = list(x for x in nodeList if x.attrs['ManagerStatus']['Leader'])[0]
        return managerLeader.attrs['ManagerStatus']['Addr'].startswith(nodeAddr)

    def getAutoscaleServices(self):
        allServices = self.dockerClient.services.list(filters={'label':self.AutoscaleLabel})
        if(len(allServices) == 0):
            return None
        enabledAutoscaleServices = list((x for x in allServices if x.attrs['Spec']['Labels'][self.AutoscaleLabel] == 'true'))
        return enabledAutoscaleServices

    def getServiceContainersId(self, service):
        tasks = service.tasks({'desired-state':'running'})
        if(len(tasks) == 0):
            return None
        return list((x['Status']['ContainerStatus']['ContainerID'] for x in tasks))

    def getServiceCpuLimitPercent(self, service):
        try:
            return service.attrs.get('Spec').get('TaskTemplate').get('Resources').get('Limits').get('NanoCPUs')/10000000/100
        except:
            return -1.0

    def getContainerCpuStat(self, containerId, cpuLimit):
        containers = self.dockerClient.containers.list(filters={'id':containerId})
        if(len(containers) == 0):
            return None
        containerStats = containers[0].stats(stream=False)
        return self.__calculateCpu(containerStats, cpuLimit)

    def scaleService(self, service, scaleIn = True):
        replicated = service.attrs['Spec']['Mode'].get('Replicated')
        if(replicated == None):
            logging.error("Cannot scale service %s because is not replicated mode", service.name)
            return
        
        maxReplicasPerNode = self.__getServiceMaxReplicasPerNode(service)
        nodeCount = self.__getNodesCountCached()

        maxReplicas = service.attrs['Spec']['Labels'].get(self.MaxReplicasLabel)
        maxReplicas = 15 if maxReplicas == None else int(maxReplicas)

        minReplicas = service.attrs['Spec']['Labels'].get(self.MinReplicasLabel)
        minReplicas = 2 if minReplicas == None else int(minReplicas)

        disableManualReplicas = service.attrs['Spec']['Labels'].get(self.DisableManualReplicasControlLabel) == 'true'

        replicas = replicated['Replicas']
        newReplicasCount = replicas + 1 if scaleIn else replicas - 1
        if(maxReplicasPerNode != None and maxReplicasPerNode != 0 and (nodeCount * maxReplicasPerNode) < newReplicasCount):
            logging.warning("There is no required number of nodes to host service (%s) instances. Nodes: %s. MaxReplicasPerNode: %s", service.name, nodeCount, maxReplicasPerNode)
            return

        if(disableManualReplicas):
            if(newReplicasCount < minReplicas):
                newReplicasCount = minReplicas
            if(newReplicasCount > maxReplicas):
                newReplicasCount = maxReplicas

        if(replicas == newReplicasCount):
            logging.debug('Replicas count not changed for the service (%s)', service.name)
            return

        if(newReplicasCount < minReplicas or newReplicasCount > maxReplicas):
            logging.debug('The limit for decreasing (%s) or increasing (%s) the number of instances for the service (%s) has been reached. NewReplicasCount: %s',
            minReplicas, maxReplicas, service.name, newReplicasCount)
            return

        logging.info("Scale service %s to %s",service.name, newReplicasCount)

        if(self.dryRun):
            return
            
        service.scale(newReplicasCount)
        
    def __calculateCpu(self, stats, cpuLimit):
        percent = 0.0
        cpuCount = stats['cpu_stats']['online_cpus']
        cpuDelta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
        systemDelta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
        if( cpuDelta > 0.0 and systemDelta > 0.0 ):
            percent = (cpuDelta / systemDelta) * len(stats['precpu_stats']['cpu_usage']['percpu_usage']) * 100.0
        
        # Correction of the percentage of workload given the limit or, in its absence, the number of CPUs to get a value in the range of 0 - 100
        if(cpuLimit > 0):
            percent = percent / cpuLimit
        else:
            percent = percent / cpuCount
        return percent

    def __getNodesCountCached(self):
        cacheKey = "nodes_count"
        nodesCount = self.memoryCache.get(cacheKey)
        if ( nodesCount != None ):
            return nodesCount
        return self.memoryCache.set(cacheKey, len(self.dockerClient.nodes.list()), 30)

    def __getServiceMaxReplicasPerNode(self, service):
        try:
            return service.attrs.get('Spec').get('TaskTemplate').get('Placement').get('MaxReplicas')
        except:
            return None
