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


def ensure(clos):

    loopback_ips = clos.db.loopback_ips

    # see if we need to populate the loopback IP pool. We will check the DB collection count
    # to see if it is empty. if it is, then we'll populate the pool with loopback host IPs.

    if loopback_ips.col.count() == 0:
        lo_net = ipaddress.ip_network(clos.config['loopback_ip_subnet'])
        num_hosts = lo_net.num_addresses - 2
        print(f"Build loopback IP pool: {lo_net} num-hosts {num_hosts}")
        loopback_ips.add_batch(lo_net.hosts())

    # next assign a loopback IP for each device and store the value into the device node as
    # a field called "lo_inet".

    lo_field = 'lo_inet'

    for dev_node in clos.db.devices:

        # if already assigned, then continue to next device
        if lo_field in dev_node:
            continue

        # take an IP using the device name as the key; this will provide an idempotent assignment.
        # update the device node dict into the database

        taken = loopback_ips.take({'device': dev_node['name']})
        dev_node[lo_field] = taken['value']
        clos.db.devices.col.update(dev_node)
