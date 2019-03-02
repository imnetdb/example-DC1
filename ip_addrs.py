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
import fire
import clos_db


def save():
    db = clos_db.get_clos_db()

    def assignedstr(this):
        return ','.join(f"{k}={v}" for k, v in this.items() if k[0] != '_')

    def row(item):
        return [item['ip']['name'], item['collection'], assignedstr(item['assigned'])]

    ip_info = db.routing_tables.get_interface_members(db.rt_global)

    with open(f"{db.db_name}-ip-interfaces.csv", "w+") as ofile:
        csv_wr = csv.writer(ofile)
        csv_wr.writerows(map(row, ip_info))

    print(f"IP interface assignments written to {ofile.name}.")


if __name__ == '__main__':
    fire.Fire()