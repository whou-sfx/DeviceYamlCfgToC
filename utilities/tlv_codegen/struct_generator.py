"""生成语义结构头文件(tlv_semantic.h)。"""

from typing import Dict, List

from .type_mapper import CTypeMapper


class StructGenerator:
    def __init__(self, schemas: Dict[str, dict]):
        self.schemas = schemas

    def _node_struct_name(self, tlv_name: str) -> str:
        if tlv_name == "Device.PortCapability":
            return "device_port_capability_node_t"
        return tlv_name.lower().replace(".", "_") + "_node_t"

    def _emit_node_struct(self, tlv_name: str, schema: dict) -> List[str]:
        struct_name = self._node_struct_name(tlv_name)
        fields = schema.get("fields", [])
        lines = [
            f"typedef struct {{",
            "    uint8_t present;",
            "    uint8_t dirty;",
            "    uint16_t tlv_value_offset;",
            "    uint16_t tlv_length;",
            "",
            "    /* 字段值 */",
        ]
        for field in fields:
            c_type = CTypeMapper.c_type(field["type"])
            name = field["name"]
            if field["type"] == "string":
                size = field.get("size", 32)
                lines.append(f"    {c_type} {name}[{size}];")
            else:
                lines.append(f"    {c_type} {name};")
        lines.append("")
        lines.append("    /* 字段描述符 */")
        for field in fields:
            name = field["name"]
            lines.append(f"    field_descriptor_t fd_{name};")
        lines.append(f"}} {struct_name};")
        lines.append("")
        return lines

    def generate(self) -> str:
        lines: List[str] = []
        device_basic_type = self._node_struct_name("Device.Basic")
        device_portcap_type = self._node_struct_name("Device.PortCapability")
        lines.extend(
            [
                "/*",
                " * 自动生成文件，请勿手动编辑。",
                " */",
                "#ifndef TLV_SEMANTIC_H",
                "#define TLV_SEMANTIC_H",
                "",
                "#include <stdint.h>",
                "#include <string.h>",
                "",
                "#include \"../../cfg/device_config_header.h\"",
                "",
                "typedef enum {",
                "    FIELD_TYPE_U8   = 0,",
                "    FIELD_TYPE_U16  = 1,",
                "    FIELD_TYPE_U32  = 2,",
                "    FIELD_TYPE_U64  = 3,",
                "    FIELD_TYPE_BOOL = 0,",
                "} field_type_t;",
                "",
                "static inline uint8_t field_type_size(field_type_t type)",
                "{",
                "    static const uint8_t sizes[] = {1, 2, 4, 8};",
                "    return (type <= FIELD_TYPE_U64) ? sizes[type] : 0;",
                "}",
                "",
                "typedef struct {",
                "    uint16_t offset;",
                "    field_type_t type;",
                "    uint8_t present;",
                "} field_descriptor_t;",
                "",
            ]
        )

        for tlv_name, schema in self.schemas.items():
            lines.extend(self._emit_node_struct(tlv_name, schema))

        lines.extend(
            [
                "typedef struct {",
                "    ld_config_node_t config;",
                "    ld_range_node_t range[MAX_RANGE_PER_REGULAR_LD];",
                "    uint8_t range_count;",
                "} regular_ld_t;",
                "",
                "typedef struct {",
                "    ld_config_node_t config;",
                "} fm_ld_t;",
                "",
                "typedef struct {",
                "    port_config_node_t config;",
                "    regular_ld_t regular_ld[MAX_REGULAR_LD_PER_PORT];",
                "    uint8_t regular_ld_count;",
                "    fm_ld_t fm_ld[MAX_FM_LD_PER_PORT];",
                "    uint8_t fm_ld_count;",
                "} port_t;",
                "",
                "typedef struct {",
                "    uint8_t *tlv_binary;",
                "    uint16_t tlv_binary_length;",
                "    uint8_t global_dirty;",
                "",
                f"    {device_basic_type} device_basic;",
                f"    {device_portcap_type} device_port_capability;",
                "",
                "    port_t port[MAX_PORTS];",
                "    uint8_t port_count;",
                "",
                "    uint8_t parse_success;",
                "    uint16_t total_tlv_count;",
                "} device_semantic_t;",
                "",
                "#define SEMANTIC_INIT(sem) do { \\",
                "    memset((sem), 0, sizeof(device_semantic_t)); \\",
                "} while (0)",
                "",
                "#define SEMANTIC_MARK_DIRTY(sem) do { \\",
                "    (sem)->global_dirty = 1; \\",
                "} while (0)",
                "",
                "#define SEMANTIC_CLEAR_DIRTY(sem) do { \\",
                "    (sem)->global_dirty = 0; \\",
                "} while (0)",
                "",
                "#define SEMANTIC_NEEDS_FLUSH(sem) ((sem)->global_dirty)",
                "",
                "#define HAS_DEVICE_BASIC(sem) ((sem)->device_basic.present)",
                "",
                "#define HAS_PORT(sem, port_id) \\",
                "    ((port_id) < MAX_PORTS && (sem)->port[port_id].config.present)",
                "",
                "#define HAS_REGULAR_LD(sem, port_id, ld_id) \\",
                "    (HAS_PORT(sem, port_id) && \\",
                "     (ld_id) < MAX_REGULAR_LD_PER_PORT && \\",
                "     (sem)->port[port_id].regular_ld[ld_id].config.present)",
                "",
                "#define HAS_RANGE(sem, port_id, ld_id, range_id) \\",
                "    (HAS_REGULAR_LD(sem, port_id, ld_id) && \\",
                "     (range_id) < MAX_RANGE_PER_REGULAR_LD && \\",
                "     (sem)->port[port_id].regular_ld[ld_id].range[range_id].present)",
                "",
                "#define HAS_FM_LD(sem, port_id, fm_id) \\",
                "    (HAS_PORT(sem, port_id) && \\",
                "     (fm_id) < MAX_FM_LD_PER_PORT && \\",
                "     (sem)->port[port_id].fm_ld[fm_id].config.present)",
                "",
                "#define MARK_NODE_DIRTY(node) do { \\",
                "    (node)->dirty = 1; \\",
                "} while (0)",
                "",
                "#define CLEAR_NODE_DIRTY(node) do { \\",
                "    (node)->dirty = 0; \\",
                "} while (0)",
                "",
                "#endif /* TLV_SEMANTIC_H */",
                "",
            ]
        )

        return "\n".join(lines)

