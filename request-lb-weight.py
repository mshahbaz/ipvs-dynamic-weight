#!/usr/bin/env python

import os, sys, memcache, time, psutil

# If the calculation of the load AND the weighting/aing
# of the load data is at the same interval (1 minute) then we
# will see a lot of jerkiness. So we take the 5 minute average.
# This means servers get lowered in priority more slowly.
server_id = _SERVER_ID_

if len(sys.argv) < 4:
    raise Exception('You must pass the hostname and port of your memcached server, '
                    'along with a timeout value for probing the state, debug, metric, and ...')

mc = memcache.Client([sys.argv[1]], )

timeout = float(sys.argv[2])
debug = sys.argv[3]
metric = sys.argv[4]

if metric == 'loadavg':
    max_load = int(sys.argv[5])

last_total_usage = 0
last_idle_usage = 0

while True:
    weight = 1

    if metric == 'loadavg':
        load = os.getloadavg()[1]

        # Weight must range from 1 - 256
        if load < 0.001:
            load = 0.001
        if load > max_load:
            load = max_load

        weight = int(((255 / max_load) * ((max_load + 0.001) - load)) + 1)
    else:
        usage = psutil.cpu_times()
        idle_usage = usage.idle
        total_usage = usage.idle + usage.user + usage.system

        weight = int(100.0 * (idle_usage - last_idle_usage) / (total_usage - last_total_usage))

        if weight == 0: weight = 1

        last_idle_usage = idle_usage
        last_total_usage = total_usage

    if debug == 'True':
        print 'Declaring weight of %s for %s for %ss' % (weight, server_id, 60 * 2)
    mc.set('server-weight-%s' % server_id, weight, time=60 * 2)  # Set a two minute expiry
    time.sleep(timeout)
