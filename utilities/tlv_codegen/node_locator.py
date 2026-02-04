"""TLV节点定位逻辑生成器。"""

from typing import Dict, List


class NodeLocator:
    """根据TLV类型生成节点定位代码片段。"""
    
    def __init__(self, hierarchy: dict = None):
        self.hierarchy = hierarchy or {}
        self.device_tlvs = self.hierarchy.get('Device_Level_TLVs', [])

    def _get_device_field_name(self, tlv_name: str) -> str:
        """从 hierarchy 配置中获取 device_semantic_t 的字段名"""
        structures = self.hierarchy.get('Structures', [])
        for struct in structures:
            if struct['name'] == 'device_semantic_t':
                for field in struct['fields']:
                    if field.get('from_tlv') == tlv_name:
                        return field['name']
        # 如果找不到，返回默认转换
        return tlv_name.lower().replace(".", "_")

    def get_locator(self, tlv_name: str) -> Dict[str, List[str]]:
        # 动态判断是否为 Device 级 TLV
        if tlv_name in self.device_tlvs:
            node_type = self._node_struct_name(tlv_name)
            field_name = self._get_device_field_name(tlv_name)
            return {
                "node_type": node_type,
                "pre_lines": [f"{node_type} *p = &sem->{field_name};"],
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
    
    def _node_struct_name(self, tlv_name: str) -> str:
        """TLV名称转结构体类型名"""
        if tlv_name == "Device.PortCapability":
            return "device_port_capability_node_t"
        return tlv_name.lower().replace(".", "_") + "_node_t"


