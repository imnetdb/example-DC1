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

import sys
import toml
import fire

from clos_db import get_clos_db


def ensure(closdb, config):

    vlan_nodes = {}

    # ensure that each VLAN exists with the defined set of fields. if the VLAN config
    # contains an IP address assignment, then pop that out and create a related IP address
    # interface node.

    for vlan_name, vlan_data in config['vlans'].items():

        ip_addr = vlan_data.pop('ip_addr', None)

        vlan_node = closdb.vlans.ensure(vlan_name, **vlan_data)
        vlan_nodes[vlan_name] = vlan_node

        if ip_addr:
            ip_node = closdb.ip_if_addrs.ensure((closdb.rt_global, ip_addr))
            closdb.ensure_edge((ip_node, 'ip_assigned', vlan_node))

    # ensure that each VLANGroup exists with the defined list of VLANs
    # the list of VLANs is defined in the config 'members' property.
    # we poop that out of the data fields before creating the actual
    # VG node

    for vg_name, vg_data in config['vlan-groups'].items():
        members = vg_data.pop('members')
        vg_node = closdb.vlan_groups.ensure(vg_name, **vg_data)

        # now ensure that each VLAN in the members list is in the VG

        for vlan_name in members:
            closdb.vlan_groups.add_member(vg_node, vlan_nodes[vlan_name])

    print("VLANs and groups created.")


class FireVlans(object):
    """ for CLI purposes ... """

    def __init__(self):
        self.closdb = get_clos_db()
        self.config = toml.load(open('config.toml'))

    def quiet(self):
        return ''

    def build(self):
        ensure(self.closdb, self.config)
        return self

    def save(self):
        return self

    def reset(self):
        for vg in self.closdb.vlan_groups:
            self.closdb.vlan_groups.remove(vg)

        for vlan in self.closdb.vlans:
            self.closdb.vlans.remove(vlan)
        print("VLANs and groups have been reset.")
        return self


if __name__ == '__main__':
    sys.argv.append('quiet')
    fire.Fire(FireVlans)