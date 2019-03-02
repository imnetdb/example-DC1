#!/usr/bin/env python
#  Copyright 2019 Jeremy Schulman, nwkautomaniac@gmail.com
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.


import ipaddress

import querys


def _ensure_pool(clos, ip_pool):
    # see if we need to populate the loopback IP pool. We will check the DB collection count
    # to see if it is empty. if it is, then we'll populate the pool with loopback host IPs.

    if ip_pool.col.count() != 0:
        return

    net = ipaddress.ip_network(clos.config['ip-assignments']['fabric_ip_subnet'])
    print(f"Build fabric IP pool: {net} into /31 p2p segments")
    ip_pool.add_batch(net.subnets(new_prefix=31))


def _ensure_leaf_spine_ips(clos, ip_pool):
    cabling = clos.db.cabling.get_cabling(match={'role': 'leaf-spine'})

    # the first step in the process is to idempotent assign a /31 subnet to each cable segment.  we
    # will use the cable node _id value for the pool take key.

    # next, we want to orient the actual IP assignment so that the LEAF gets the FIRST ip
    # and the SPINE gets the SECOND ip.  This decision is completely "user defined", but we need to make A
    # decision so that the actual IP address values are idempotent assigned as well.  So for this
    # purpose we will need to get the device nodes and orient the data by names for lookup.

    devices = {dev['name']: dev for dev in clos.db.devices}

    for cable_item in cabling:

        take_key = cable_item['cable']['_id']
        taken = ip_pool.take(take_key)

        # the taken value is a /31 subnet, and we expand the host addresses into a list for
        # assignment into the database [0] = leaf interface, [1] = spine interface

        ip_list = list(ipaddress.ip_network(taken['value']))

        for if_node in cable_item['interfaces']:
            role = devices[if_node['device']]['role']

            # LEAF gets 1s ip, SPINE gets 2nd ip
            ip_addr = ip_list[0] if role == 'leaf' else ip_list[1]

            # ensure that this IP interface address exists in the global routing table DB.
            ip_node = clos.db.ip_if_addrs.ensure((clos.db.rt_global, f"{ip_addr}/31"))

            # ensure that this IP address has an assigned relationship to the interface node
            clos.db.ensure_edge((ip_node, 'ip_assigned', if_node))


def _ensure_leaf_pair_ips(clos, ip_pool):
    cabling = clos.db.cabling.get_cabling(match={'role': 'leaf-pair'})

    # the first step in the process is to idempotent assign a /31 subnet to each cable segment.  we
    # will use the cable node _id value for the pool take key.

    # next, we want to orient the actual IP assignment so that the RACK LEAF peer=0 gets the FIRST ip
    # and the peer=1 gets the SECOND ip.  This decision is completely "user defined", but we need to make A
    # decision so that the actual IP address values are idempotent assigned as well.  So for this
    # purpose we will need to get the device nodes and orient the data by names for lookup.

    devices = {dev['name']: dev for dev in clos.db.devices}

    for cable_item in cabling:

        take_key = cable_item['cable']['_id']
        taken = ip_pool.take({'cable': take_key})

        # the taken value is a /31 subnet, and we expand the host addresses into a list for
        # assignment into the database [0] = leaf interface, [1] = spine interface

        ip_list = list(ipaddress.ip_network(taken['value']))

        for if_node in cable_item['interfaces']:
            peer_id = devices[if_node['device']]['peer_id']

            # LEAF peer=0 gets first, peer=1 gets 2nd.
            ip_addr = ip_list[peer_id]

            # ensure that this IP interface address exists in the global routing table DB.
            ip_node = clos.db.ip_if_addrs.ensure((clos.db.rt_global, f"{ip_addr}/31"))

            # ensure that this IP address has an assigned relationship to the interface node
            clos.db.ensure_edge((ip_node, 'ip_assigned', if_node))


def _ensure_leaf_pair_lag_ips(clos, ip_pool):

    rack_lag_info = querys.get_rack_leaf_peer_lag(clos.db, "Lag0")

    for entry in rack_lag_info:

        rack_node = entry['rack']
        l0_lag = entry['devices'][0]['lag']
        l1_lag = entry['devices'][1]['lag']

        # use the rack node ID as the pool key for this p2p subnet
        taken = ip_pool.take({'leaf_pair': rack_node['_id']})

        # use the taken value to obtain the two ip address
        ip_list = list(ipaddress.ip_network(taken['value']))

        # ensure the IPInterface nodes exist

        ip0_node = clos.db.ip_if_addrs.ensure((clos.db.rt_global, f"{ip_list[0]}/31"))
        ip1_node = clos.db.ip_if_addrs.ensure((clos.db.rt_global, f"{ip_list[1]}/31"))

        # ensure they are bound to the LAG nodes
        clos.db.ensure_edge((ip0_node, 'ip_assigned', l0_lag))
        clos.db.ensure_edge((ip1_node, 'ip_assigned', l1_lag))


def ensure(clos):

    ip_pool = clos.db.fabric_ips

    _ensure_pool(clos, ip_pool)

    _ensure_leaf_spine_ips(clos, ip_pool)

    use_lag = "rack-dual-leaf-lag" in clos.config['architectural-decisions']
    if use_lag:
        _ensure_leaf_pair_lag_ips(clos, ip_pool)
    else:
        _ensure_leaf_pair_ips(clos, ip_pool)

    print("Fabric IP addresses assigned.")
