#!/bin/python
import os
import socket
from requests import get
import json


class Discovery(object):
    def __init__(self, discoveryDnsName):
        self.discoveryName = discoveryDnsName
        self.addrInfoExpectedType = socket.SOCK_STREAM
        if(os.name == 'nt'):
            self.addrInfoExpectedType = 0

    def getContainerStats(self, containerId, cpuLimit):
        return self.sendToAll("/api/container/stats?id=%s&cpuLimit=%s" %
                         (containerId, cpuLimit))

    def sendToAll(self, url):
        for ip in self.getClusterHosts():
            result = get("http://%s%s" %(ip,url))
            if(result != None and result.status_code == 200):
                return json.loads(result.text)
        return None


    def getClusterHosts(self):
        hosts = []
        dnsResult = socket.getaddrinfo(self.discoveryName, 80)
        for info in dnsResult:
            if(info[0] == socket.AF_INET and info[1] == self.addrInfoExpectedType):
                hosts.append(info[4][0])
        return hosts
