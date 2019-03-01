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

from bracket_expansion import expand

from imnetdb.devicestencils.arista.DCS7050X3 import (
    AristaDCS7050X3m48YC8,
    AristaDCS7050X3m32S)


class MySpineStencil(AristaDCS7050X3m32S):
    """
    Define a SPINE switch providing 32x100g defined for all leaf-spine
    """
    ROLE = 'spine'

    SPEC_NAME = "32x100g"

    INTERFACES_SPEC = [
        (("Loopback0", ), dict(role='loopback')),
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
        (("Loopback0", ), dict(role='loopback')),
        (expand("Ethernet[1-48]"),  dict(speed=10,  role='leaf-server')),
        (expand("Ethernet[49-54]"),  dict(speed=100, role='leaf-spine')),
        (expand("Ethernet[55-56]"), dict(speed=100, role='leaf-pair'))
    ]