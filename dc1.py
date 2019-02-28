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

import fire
from itertools import product
from operator import itemgetter

from bracket_expansion import expand
from imnetdb import IMNetDB
from imnetdb.devicestencils.arista.DCS7050X3 import (
    AristaDCS7050X3m48YC8,
    AristaDCS7050X3m32S)

TOPOLOGY = {
    'name': 'DC1',
    'spines': 2,
    'racks': 8
}


class MySpineStencil(AristaDCS7050X3m32S):
    """
    Define a SPINE switch providing 32x100g defined for all leaf-spine
    """
    ROLE = 'spine'

    SPEC_NAME = "32x100g"

    INTERFACES_SPEC = [
        (expand("Ethernet[1-32]"), dict(speed=100, role='leaf-spine'))
    ]


class MyLeafStencil(AristaDCS7050X3m48YC8):
    """
    Define a leaf switch providing 48x10g + 8x100g defined:
        - 48x10g for leaf-server links
        - 6x100g for leaf-spine links
        - 2x100g for leaf pair links
    """
    ROLE = 'leaf'

    SPEC_NAME = '48x10g+100g'

    INTERFACES_SPEC = [
        (expand("Ethernet[1-48]"),  dict(speed=10,  role='leaf-server')),
        (expand("Ethernet[49-54"),  dict(speed=100, role='leaf-spine')),
        (expand("Ethernet[55-56]"), dict(speed=100, role='pair'))
    ]


def get_db():
    return IMNetDB(db_name=TOPOLOGY['name'], password='admin123')


def define_name(role, num):
    return "{role}{num:02}".format(role=role, num=num)


def reset():
    print("Reset database: {} ... ".format(TOPOLOGY['name']), end='')
    get_db().reset_database()
    print("OK")


def ensure_rack(db, rack_num, stencil):
    rack_name = define_name('rack', rack_num)
    print("... {} ... ".format(rack_name), flush=True, end='')
    leaf1_num = (rack_num - 1) * 2 + 1
    leaf2_num = leaf1_num + 1

    group_node = db.device_groups.ensure(rack_name, rack_id=rack_num)

    l1_name = define_name(stencil.ROLE, leaf1_num)
    print(f"{l1_name} ... ", flush=True, end='')
    l1 = stencil(db, l1_name, role=stencil.ROLE, peer_id=0, rack_id=rack_num)

    l2_name = define_name(stencil.ROLE, leaf2_num)
    print(f"{l2_name} ... ", flush=True, end='')
    l2 = stencil(db, l2_name, role=stencil.ROLE, peer_id=1, rack_id=rack_num)

    db.device_groups.add_member(group_node, l1.nodes['device'])
    db.device_groups.add_member(group_node, l2.nodes['device'])
    print("OK", flush=True)


def ensure_devices():
    print("Ensure devices: {} ... ".format(TOPOLOGY['name']), flush=True)

    db = get_db()

    stencil = MySpineStencil

    # create the SPINE devices

    for spine_num in range(1, TOPOLOGY['spines'] + 1):
        device_name = define_name(stencil.ROLE, spine_num)
        print("... {} ... ".format(device_name), flush=True, end='')
        stencil(db, device_name, role=stencil.ROLE, spine_id=spine_num)
        print("OK")

    # create the LEAF devices in 2 per RACK formation

    for rack_num in range(1, TOPOLOGY['racks'] + 1):
        ensure_rack(db, rack_num, stencil=MyLeafStencil)

    print("OK")


def ensure_cabling():
    db = get_db()

    name = itemgetter('name')

    spine_devs = {
        name(dev): dev
        for dev in db.devices.col.find({'role': 'spine'})
    }

    leaf_devs = {
        name(dev): dev
        for dev in db.devices.col.find({'role': 'leaf'})
    }

    topo_spine_leaf = product(spine_devs, leaf_devs)

    import pdb
    pdb.set_trace()


if __name__ == "__main__":
    fire.Fire({
        'reset': reset,
        'devices': ensure_devices,
        'cabling': ensure_cabling
    })
