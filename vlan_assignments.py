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


def _ensure_device_vlans(closdb, dev_name, if_vlans):

    dev_node = closdb.devices[dev_name]

    for if_name, vlans_provided in if_vlans.items():

        # obtain the IF node so we can bind the vlan item to it later

        if_node = closdb.interfaces[(dev_node, if_name)]

        # vlans could either be a str | list.

        vlan_list = [vlans_provided] if not isinstance(vlans_provided, list) else vlans_provided

        # the item in the list could either be a VLAN or a VLANGroup.

        for vlan in vlan_list:
            v_node = closdb.vlan_groups[vlan] or closdb.vlans[vlan]

            # ensure the VLAN assignment to this device interface
            closdb.ensure_edge((v_node, 'vlan_assigned', if_node))

        # now, let's use what was given to determine the interface mode "access" or "trunk".  Well
        # retrieve the actual vlan list for this interface, and assign the interface access IFF:
        #   - the "vlans" was originally a str and not a list
        #   - the number of actual vlans assigned is 1.  Need to check, since the str value could have been
        #     a group, and that group could have one or more vlans.

        vlan_list = closdb.vlans.get_attached_vlans(if_node)
        if_node['vlan_mode'] = 'access' if len(vlan_list) == 1 and isinstance(vlans_provided, str) else 'trunk'
        closdb.interfaces.col.update(if_node)

    print(f"VLANs assigned on device {dev_name}.")


def ensure(closdb, config):

    assignments = config['vlan-assignments']

    for dev_name, if_vlans in assignments.items():
        _ensure_device_vlans(closdb, dev_name, if_vlans)
