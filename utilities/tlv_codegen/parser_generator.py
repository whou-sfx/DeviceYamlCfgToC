"""生成解析器头文件与实现文件(tlv_parser.h/.c)。"""

from typing import Dict, List

from .field_reader import FieldReader
from .node_locator import NodeLocator
from .type_mapper import CTypeMapper


class ParserGenerator:
    def __init__(self, schemas: Dict[str, dict], hierarchy: dict = None):
        self.schemas = schemas
        self.hierarchy = hierarchy or {}
        self.node_locator = NodeLocator(hierarchy)

    def _map_func_name(self, tlv_name: str) -> str:
        return "map_" + tlv_name.lower().replace(".", "_")

    def generate_header(self) -> str:
        lines: List[str] = [
            "/*",
            " * 自动生成文件，请勿手动编辑。",
            " */",
            "#ifndef TLV_PARSER_H",
            "#define TLV_PARSER_H",
            "",
            "#include <stdint.h>",
            "",
            "#include \"tlv_semantic.h\"",
            "#include \"../../cfg/device_config_header.h\"",
            "",
            "#define MAX_TLV_COUNT 128",
            "",
            "typedef struct {",
            "    uint8_t type;",
            "    uint8_t enable;",
            "    uint16_t length;",
            "    uint16_t value_offset;",
            "    uint16_t tlv_offset;",
            "} tlv_index_t;",
            "",
            "int parse_tlv_binary(device_semantic_t *sem, uint8_t *binary, uint16_t length);",
            "int update_tlv_header(device_semantic_t *sem);",
            "uint32_t calculate_crc32(const uint8_t *data, uint32_t length);",
            "int semantic_write_field(device_semantic_t *sem, const field_descriptor_t *fd, uint64_t value);",
            "int semantic_read_field(const device_semantic_t *sem, const field_descriptor_t *fd, uint64_t *value);",
            "",
            "#endif /* TLV_PARSER_H */",
            "",
        ]
        return "\n".join(lines)

    def _emit_field_read_block(self, fields: list) -> List[str]:
        lines: List[str] = []
        offset = 0
        for field in fields:
            name = field["name"]
            ftype = field["type"]
            size = CTypeMapper.size(ftype)
            if ftype == "string":
                max_len = field.get("size", 32)
                lines.extend(
                    [
                        f"if (len >= {offset + max_len}) {{",
                        f"    memcpy(p->{name}, v + {offset}, {max_len});",
                        f"    p->fd_{name} = (field_descriptor_t){{ .offset = base + {offset}, .type = FIELD_TYPE_U8, .present = 1 }};",
                        "} else {",
                        f"    memset(p->{name}, 0, {max_len});",
                        f"    p->fd_{name} = (field_descriptor_t){{ .offset = base + {offset}, .type = FIELD_TYPE_U8, .present = 0 }};",
                        "}",
                    ]
                )
                offset += max_len
                continue
            lines.append(f"if (len >= {offset + size}) {{")
            lines.append(f"    {FieldReader.generate_assign_statement(name, ftype, offset)}")
            lines.append(
                f"    {FieldReader.field_descriptor_init(name, ftype, offset)}"
            )
            lines.append("} else {")
            lines.append(
                f"    p->fd_{name} = (field_descriptor_t){{ .offset = base + {offset}, .type = {CTypeMapper.field_type(ftype)}, .present = 0 }};"
            )
            lines.append("}")
            offset += size
        return lines

    def _emit_map_function(self, tlv_name: str, schema: dict) -> List[str]:
        func_name = self._map_func_name(tlv_name)
        locator = self.node_locator.get_locator(tlv_name)
        fields = schema.get("fields", [])
        lines: List[str] = [
            f"static void {func_name}(const uint8_t *buf, const tlv_index_t *idx, device_semantic_t *sem)",
            "{",
            "    if (idx->enable != TLV_ENABLE_ENABLED) {",
            "        return;",
            "    }",
            "    const uint8_t *v = buf + idx->value_offset;",
            "    uint16_t base = idx->value_offset;",
            "    uint16_t len = idx->length;",
            "",
        ]
        for line in locator["pre_lines"]:
            lines.append(f"    {line}")
        lines.extend(
            [
                "    p->present = 1;",
                "    p->dirty = 0;",
                "    p->tlv_value_offset = idx->value_offset;",
                "    p->tlv_length = idx->length;",
                "",
            ]
        )
        for line in self._emit_field_read_block(fields):
            lines.append(f"    {line}")
        lines.append("}")
        lines.append("")
        return lines

    def generate_source(self) -> str:
        lines: List[str] = [
            "/*",
            " * 自动生成文件，请勿手动编辑。",
            " */",
            "#include <string.h>",
            "",
            "#include \"tlv_parser.h\"",
            "",
            "static int build_tlv_index(const uint8_t *binary, uint16_t length,",
            "                           tlv_index_t *index, uint16_t *count, uint16_t max_count)",
            "{",
            "    uint16_t offset = sizeof(binary_tlv_header_t);",
            "    uint16_t idx = 0;",
            "    while (offset + sizeof(tlv_entry_t) <= length) {",
            "        const tlv_entry_t *entry = (const tlv_entry_t *)(binary + offset);",
            "        uint16_t value_offset = offset + sizeof(tlv_entry_t);",
            "        uint16_t value_length = entry->length;",
            "        if (value_offset + value_length > length) {",
            "            break;",
            "        }",
            "        if (idx < max_count) {",
            "            index[idx].type = entry->type;",
            "            index[idx].enable = entry->enable;",
            "            index[idx].length = value_length;",
            "            index[idx].value_offset = value_offset;",
            "            index[idx].tlv_offset = offset;",
            "            idx++;",
            "        }",
            "        offset = value_offset + value_length;",
            "    }",
            "    *count = idx;",
            "    return 0;",
            "}",
            "",
        ]

        for tlv_name, schema in self.schemas.items():
            lines.extend(self._emit_map_function(tlv_name, schema))

        lines.extend(
            [
                "int parse_tlv_binary(device_semantic_t *sem, uint8_t *binary, uint16_t length)",
                "{",
                "    if (!sem || !binary) {",
                "        return -1;",
                "    }",
                "    if (length < sizeof(binary_tlv_header_t)) {",
                "        return -1;",
                "    }",
                "",
                "    SEMANTIC_INIT(sem);",
                "    sem->tlv_binary = binary;",
                "    sem->tlv_binary_length = length;",
                "",
                "    tlv_index_t index[MAX_TLV_COUNT];",
                "    uint16_t index_count = 0;",
                "    build_tlv_index(binary, length, index, &index_count, MAX_TLV_COUNT);",
                "",
                "    for (uint16_t i = 0; i < index_count; i++) {",
                "        switch (index[i].type) {",
                "            case TLV_TYPE_DEVICE_BASIC:",
                f"                {self._map_func_name('Device.Basic')}(binary, &index[i], sem);",
                "                break;",
                "            case TLV_TYPE_DEVICE_PORT_CAPABILITY:",
                f"                {self._map_func_name('Device.PortCapability')}(binary, &index[i], sem);",
                "                break;",
                "            case TLV_TYPE_PORT_CONFIG:",
                f"                {self._map_func_name('Port.Config')}(binary, &index[i], sem);",
                "                break;",
                "            case TLV_TYPE_LD_CONFIG:",
                f"                {self._map_func_name('LD.Config')}(binary, &index[i], sem);",
                "                break;",
                "            case TLV_TYPE_LD_RANGE:",
                f"                {self._map_func_name('LD.Range')}(binary, &index[i], sem);",
                "                break;",
                "            default:",
                "                break;",
                "        }",
                "    }",
                "",
                "    sem->parse_success = 1;",
                "    sem->total_tlv_count = index_count;",
                "    return 0;",
                "}",
                "",
                "uint32_t calculate_crc32(const uint8_t *data, uint32_t length)",
                "{",
                "    uint32_t crc = 0xFFFFFFFFu;",
                "    for (uint32_t i = 0; i < length; i++) {",
                "        crc ^= data[i];",
                "        for (uint8_t b = 0; b < 8; b++) {",
                "            if (crc & 1) {",
                "                crc = (crc >> 1) ^ 0xEDB88320u;",
                "            } else {",
                "                crc >>= 1;",
                "            }",
                "        }",
                "    }",
                "    return ~crc;",
                "}",
                "",
                "int update_tlv_header(device_semantic_t *sem)",
                "{",
                "    if (!sem || !sem->tlv_binary) {",
                "        return -1;",
                "    }",
                "    if (!sem->global_dirty) {",
                "        return 0;",
                "    }",
                "    if (sem->tlv_binary_length < sizeof(binary_tlv_header_t)) {",
                "        return -1;",
                "    }",
                "",
                "    binary_tlv_header_t *hdr = (binary_tlv_header_t *)sem->tlv_binary;",
                "    hdr->length = sem->tlv_binary_length - sizeof(binary_tlv_header_t);",
                "    hdr->crc32 = 0;",
                "    hdr->crc32 = calculate_crc32(sem->tlv_binary, sem->tlv_binary_length);",
                "    return 0;",
                "}",
                "",
                "int semantic_write_field(device_semantic_t *sem, const field_descriptor_t *fd, uint64_t value)",
                "{",
                "    if (!sem || !fd || !fd->present || !sem->tlv_binary) {",
                "        return -1;",
                "    }",
                "",
                "    uint16_t offset = fd->offset;",
                "    uint8_t size = field_type_size(fd->type);",
                "    if (offset + size > sem->tlv_binary_length) {",
                "        return -1;",
                "    }",
                "",
                "    uint8_t *ptr = sem->tlv_binary + offset;",
                "    /* FIELD_TYPE_BOOL == FIELD_TYPE_U8, handle them together */",
                "    if (fd->type == FIELD_TYPE_U8 || fd->type == FIELD_TYPE_BOOL) {",
                "        *ptr = (uint8_t)value;",
                "    } else if (fd->type == FIELD_TYPE_U16) {",
                "        ptr[0] = value & 0xFF;",
                "        ptr[1] = (value >> 8) & 0xFF;",
                "    } else if (fd->type == FIELD_TYPE_U32) {",
                "        ptr[0] = value & 0xFF;",
                "        ptr[1] = (value >> 8) & 0xFF;",
                "        ptr[2] = (value >> 16) & 0xFF;",
                "        ptr[3] = (value >> 24) & 0xFF;",
                "    } else if (fd->type == FIELD_TYPE_U64) {",
                "        for (uint8_t i = 0; i < 8; i++) {",
                "            ptr[i] = (value >> (i * 8)) & 0xFF;",
                "        }",
                "    } else {",
                "        return -1;",
                "    }",
                "",
                "    sem->global_dirty = 1;",
                "    return 0;",
                "}",
                "",
                "int semantic_read_field(const device_semantic_t *sem, const field_descriptor_t *fd, uint64_t *value)",
                "{",
                "    if (!sem || !fd || !fd->present || !sem->tlv_binary || !value) {",
                "        return -1;",
                "    }",
                "",
                "    uint16_t offset = fd->offset;",
                "    uint8_t size = field_type_size(fd->type);",
                "    if (offset + size > sem->tlv_binary_length) {",
                "        return -1;",
                "    }",
                "",
                "    const uint8_t *ptr = sem->tlv_binary + offset;",
                "    *value = 0;",
                "    /* FIELD_TYPE_BOOL == FIELD_TYPE_U8, handle them together */",
                "    if (fd->type == FIELD_TYPE_U8 || fd->type == FIELD_TYPE_BOOL) {",
                "        *value = *ptr;",
                "    } else if (fd->type == FIELD_TYPE_U16) {",
                "        *value = ptr[0] | ((uint16_t)ptr[1] << 8);",
                "    } else if (fd->type == FIELD_TYPE_U32) {",
                "        *value = ptr[0] | ((uint32_t)ptr[1] << 8) | ((uint32_t)ptr[2] << 16) | ((uint32_t)ptr[3] << 24);",
                "    } else if (fd->type == FIELD_TYPE_U64) {",
                "        for (uint8_t i = 0; i < 8; i++) {",
                "            *value |= ((uint64_t)ptr[i]) << (i * 8);",
                "        }",
                "    } else {",
                "        return -1;",
                "    }",
                "",
                "    return 0;",
                "}",
                "",
            ]
        )

        return "\n".join(lines)


