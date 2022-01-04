[![Autoscaller Build](https://github.com/AMEST/swarm-autoscaler/actions/workflows/main.yml/badge.svg?branch=master)](https://github.com/AMEST/swarm-autoscaler/actions/workflows/main.yml)
![hub.docker.com](https://img.shields.io/docker/pulls/eluki/swarm-service-autoscaler.svg)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/amest/swarm-autoscaler)
![GitHub](https://img.shields.io/github/license/amest/swarm-autoscaler)

# Swarm Service Autoscaler

## Links  
* **[Docker hub](https://hub.docker.com/r/eluki/swarm-service-autoscaler)**

***

## Description

The project is an application that implements the ability to dynamically change the number of service instances under high load. The application receives all services that have the `swarm.autoscaler` label enabled, calculates the average value of the CPU utilization and, based on this, either increases the number of instances or decreases it.

Currently, only the CPU is used for autoscaling in the project. By default, if the CPU load reaches 85%, the service will scale, if it reaches 25%, it will be scaled down.   
But the minimum and maximum values ​​of CPU utilization can be changed through environment variables.

Also, for each service, you can set the maximum and minimum number of replicas to prevent a situation with an uncontrolled increase in the number of replicas (or too much decrease)

## Usage

1. Deploy Swarm Autoscaler using [`swarm-deploy.yml`](swarm-deploy.yml) from this repository
2. Add label `swarm.autoscaler=true` for services you want to autoscale. 

```yml
deploy:
  labels:
    - "swarm.autoscaler=true"
```

For better resource management, it is recommended to add resource constraints to your service. Then it will definitely not eat more resources than necessary, and auto-scaling will work much better and will save resources in idle time.

```yml
deploy:
  resources:
    limits:
      cpus: '0.50'
```

## Configuration

### Swarm Autoscaler configuration

_**The application is configured through environment variables**_

| Setting                     | Default Value      | Description                                                                             |
| --------------------------- | ------------------ | --------------------------------------------------------------------------------------- |
| `AUTOSCALER_MIN_PERCENTAGE` | 25.0               | minimum service cpu utilization value in percent (0.0-100.0) for decrease service       |
| `AUTOSCALER_MAX_PERCENTAGE` | 85.0               | maximum service cpu utilization value in percent (0.0-100.0) for increase service       |
| `AUTOSCALER_DNSNAME`        | `tasks.autoscaler` | swarm service name for in stack communication                                           |
| `AUTOSCALER_INTERVAL`       | 300                | interval between checks in seconds                                                      |
| `AUTOSCALER_DRYRUN`         | false              | noop mode for check service functional without enable inc or dec service replicas count |

### Services configuration

_**Services in docker swarm are configured via labels**_

| Setting                | Value   | Description                                                                                                                |
| ---------------------- | ------- | -------------------------------------------------------------------------------------------------------------------------- |
| `swarm.autoscaler`     | `true`  | Required. This enables autoscaling for a service. Anything other than `true` will not enable it                            |
| `swarm.autoscaler.min` | Integer | Optional. This is the minimum number of replicas wanted for a service. The autoscaler will not downscale below this number |
| `swarm.autoscaler.max` | Integer | Optional. This is the maximum number of replicas wanted for a service. The autoscaler will not scale up past this number   |
