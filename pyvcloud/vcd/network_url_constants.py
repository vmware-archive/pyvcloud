# VMware vCloud Director Python SDK
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

FIREWALL_URL_TEMPLATE = "/firewall/config"
FIREWALL_RULES_URL_TEMPLATE = "/firewall/config/rules"
DHCP_URL_TEMPLATE = "/dhcp/config"
DHCP_POOLS = "/ippools"
DHCP_POOLS_URL_TEMPLATE = "/dhcp/config" + DHCP_POOLS
DHCP_POOL_URL_TEMPLATE = DHCP_POOLS_URL_TEMPLATE + "/{0}"
NAT_URL_TEMPLATE = "/nat/config"
NAT_RULES = "/rules"
NAT_RULES_URL_TEMPLATE = "/nat/config" + NAT_RULES
NAT_RULE_URL_TEMPLATE = NAT_RULES_URL_TEMPLATE + "/{0}"
STATIC_ROUTE_URL_TEMPLATE = "/routing/config/static"
