from flask import request
from main import App, SwarmService

@App.route('/api/container/stats', methods=['GET'])
def getContainerStats():
    """
        Api method get container stats (cpu usage percent) by id if container running on this node
    """
    containerId = request.args.get('id')
    cpuLimit = float(request.args.get('cpuLimit'))
    stats = SwarmService.getContainerCpuStat(containerId, cpuLimit)
    if(stats == None):
        return "Container with id=%s not running on this node" %(containerId), 404
    return {'ContainerId':containerId, 'cpu': stats}

