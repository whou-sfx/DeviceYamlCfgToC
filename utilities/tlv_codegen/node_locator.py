"""TLV节点定位逻辑生成器。"""

from typing import Dict, List


class NodeLocator:
    """根据TLV类型生成节点定位代码片段。"""

    @staticmethod
    def get_locator(tlv_name: str) -> Dict[str, List[str]]:
        if tlv_name == "Device.Basic":
            return {
                "node_type": "device_basic_node_t",
                "pre_lines": ["device_basic_node_t *p = &sem->device_basic;"],
            }
        if tlv_name == "Device.PortCapability":
            return {
                "node_type": "device_port_capability_node_t",
                "pre_lines": ["device_port_capability_node_t *p = &sem->device_port_capability;"],
            }
        if tlv_name == "Port.Config":
            return {
                "node_type": "port_config_node_t",
                "pre_lines": [
                    "uint8_t port_id = v[0];",
                    "if (port_id >= MAX_PORTS) {",
                    "    return;",
                    "}",
                    "if (port_id + 1 > sem->port_count) {",
                    "    sem->port_count = port_id + 1;",
                    "}",
                    "port_config_node_t *p = &sem->port[port_id].config;",
                ],
            }
        if tlv_name == "LD.Config":
            return {
                "node_type": "ld_config_node_t",
                "pre_lines": [
                    "uint8_t port_id = v[0];",
                    "uint8_t ld_id = v[1];",
                    "uint8_t ld_type = v[2];",
                    "if (port_id >= MAX_PORTS) {",
                    "    return;",
                    "}",
                    "if (port_id + 1 > sem->port_count) {",
                    "    sem->port_count = port_id + 1;",
                    "}",
                    "ld_config_node_t *p = NULL;",
                    "if (ld_type == LD_TYPE_FM_LD) {",
                    "    if (0 >= MAX_FM_LD_PER_PORT) {",
                    "        return;",
                    "    }",
                    "    if (1 > sem->port[port_id].fm_ld_count) {",
                    "        sem->port[port_id].fm_ld_count = 1;",
                    "    }",
                    "    p = &sem->port[port_id].fm_ld[0].config;",
                    "} else {",
                    "    if (ld_id >= MAX_REGULAR_LD_PER_PORT) {",
                    "        return;",
                    "    }",
                    "    if (ld_id + 1 > sem->port[port_id].regular_ld_count) {",
                    "        sem->port[port_id].regular_ld_count = ld_id + 1;",
                    "    }",
                    "    p = &sem->port[port_id].regular_ld[ld_id].config;",
                    "}",
                    "if (p == NULL) {",
                    "    return;",
                    "}",
                ],
            }
        if tlv_name == "LD.Range":
            return {
                "node_type": "ld_range_node_t",
                "pre_lines": [
                    "uint8_t port_id = v[0];",
                    "uint8_t ld_id = v[1];",
                    "uint8_t range_id = v[2];",
                    "if (port_id >= MAX_PORTS) {",
                    "    return;",
                    "}",
                    "if (ld_id >= MAX_REGULAR_LD_PER_PORT) {",
                    "    return;",
                    "}",
                    "if (range_id >= MAX_RANGE_PER_REGULAR_LD) {",
                    "    return;",
                    "}",
                    "if (port_id + 1 > sem->port_count) {",
                    "    sem->port_count = port_id + 1;",
                    "}",
                    "if (ld_id + 1 > sem->port[port_id].regular_ld_count) {",
                    "    sem->port[port_id].regular_ld_count = ld_id + 1;",
                    "}",
                    "if (range_id + 1 > sem->port[port_id].regular_ld[ld_id].range_count) {",
                    "    sem->port[port_id].regular_ld[ld_id].range_count = range_id + 1;",
                    "}",
                    "ld_range_node_t *p = &sem->port[port_id].regular_ld[ld_id].range[range_id];",
                ],
            }
        raise KeyError(f"Unsupported TLV name for locator: {tlv_name}")


