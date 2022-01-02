![hub.docker.com](https://img.shields.io/docker/pulls/eluki/swarm-service-autoscaler.svg)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/amest/swarm-autoscaler)

# Swarm Service Autoscaler

## Description

The project is an application that implements the ability to dynamically change the number of service instances under high load. The application receives all services that have the `swarm.autoscaler` label enabled, calculates the average value of the CPU utilization and, based on this, either increases the number of instances or decreases it.

Currently, only the CPU is used for autoscaling in the project. By default, if the CPU load reaches 85%, the service will scale, if it reaches 25%, it will be scaled down.   
But the minimum and maximum values ​​of CPU utilization can be changed through environment variables.

Also, for each service, you can set the maximum and minimum number of replicas to prevent a situation with an uncontrolled increase in the number of replicas (or too much decrease)

## Configuration

Service configure wia environment variable

* `MIN_PERCENTAGE` - minimum service cpu utilization value in percent (0.0-100.0) for decrease service
* `MAX_PERCENTAGE` - maximum service cpu utilization value in percent (0.0-100.0) for increase service
* `DISCOVERY_DNSNAME` - swarm service name for in stack communication
* `CHECK_INTERVAL` - interval between checks
* `DRY_RUN` - noop mode for check service functional without enable inc or dec service replicas count


## Usage
...
