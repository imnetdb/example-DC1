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

from stencils import MyLeafStencil, MySpineStencil


def define_name(role, num):
    return "{role}{num:02}".format(role=role, num=num)


def ensure_rack(clos, rack_num, stencil):
    db = clos.db

    rack_name = define_name('rack', rack_num)
    print("... {} ... ".format(rack_name), flush=True, end='')
    leaf1_num = (rack_num - 1) * 2 + 1
    leaf2_num = leaf1_num + 1

    # create a DeviceGroup that represents the rack; that is used to identify the two leaf devices
    # that form a rack pair

    group_node = db.device_groups.ensure(rack_name, rack_id=rack_num)

    # LEAF-1 in the rack, the stencil create returns a dictionary of node information
    # keys=('device', 'interfaces').  Only using the device for now since we need to when forming the
    # rack group members

    l1_name = define_name(stencil.ROLE, leaf1_num)
    print(f"{l1_name} ... ", flush=True, end='')
    l1 = stencil(db, l1_name, role=stencil.ROLE, leaf_id=leaf1_num, peer_id=0, rack_id=rack_num)

    # LEAF-2 in the rack

    l2_name = define_name(stencil.ROLE, leaf2_num)
    print(f"{l2_name} ... ", flush=True, end='')
    l2 = stencil(db, l2_name, role=stencil.ROLE, leaf_id=leaf2_num, peer_id=1, rack_id=rack_num)

    # add both leaf devices to the rack group

    db.device_groups.add_member(group_node, l1.nodes['device'])
    db.device_groups.add_member(group_node, l2.nodes['device'])

    print("OK", flush=True)


def ensure(clos):
    print("Ensure devices: {} ... ".format(clos.name), flush=True)

    topo_cfg = clos.config['topology']

    db = clos.db

    stencil = MySpineStencil

    # create the SPINE devices

    for spine_num in range(1, topo_cfg['spines'] + 1):
        device_name = define_name(stencil.ROLE, spine_num)
        print("... {} ... ".format(device_name), flush=True, end='')
        stencil(db, device_name, role=stencil.ROLE, spine_id=spine_num)
        print("OK")

    # create the LEAF devices in 2 per RACK formation

    for rack_num in range(1, topo_cfg['racks'] + 1):
        ensure_rack(clos, rack_num, stencil=MyLeafStencil)

    print("Devices in database OK", flush=True)
