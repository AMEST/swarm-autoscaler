#!/bin/python
import os
import socket
from requests import get
import json
from cache import Cache


class Discovery(object):
    DiscoveryCacheKey = "discovery_hosts"
    def __init__(self, discoveryDnsName, memoryCache: Cache, checkInterval: int):
        self.cache = memoryCache
        self.cacheTime = checkInterval / 2
        self.discoveryName = discoveryDnsName
        self.addrInfoExpectedType = socket.SOCK_STREAM
        if(os.name == 'nt'):
            self.addrInfoExpectedType = 0

    def getContainerStats(self, containerId, cpuLimit):
        return self.__sendToAll("/api/container/stats?id=%s&cpuLimit=%s" %
                         (containerId, cpuLimit))

    def __sendToAll(self, url):
        for ip in self.__getClusterHosts():
            result = get("http://%s%s" %(ip,url))
            if(result != None and result.status_code == 200):
                return json.loads(result.text)
        return None

    def __getClusterHosts(self):
        cachedHosts = self.cache.get(self.DiscoveryCacheKey)
        if(cachedHosts != None):
            return cachedHosts
        
        hosts = []
        dnsResult = socket.getaddrinfo(self.discoveryName, 80)
        for info in dnsResult:
            if(info[0] == socket.AF_INET and info[1] == self.addrInfoExpectedType):
                hosts.append(info[4][0])

        return self.cache.set(self.DiscoveryCacheKey, hosts, self.cacheTime)
