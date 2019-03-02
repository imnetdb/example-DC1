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


def get_cabling(db, role='leaf-spine'):
    return list(db.query(_query_cabling, bind_vars={
        'cable_role': role
    }))


_query_device_role = """
FOR dev in Device
    FILTER dev.role == @role
    RETURN dev
"""


def get_devices(db, role):
    return list(db.query(_query_device_role, bind_vars={
        'role': role
    }))


_query_get_rack_groups = """
for group in DeviceGroup
    FILTER group.rack_id != null
    LET leaf_nodes = (
        FOR dev_node IN INBOUND group device_member
            FILTER dev_node.role == 'leaf'
            RETURN dev_node
    )
    return {
        rack: group,
        devices: leaf_nodes
    }
"""


def get_rack_groups(db):
    return list(db.query(_query_get_rack_groups))


_query_leaf_peer_lag = """
FOR dgroup in DeviceGroup
    FILTER dgroup.rack_id != null
    LET devices = (FOR device in inbound dgroup device_member
        LET lag = FIRST(for lag in 1..2 outbound device graph "master"
            FILTER IS_SAME_COLLECTION(lag, "LAG") and lag.name == @lag_name
            LIMIT 1
            return lag
        )
        SORT device.peer_id    
        return {device: device, lag: lag}
    )
    
    SORT dgroup.rack_id
    return {
        rack: dgroup,
        devices: devices
    }
"""


def get_rack_leaf_peer_lag(db, lag_name):
    """
    This query returns a list of LAGs oriented around a rack so that the caller can then query based on
    the LAG name.  The primary purpose for this is for rack leaf switches that have a LAG based set of
    peer interfaces.  The structure of each list item has the keys:

        - rack: the device group node (rack)
        - devices: the list[dict] of devices, each has the structure:
            - device: the device node
            - lag: the lag node

    The list is ASC sorted based on the rack_id and then by the leaf peer_id.

    Parameters
    ----------
    db : TwoStageL3ClosDB

    lag_name : str
        The LAG interface name, for example "Lag0"

    Returns
    -------
    list[dict]
        see above
    """
    return list(db.query(_query_leaf_peer_lag, bind_vars={
        'lag_name': lag_name
    }))
