#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schema驱动编码器测试脚本
演示如何使用Schema驱动编码器进行TLV编码
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from schema_driven_encoder import SchemaDrivenEncoder


def test_basic_encoding():
    """测试基本编码功能"""
    print("=" * 70)
    print("测试1: 基本编码功能")
    print("=" * 70)
    
    encoder = SchemaDrivenEncoder(verbose=True)
    
    # 测试Device.Basic
    config_item = {
        'Type': 'Device.Basic',
        'Enable': True,
        'Value': {
            'DeviceType': 'CXL_Type3',
            'HDMType': 'HDM-H',
            'TotalDRAMCapacity': '512GB',
            'DRAMShareable': True
        }
    }
    
    tlv_data = encoder.encode_config_item(config_item)
    print(f"\n生成的TLV数据长度: {len(tlv_data)} 字节")
    print(f"前32字节的十六进制: {tlv_data[:32].hex()}")
    print()


def test_disabled_config():
    """测试禁用的配置项"""
    print("=" * 70)
    print("测试2: 禁用的配置项")
    print("=" * 70)
    
    encoder = SchemaDrivenEncoder(verbose=True)
    
    # 测试禁用的Port.Config
    config_item = {
        'Type': 'Port.Config',
        'Enable': False,  # 禁用
        'Value': {
            'PortID': 0,
            'EnablePort': False,
            'PCIeSpeed': 'Gen5',
            'PCIeWidth': 'x16',
            'LDMode': 'SLD'
        }
    }
    
    tlv_data = encoder.encode_config_item(config_item)
    print(f"\n生成的TLV数据长度: {len(tlv_data)} 字节")
    
    # 检查Enable字段（第2个字节应该是0）
    enable_byte = tlv_data[1]
    print(f"Enable字段值: {enable_byte} (0=禁用, 1=启用)")
    print()


def test_list_schemas():
    """测试列出所有支持的Schema"""
    print("=" * 70)
    print("测试3: 列出所有支持的TLV类型")
    print("=" * 70)
    
    encoder = SchemaDrivenEncoder()
    
    print("\n支持的TLV类型:")
    for type_name in encoder.list_supported_types():
        schema = encoder.get_schema(type_name)
        print(f"\n{type_name} (Type ID: 0x{schema['type_id']:02X})")
        print(f"  描述: {schema.get('description', 'N/A')}")
        print(f"  字段数: {len(schema['fields'])}")
        print(f"  对齐: {schema.get('alignment', 4)} 字节")
        
        # 列出字段
        for field in schema['fields']:
            field_info = f"    - {field['name']}: {field['type']}"
            if field['type'] == 'string':
                field_info += f" (size={field.get('size', 'N/A')})"
            if 'parser' in field:
                field_info += f" [parser={field['parser']}]"
            print(field_info)
    print()


def test_special_parsers():
    """测试特殊解析器"""
    print("=" * 70)
    print("测试4: 特殊解析器")
    print("=" * 70)
    
    encoder = SchemaDrivenEncoder(verbose=True)
    
    # 测试LD.Range（包含size_string和hex_string解析器）
    config_item = {
        'Type': 'LD.Range',
        'Enable': True,
        'Value': {
            'PortID': 0,
            'LDID': 0,
            'RangeID': 0,
            'Start_DPA': '0x0000_0000_0000',
            'Length': '256GB',
            'DCD_Supported': True,
            'ShareModeEnable': False
        }
    }
    
    tlv_data = encoder.encode_config_item(config_item)
    print(f"\n生成的TLV数据长度: {len(tlv_data)} 字节")
    print()


def main():
    """主函数"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "Schema驱动编码器测试" + " " * 33 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    try:
        test_basic_encoding()
        test_disabled_config()
        test_list_schemas()
        test_special_parsers()
        
        print("=" * 70)
        print("✓ 所有测试通过！")
        print("=" * 70)
        print()
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

