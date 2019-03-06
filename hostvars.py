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
import json

from imnetdb.extracto.device import extracto_device

from clos_db import get_clos_db


def save(name, db=None):
    db = db or get_clos_db()
    hostvars = extracto_device(db, name)
    with open(f"{db.db_name}-{name}-hostvars.json", "w+") as ofile:
        json.dump(hostvars, ofile, indent=2)

    print(f"Created device hostvars: {ofile.name}.")


if __name__ == '__main__':
    fire.Fire({'save': save})