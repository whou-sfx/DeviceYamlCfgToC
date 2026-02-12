"""生成语义结构头文件(tlv_semantic.h)。"""

from typing import Dict, List

from .type_mapper import CTypeMapper


class StructGenerator:
    def __init__(self, schemas: Dict[str, dict], hierarchy: dict = None):
        self.schemas = schemas
        self.hierarchy = hierarchy or {}

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

    def _emit_hierarchy_struct(self, struct_def: dict) -> List[str]:
        """根据 hierarchy 配置生成结构体定义"""
        lines = []
        struct_name = struct_def['name']
        
        # device_semantic_t 特殊处理：不生成 typedef，它在后面单独生成
        if struct_name == 'device_semantic_t':
            return []
        
        lines.append(f"typedef struct {{")
        
        for field in struct_def['fields']:
            field_name = field['name']
            field_type = field['type']
            
            if 'array' in field:
                lines.append(f"    {field_type} {field_name}[{field['array']}];")
            else:
                lines.append(f"    {field_type} {field_name};")
        
        lines.append(f"}} {struct_name};")
        lines.append("")
        
        return lines

    def _get_device_semantic_struct(self) -> dict:
        """获取 device_semantic_t 结构定义"""
        structures = self.hierarchy.get('Structures', [])
        for struct in structures:
            if struct['name'] == 'device_semantic_t':
                return struct
        return None

    def _emit_device_semantic_struct(self, struct_def: dict) -> List[str]:
        """生成 device_semantic_t 结构体"""
        lines = ["typedef struct {"]
        
        for field in struct_def['fields']:
            field_name = field['name']
            field_type = field['type']
            
            if 'array' in field:
                lines.append(f"    {field_type} {field_name}[{field['array']}];")
            else:
                lines.append(f"    {field_type} {field_name};")
        
        lines.append("} device_semantic_t;")
        lines.append("")
        
        return lines

    def _generate_macros(self) -> List[str]:
        """生成宏定义"""
        return [
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
        ]

    def generate(self) -> str:
        lines: List[str] = []
        
        # 生成文件头
        lines.extend([
            "/*",
            " * 自动生成文件，请勿手动编辑。",
            " */",
            "#ifndef __TLV_SEMANTIC_H__",
            "#define __TLV_SEMANTIC_H__",
            "",
            "#ifdef __SMOKE_TEST__",
            "#include <stdint.h>",
            "#include <string.h>",
            "",
            "#include \"../../cfg/device_config_header.h\"",
            "#else",
            "#include \"device_config_header.h\"",
            "#endif",
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
        ])

        # 生成各个TLV的node结构
        for tlv_name, schema in self.schemas.items():
            lines.extend(self._emit_node_struct(tlv_name, schema))

        # 从 hierarchy 配置生成层级结构
        if 'Structures' in self.hierarchy:
            for struct_def in self.hierarchy['Structures']:
                if struct_def['name'] != 'device_semantic_t':
                    lines.extend(self._emit_hierarchy_struct(struct_def))
            
            # 单独生成 device_semantic_t
            device_semantic = self._get_device_semantic_struct()
            if device_semantic:
                lines.extend(self._emit_device_semantic_struct(device_semantic))

        # 生成宏定义
        lines.extend(self._generate_macros())
        
        lines.extend([
            "#endif /* __TLV_SEMANTIC_H__ */",
            "",
        ])

        return "\n".join(lines)

