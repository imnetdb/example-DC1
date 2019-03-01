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


def _populate_pools(clos):
    spine_range = clos.config['asn_spine_range']
    leaf_range = clos.config['asn_leaf_range']

    clos.db.asn_pools['leaf'].add_batch(range(leaf_range[0], leaf_range[1] + 1))
    clos.db.asn_pools['spine'].add_batch(range(spine_range[0], spine_range[1] + 1))

    print("Create ASN pools.")


def _ensure_spine_asn_values(clos):
    asn_pool = clos.db.asn_pools['spine']
    dev_col = clos.db.devices.col

    for dev in querys.get_devices(clos.db, role='spine'):
        taken = asn_pool.take({'spine': dev['name']})
        dev['asn'] = taken['value']
        dev_col.update(dev)

    print("Spine ASN values assigned.")


def _ensure_leaf_asn_values(clos):
    asn_pool = clos.db.asn_pools['leaf']
    dev_col = clos.db.devices.col

    rack_groups = querys.get_rack_groups(clos.db)
    for rack in rack_groups:
        taken = asn_pool.take({'rack': rack['rack']['rack_id']})
        rack_asn = taken['value']
        for leaf_dev in rack['devices']:
            leaf_dev['asn'] = rack_asn
            dev_col.update(leaf_dev)

    print("Leaf ASN values assigned")


def ensure(clos):

    if clos.db.asn_pools['leaf'].col.count() == 0:
        _populate_pools(clos)

    _ensure_spine_asn_values(clos)
    _ensure_leaf_asn_values(clos)
