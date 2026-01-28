#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schema驱动的TLV编码器
通过YAML配置文件定义TLV结构，实现通用编码逻辑
"""

import struct
import yaml
from typing import Any, Dict, List
from pathlib import Path

try:
    from .header_config_parser import HeaderConfigParser
except ImportError:
    from header_config_parser import HeaderConfigParser


class SchemaDrivenEncoder:
    """基于Schema的通用TLV编码器
    
    通过读取tlv_schema.yaml文件来获取TLV结构定义，
    实现通用的编码逻辑，无需为每种TLV类型编写专门的编码方法。
    """
    
    def __init__(self, schema_file: str = None, verbose: int = 0):
        """初始化编码器
        
        Args:
            schema_file: TLV Schema YAML文件路径，None则使用默认路径
            verbose: 详细输出级别 (0=无, 1=仅启用项, 2=所有项)
        """
        self.verbose = verbose
        
        # 初始化HeaderConfigParser以支持枚举解析
        self.header_parser = HeaderConfigParser()
        
        # 加载Schema
        if schema_file is None:
            script_dir = Path(__file__).parent
            schema_file = script_dir / "../../cfg/tlv_schema.yaml"
        
        self.schema_file = Path(schema_file)
        
        if not self.schema_file.exists():
            raise FileNotFoundError(f"TLV Schema file not found: {self.schema_file}")
        
        with open(self.schema_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            self.schemas = config.get('TLV_Schemas', {})
        
        if not self.schemas:
            raise ValueError(f"No TLV_Schemas found in {self.schema_file}")
        
        # 构建类型名称到Schema的映射
        self.type_map = {}
        for type_name, schema in self.schemas.items():
            self.type_map[type_name] = schema
    
    # ========================================================================
    # 基本类型编码方法
    # ========================================================================
    
    def encode_u8(self, value: int) -> bytes:
        """编码U8类型"""
        return struct.pack('<B', value & 0xFF)
    
    def encode_u16(self, value: int) -> bytes:
        """编码U16类型"""
        return struct.pack('<H', value & 0xFFFF)
    
    def encode_u32(self, value: int) -> bytes:
        """编码U32类型"""
        return struct.pack('<I', value & 0xFFFFFFFF)
    
    def encode_u64(self, value: int) -> bytes:
        """编码U64类型"""
        return struct.pack('<Q', value & 0xFFFFFFFFFFFFFFFF)
    
    def encode_bool(self, value: bool) -> bytes:
        """编码布尔类型为U8"""
        return self.encode_u8(1 if value else 0)
    
    def encode_string(self, value: str, max_len: int) -> bytes:
        """编码字符串类型
        
        Args:
            value: 字符串值
            max_len: 最大长度
            
        Returns:
            定长字节数据，不足部分补0
        """
        encoded = value.encode('utf-8')
        if len(encoded) > max_len:
            encoded = encoded[:max_len]
        return encoded + b'\x00' * (max_len - len(encoded))
    
    # ========================================================================
    # 特殊解析器
    # ========================================================================
    
    def parse_size_string(self, size_str) -> int:
        """解析大小字符串 (如 "512GB", "64GB") 为字节数
        
        Args:
            size_str: 大小字符串或整数
            
        Returns:
            字节数
        """
        if isinstance(size_str, int):
            return size_str
        
        size_str = str(size_str).strip().upper()
        
        if size_str.endswith('GB'):
            return int(size_str[:-2]) * (1024 ** 3)
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * (1024 ** 2)
        elif size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('B'):
            return int(size_str[:-1])
        else:
            # 尝试直接解析为整数
            return int(size_str, 0)
    
    def parse_hex_string(self, hex_str) -> int:
        """解析十六进制字符串 (如 "0x0000_0000_0000")
        
        Args:
            hex_str: 十六进制字符串或整数
            
        Returns:
            整数值
        """
        if isinstance(hex_str, int):
            return hex_str
        
        # 移除下划线和空格
        hex_str = str(hex_str).replace('_', '').replace(' ', '').strip()
        return int(hex_str, 16)
    
    def parse_enum(self, value, enum_type: str) -> int:
        """解析枚举值
        
        Args:
            value: 枚举名称字符串或整数
            enum_type: 枚举类型名称（如 "pcie_speed_t"）
            
        Returns:
            枚举对应的整数值
        """
        if isinstance(value, int):
            return value
        
        # 查找枚举值
        return self.header_parser.get_enum_value(enum_type, value)
    
    # ========================================================================
    # Schema驱动的编码方法
    # ========================================================================
    
    def encode_field(self, field_def: dict, value: Any) -> bytes:
        """根据字段定义编码单个字段
        
        Args:
            field_def: 字段定义（来自Schema）
            value: 字段值
            
        Returns:
            编码后的字节数据
        """
        field_type = field_def['type']
        parser = field_def.get('parser')
        
        # 如果有特殊解析器，先解析值
        if parser == 'size_string':
            value = self.parse_size_string(value)
        elif parser == 'hex_string':
            value = self.parse_hex_string(value)
        elif parser == 'enum':
            enum_type = field_def.get('enum_type')
            if not enum_type:
                raise ValueError(f"Field {field_def.get('name')} has parser=enum but no enum_type specified")
            value = self.parse_enum(value, enum_type)
        
        # 根据类型编码
        if field_type == 'u8':
            return self.encode_u8(value)
        elif field_type == 'u16':
            return self.encode_u16(value)
        elif field_type == 'u32':
            return self.encode_u32(value)
        elif field_type == 'u64':
            return self.encode_u64(value)
        elif field_type == 'bool':
            return self.encode_bool(value)
        elif field_type == 'string':
            size = field_def.get('size', 32)
            return self.encode_string(value, size)
        else:
            raise ValueError(f"Unknown field type: {field_type}")
    
    def encode_value_by_schema(self, type_name: str, value: dict) -> bytes:
        """根据Schema编码Value部分
        
        Args:
            type_name: TLV类型名称（如 "Device.Basic"）
            value: 值字典
            
        Returns:
            编码后的Value数据
        """
        if type_name not in self.type_map:
            raise ValueError(f"Unknown TLV type: {type_name}")
        
        schema = self.type_map[type_name]
        data = bytearray()
        
        # 按照Schema定义的顺序编码字段
        for field_def in schema['fields']:
            field_name = field_def['name']
            field_value = value.get(field_name)
            
            # 如果值为None，使用默认值
            if field_value is None:
                if field_def['type'] in ['u8', 'u16', 'u32', 'u64']:
                    field_value = 0
                elif field_def['type'] == 'bool':
                    field_value = False
                elif field_def['type'] == 'string':
                    field_value = ''
            
            # 编码字段
            field_data = self.encode_field(field_def, field_value)
            data.extend(field_data)
        
        # 对齐
        alignment = schema.get('alignment', 4)
        while len(data) % alignment != 0:
            data.append(0)
        
        return bytes(data)
    
    def encode_tlv(self, tlv_type: int, value_data: bytes, enable: bool = True) -> bytes:
        """编码TLV结构
        
        TLV结构:
        - Type (U8): TLV类型ID
        - Enable (U8): 启用标志 (1=启用, 0=禁用)
        - Length (U16): Value字段长度
        - Value (可变长度): 具体配置数据
        
        Args:
            tlv_type: TLV类型ID
            value_data: Value部分的字节数据
            enable: 是否启用
            
        Returns:
            完整的TLV字节数据
        """
        tlv = bytearray()
        
        # Type (U8)
        tlv.extend(self.encode_u8(tlv_type))
        
        # Enable (U8)
        tlv.extend(self.encode_u8(1 if enable else 0))
        
        # Length (U16)
        tlv.extend(self.encode_u16(len(value_data)))
        
        # Value
        tlv.extend(value_data)
        
        return bytes(tlv)
    
    def encode_config_item(self, config_item: dict) -> bytes:
        """编码单个配置项
        
        Args:
            config_item: 配置项字典，包含Type、Enable、Value
            
        Returns:
            编码后的TLV数据
        """
        tlv_type_str = config_item.get('Type', '')
        value = config_item.get('Value', {})
        enable = config_item.get('Enable', True)
        
        # 如果verbose模式，打印TLV信息
        # verbose=1: 只打印启用的项
        # verbose=2: 打印所有项
        if self.verbose > 0:
            if self.verbose == 1 and not enable:
                # Level 1: skip disabled items
                pass
            else:
                # Level 1 (enabled only) or Level 2 (all items)
                enable_str = '启用' if enable else '禁用'
                print(f"编码TLV: {tlv_type_str} (Enable={enable_str})")
                
                # Get schema to check field parsers for proper formatting
                schema = self.type_map.get(tlv_type_str, {})
                field_defs = schema.get('fields', [])
                field_parser_map = {field['name']: field.get('parser') for field in field_defs}
                
                for key, val in value.items():
                    # Check if this field uses hex_string parser
                    parser = field_parser_map.get(key)
                    if parser == 'hex_string' and isinstance(val, int):
                        # Display as hex for hex_string fields
                        print(f"  {key}: 0x{val:X}")
                    else:
                        print(f"  {key}: {val}")
        
        # 获取Schema
        if tlv_type_str not in self.type_map:
            raise ValueError(f"Unknown TLV type: {tlv_type_str}")
        
        schema = self.type_map[tlv_type_str]
        type_id = schema['type_id']
        
        # 使用Schema编码Value
        value_data = self.encode_value_by_schema(tlv_type_str, value)
        
        # 编码TLV
        tlv_data = self.encode_tlv(type_id, value_data, enable)
        
        # 如果verbose模式，打印TLV大小信息
        if self.verbose > 0:
            if self.verbose == 1 and not enable:
                pass  # Skip disabled items at level 1
            else:
                enable_val = 1 if enable else 0
                print(f"  → TLV大小: {len(tlv_data)}字节 (Type=0x{type_id:02X}, Enable={enable_val}, Length={len(value_data)})")
        
        return tlv_data
    
    def encode_config_list(self, config_list: List[dict]) -> bytes:
        """编码配置列表
        
        注意：所有配置项都会被编码，Enable字段会反映在TLV的Enable字段中
        
        Args:
            config_list: 配置项列表
            
        Returns:
            编码后的所有TLV数据
        """
        data = bytearray()
        
        if self.verbose > 0:
            total_items = len(config_list)
            if self.verbose == 1:
                enabled_count = sum(1 for item in config_list if item.get('Enable', True))
                print(f"\n开始编码 {total_items} 个配置项 (显示 {enabled_count} 个启用项)...")
            else:
                print(f"\n开始编码 {total_items} 个配置项...")
            print("=" * 70)
        
        for i, config_item in enumerate(config_list):
            if self.verbose > 0:
                # Only print item number if we're going to show this item
                enable = config_item.get('Enable', True)
                if self.verbose == 2 or (self.verbose == 1 and enable):
                    print(f"\n[{i+1}/{len(config_list)}] ", end="")
            
            # 编码所有配置项，无论Enable是true还是false
            tlv_data = self.encode_config_item(config_item)
            data.extend(tlv_data)
        
        if self.verbose > 0:
            print("\n" + "=" * 70)
        
        return bytes(data)
    
    def list_supported_types(self) -> List[str]:
        """列出所有支持的TLV类型
        
        Returns:
            TLV类型名称列表
        """
        return list(self.type_map.keys())
    
    def get_schema(self, type_name: str) -> dict:
        """获取指定TLV类型的Schema
        
        Args:
            type_name: TLV类型名称
            
        Returns:
            Schema字典
        """
        return self.type_map.get(type_name)
    
    def __str__(self) -> str:
        """返回编码器的字符串表示"""
        return (f"SchemaDrivenEncoder(\n"
                f"  schema_file={self.schema_file},\n"
                f"  supported_types={len(self.type_map)},\n"
                f"  verbose={self.verbose}\n"
                f")")


if __name__ == '__main__':
    # 测试代码
    encoder = SchemaDrivenEncoder(verbose=True)
    print(encoder)
    print("\n支持的TLV类型:")
    for type_name in encoder.list_supported_types():
        schema = encoder.get_schema(type_name)
        print(f"  - {type_name} (Type ID: 0x{schema['type_id']:02X})")

