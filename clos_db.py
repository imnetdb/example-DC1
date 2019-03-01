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

import yaml
from imnetdb import IMNetDB

__all__ = ['TwoStageL3ClosDB']


class TwoStageL3ClosDB(IMNetDB):

    def ensure_database(self):
        super(TwoStageL3ClosDB, self).ensure_database()

        # manage the loopback IP pool.
        self.loopback_ips = self.resource_pool('RP_Loopback')

        # manage the fabric IP pool
        self.fabric_ips = self.resource_pool('RP_Fabric')

        # create a global routing-table for IP address management
        self.rt_global = self.routing_tables.ensure('global')

        self.asn_pools = {}
        self.asn_pools['leaf'] = self.resource_pool('RP_ASN_leaf', value_type=int)
        self.asn_pools['spine'] = self.resource_pool('RP_ASN_spine', value_type=int)


def get_clos_db():
    config = yaml.load(open('config.yml'))
    return TwoStageL3ClosDB(db_name=config['name'], password='admin123')
