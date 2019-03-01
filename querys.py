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

_query_cabling = """
FOR cable in Cable
    FILTER cable.role == @cable_role
    LET if_nodes = (
        FOR if_node IN INBOUND cable cabled
            LET ip_addr = FIRST(
                FOR ip IN INBOUND if_node ip_assigned
                    RETURN ip
            )
            RETURN {
                interface: KEEP(if_node, ATTRIBUTES(if_node, true)),
                ip_addr: KEEP(ip_addr, ATTRIBUTES(ip_addr, true))
            }
    )
    return if_nodes
"""


def get_cabling(clos, role='leaf-spine'):
    return list(clos.query(_query_cabling, bind_vars={
        'cable_role': role
    }))
