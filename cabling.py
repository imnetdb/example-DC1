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

import csv
from collections import defaultdict
from itertools import product

import fire


from clos_db import get_clos_db
import querys


def _ensure_leaf_spine_cabling(clos, spine_devs, leaf_devs):
    link_role = 'leaf-spine'
    db = clos.db

    leaf_spine_if_count = clos.config['topology']['leaf-spine-interface-count']

    for spine_name, leaf_name in product(spine_devs, leaf_devs):
        # get the leaf interface going to the spine device

        for if_id in range(leaf_spine_if_count):
            leaf_if_node = db.interfaces.pool_take(
                key={'device': leaf_name, 'spine': spine_name, 'if_id': if_id},
                match={'device': leaf_name, 'role': link_role})

            # get the spine interface going to the leaf device

            spine_if_node = db.interfaces.pool_take(
                key={'device': spine_name, 'leaf': leaf_name, 'if_id': if_id},
                match={'device': spine_name, 'role': link_role})

            # ensure a cabling node exists between these two interfaces
            clos.db.cabling.ensure((leaf_if_node, spine_if_node), role=link_role)


def _ensure_lag(closdb, dev_name, lag_name, if_node_list, **fields):
    dev_node = closdb.devices[dev_name]
    lag_node = closdb.lags.ensure((dev_node, lag_name), **fields)

    for if_node in if_node_list:
        closdb.lags.add_member(lag_node, if_node)


def _ensure_leaf_pair_cabling(clos, leaf_devs):
    link_role = 'leaf-pair'

    use_lag = "rack-dual-leaf-lag" in clos.config['architectural-decisions']
    leaf_pair_if_count = clos.config['topology']['leaf-pair-interface-count']

    # organize leaf in pairs by their rack_id so that we can connect the leaf-pair
    # together of their leaf-pair interfaces

    racks = defaultdict(list)
    for leaf_name, leaf_dict in leaf_devs.items():
        racks[leaf_dict['rack_id']].append(leaf_name)

    # we need to keep track of interfaces as they are allocated on a per leaf switch
    # basis because we may need to create a LAG between these interfaces based on the
    # `use_lag` option.

    leaf_if_nodes = defaultdict(list)

    for leaf_0, leaf_1 in racks.values():

        for if_id in range(leaf_pair_if_count):

            l0_if_node = clos.db.interfaces.pool_take(
                key={'device': leaf_0, 'leaf_peer': leaf_1, 'if_id': if_id},
                match={'device': leaf_0, 'role': link_role})

            leaf_if_nodes[leaf_0].append(l0_if_node)

            l1_if_node = clos.db.interfaces.pool_take(
                key={'device': leaf_1, 'leaf_peer': leaf_0, 'if_id': if_id},
                match={'device': leaf_1, 'role': link_role})

            leaf_if_nodes[leaf_1].append(l1_if_node)

            # ensure a cabling node exists between these two interfaces
            clos.db.cabling.ensure((l0_if_node, l1_if_node), role=link_role)

        if use_lag:
            _ensure_lag(clos.db, leaf_0, "Lag0", leaf_if_nodes[leaf_0], role=link_role)
            _ensure_lag(clos.db, leaf_1, "Lag0", leaf_if_nodes[leaf_1], role=link_role)


def ensure(clos):

    print(f"Ensure device cabling: {clos.name} ... ", flush=True, end='')

    spine_devs = {dev['name']: dev for dev in querys.get_devices(clos.db, role='spine')}
    leaf_devs = {dev['name']: dev for dev in querys.get_devices(clos.db, role='leaf')}

    _ensure_leaf_spine_cabling(clos, spine_devs, leaf_devs)
    _ensure_leaf_pair_cabling(clos, leaf_devs)

    print("OK", flush=True)
    return clos


def save(role='leaf-spine'):
    clos = get_clos_db()
    cabling = querys.get_cabling(clos, role=role)

    def getdata(item):
        ifd = item['interface']
        return ifd['device'], ifd['name'], (item.get('ip_addr') or {}).get('name', 'n/a')

    with open(f'{clos.db_name}-cabling-{role}.csv', 'w+') as ofile:
        csv_wr = csv.writer(ofile)

        for each in cabling:
            csv_wr.writerow(getdata(each[0]) + getdata(each[1]))

    print(f"Created {ofile.name}")


if __name__ == '__main__':
    fire.Fire({
        'save': save
    })