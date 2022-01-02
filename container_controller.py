from flask import request
from main import App, SwarmService

# Search by container hostname
@App.route('/api/container/stats', methods=['GET'])
def getContainerStats():
    containerId = request.args.get('id')
    cpuLimit = float(request.args.get('cpuLimit'))
    stats = SwarmService.getContainerCpuStat(containerId, cpuLimit)
    if(stats == None):
        return "Container with id=%s not running on this node" %(containerId), 404
    return {'ContainerId':containerId, 'cpu': stats}

