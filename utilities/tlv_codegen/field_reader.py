"""生成字段读取C代码片段。"""

from typing import Dict

from .type_mapper import CTypeMapper


class FieldReader:
    """生成小端序字段读取代码。"""

    @staticmethod
    def generate_read_expr(yaml_type: str, base_ptr: str, offset: int) -> str:
        """生成读取表达式，base_ptr为uint8_t*指针变量名。"""
        if yaml_type == "u8" or yaml_type == "bool":
            return f"{base_ptr}[{offset}]"
        if yaml_type == "u16":
            return (f"({base_ptr}[{offset}] | "
                    f"((uint16_t){base_ptr}[{offset + 1}] << 8))")
        if yaml_type == "u32":
            return (f"({base_ptr}[{offset}] | "
                    f"((uint32_t){base_ptr}[{offset + 1}] << 8) | "
                    f"((uint32_t){base_ptr}[{offset + 2}] << 16) | "
                    f"((uint32_t){base_ptr}[{offset + 3}] << 24))")
        if yaml_type == "u64":
            parts = []
            for i in range(8):
                shift = i * 8
                parts.append(f"((uint64_t){base_ptr}[{offset + i}] << {shift})")
            return "(" + " | ".join(parts) + ")"
        if yaml_type == "string":
            return f"(const char *)(&{base_ptr}[{offset}])"
        raise KeyError(f"Unsupported yaml field type: {yaml_type}")

    @classmethod
    def generate_assign_statement(
        cls,
        field_name: str,
        yaml_type: str,
        offset: int,
        base_ptr: str = "v",
        target_ptr: str = "p",
    ) -> str:
        """生成赋值语句（将读取结果写入结构体字段）。"""
        expr = cls.generate_read_expr(yaml_type, base_ptr, offset)
        return f"{target_ptr}->{field_name} = {expr};"

    @staticmethod
    def field_descriptor_init(
        field_name: str,
        yaml_type: str,
        offset: int,
        base_offset_var: str = "base",
        target_ptr: str = "p",
    ) -> str:
        """生成字段描述符初始化语句。"""
        field_type = CTypeMapper.field_type(yaml_type)
        return (
            f"{target_ptr}->fd_{field_name} = (field_descriptor_t){{"
            f" .offset = {base_offset_var} + {offset},"
            f" .type = {field_type},"
            f" .present = 1 }};"
        )

    @staticmethod
    def size_map(schema_fields: list) -> Dict[str, int]:
        """返回字段名到size的映射。"""
        return {field["name"]: CTypeMapper.size(field["type"]) for field in schema_fields}



