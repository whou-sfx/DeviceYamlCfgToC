"""TLV Schema字段类型到C类型的映射与辅助函数。"""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class CTypeInfo:
    c_type: str
    field_type: str
    size: int


class CTypeMapper:
    """提供YAML类型到C类型/字段类型/大小的映射。"""

    _type_map: Dict[str, CTypeInfo] = {
        "u8": CTypeInfo(c_type="uint8_t", field_type="FIELD_TYPE_U8", size=1),
        "u16": CTypeInfo(c_type="uint16_t", field_type="FIELD_TYPE_U16", size=2),
        "u32": CTypeInfo(c_type="uint32_t", field_type="FIELD_TYPE_U32", size=4),
        "u64": CTypeInfo(c_type="uint64_t", field_type="FIELD_TYPE_U64", size=8),
        "bool": CTypeInfo(c_type="uint8_t", field_type="FIELD_TYPE_BOOL", size=1),
        "string": CTypeInfo(c_type="char", field_type="FIELD_TYPE_U8", size=1),
    }

    @classmethod
    def get(cls, yaml_type: str) -> CTypeInfo:
        if yaml_type not in cls._type_map:
            raise KeyError(f"Unsupported yaml field type: {yaml_type}")
        return cls._type_map[yaml_type]

    @classmethod
    def c_type(cls, yaml_type: str) -> str:
        return cls.get(yaml_type).c_type

    @classmethod
    def field_type(cls, yaml_type: str) -> str:
        return cls.get(yaml_type).field_type

    @classmethod
    def size(cls, yaml_type: str) -> int:
        return cls.get(yaml_type).size



