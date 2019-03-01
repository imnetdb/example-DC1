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
from collections import defaultdict
from itertools import product

import fire


from clos_db import get_clos_db
import querys


def _ensure_leaf_spine_cabling(clos, spine_devs, leaf_devs):
    link_role = 'leaf-spine'
    db = clos.db

    for spine_name, leaf_name in product(spine_devs, leaf_devs):
        # get the leaf interface going to the spine device

        leaf_if_node = db.interfaces.pool_take(
            key={'device': leaf_name, 'spine': spine_name},
            match={'device': leaf_name, 'role': link_role})

        # get the spine interface going to the leaf device

        spine_if_node = db.interfaces.pool_take(
            key={'device': spine_name, 'leaf': leaf_name},
            match={'device': spine_name, 'role': link_role})

        # ensure a cabling node exists between these two interfaces
        clos.db.cabling.ensure((leaf_if_node, spine_if_node), role=link_role)


def _ensure_leaf_pair_cabling(clos, leaf_devs):
    link_role = 'leaf-pair'

    # organize leaf in pairs by their rack_id so that we can connect the leaf-pair
    # together of their leaf-pair interfaces

    racks = defaultdict(list)
    for leaf_name, leaf_dict in leaf_devs.items():
        racks[leaf_dict['rack_id']].append(leaf_name)

    for leaf_0, leaf_1 in racks.values():
        # get the leaf interface going to the spine device

        l0_if_node = clos.db.interfaces.pool_take(
            key={'device': leaf_0, 'leaf_peer': leaf_1},
            match={'device': leaf_0, 'role': link_role})

        l1_if_node = clos.db.interfaces.pool_take(
            key={'device': leaf_1, 'leaf_peer': leaf_0},
            match={'device': leaf_1, 'role': link_role})

        # ensure a cabling node exists between these two interfaces
        clos.db.cabling.ensure((l0_if_node, l1_if_node), role=link_role)


def ensure(clos):

    print(f"Ensure device cabling: {clos.name} ... ", flush=True, end='')

    spine_devs = {dev['name']: dev for dev in querys.get_devices(clos.db, role='spine')}
    leaf_devs = {dev['name']: dev for dev in querys.get_devices(clos.db, role='leaf')}

    _ensure_leaf_spine_cabling(clos, spine_devs, leaf_devs)
    _ensure_leaf_pair_cabling(clos, leaf_devs)

    print("OK", flush=True)
    return clos


def save():
    closdb = get_clos_db()
    cabling = closdb.cabling.get_cabling()
    ofile = f'{closdb.db_name}-cabling.json'
    json.dump(cabling, open(ofile, 'w+'), indent=3)
    print(f"Cabling written to {ofile}.")


if __name__ == '__main__':
    fire.Fire({
        'save': save
    })