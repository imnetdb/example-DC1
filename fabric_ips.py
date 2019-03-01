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

import json
import fire
import ipaddress
import csv
from clos_db import get_clos_db

import querys


def _ensure_pool(clos, ip_pool):
    # see if we need to populate the loopback IP pool. We will check the DB collection count
    # to see if it is empty. if it is, then we'll populate the pool with loopback host IPs.

    if ip_pool.col.count() != 0:
        return

    net = ipaddress.ip_network(clos.config['fabric_ip_subnet'])
    print(f"Build fabric IP pool: {net} into /31 p2p segments")
    ip_pool.add_batch(net.subnets(new_prefix=31))


def ensure(clos):

    ip_pool = clos.db.fabric_ips

    _ensure_pool(clos, ip_pool)

    # obtain the cabling information for the 'leaf-spine' role only.  each item in this
    # list has a 'cable' node and 'interfaces' list.

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


def save_json():
    clos = get_clos_db()
    assigned = clos.routing_tables.get_interface_members(clos.rt_global)
    ofile = f'{clos.db_name}-fabric-ips.json'
    json.dump(assigned, open(ofile, 'w+'), indent=3)
    print(f"Fabric IP dataset saved to {ofile}")


def save_csv():
    clos = get_clos_db()
    cabling = querys.get_cabling(clos)

    def getdata(item):
        ifd = item['interface']
        return ifd['device'], ifd['name'], item['ip_addr']['name']

    with open(f'{clos.db_name}-fabric-cabling.csv', 'w+') as ofile:
        csv_wr = csv.writer(ofile)

        for each in cabling:
            csv_wr.writerow(getdata(each[0]) + getdata(each[1]))

    print(f"Created {ofile.name}")


if __name__ == '__main__':
    fire.Fire({
        'save': save_csv,
        'save-json': save_json
    })