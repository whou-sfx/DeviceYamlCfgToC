"""TLV 名称与 C 标识符之间的通用转换工具。"""

import re


def camel_to_snake(name: str) -> str:
    """CamelCase -> snake_case, e.g. 'PortCapability' -> 'port_capability'."""
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name)
    return s.lower()


def tlv_name_to_snake(tlv_name: str) -> str:
    """TLV 点分名 -> snake_case, e.g. 'Device.PortCapability' -> 'device_port_capability'."""
    return "_".join(camel_to_snake(p) for p in tlv_name.split("."))


def node_struct_name(tlv_name: str) -> str:
    """TLV 名 -> C node 结构体类型名, e.g. 'Device.Basic' -> 'device_basic_node_t'."""
    return tlv_name_to_snake(tlv_name) + "_node_t"


def map_func_name(tlv_name: str) -> str:
    """TLV 名 -> C map 函数名, e.g. 'Device.Basic' -> 'map_device_basic'."""
    return "map_" + tlv_name_to_snake(tlv_name)


def tlv_type_enum_name(tlv_name: str) -> str:
    """TLV 名 -> C 枚举常量名, e.g. 'Device.PortCapability' -> 'TLV_TYPE_DEVICE_PORT_CAPABILITY'."""
    return "TLV_TYPE_" + tlv_name_to_snake(tlv_name).upper()
