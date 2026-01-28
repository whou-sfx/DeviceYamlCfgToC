#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置Schema定义模块
从tlv_schema.yaml自动加载验证规则，消除硬编码
"""

import yaml
from typing import Dict, Any, List
from pathlib import Path


class ConfigSchema:
    """配置Schema类
    
    自动从tlv_schema.yaml加载TLV结构定义，
    提供配置验证功能，无需手动维护字段列表。
    """
    
    # 类变量：缓存加载的schema
    _schema_cache = None
    _schema_file = None
    
    @classmethod
    def _load_schema(cls, schema_file: str = None) -> Dict[str, List[str]]:
        """加载TLV Schema
        
        Args:
            schema_file: Schema文件路径，None则使用默认路径
            
        Returns:
            TLV类型到字段名列表的映射
        """
        # 如果已缓存且路径未变，直接返回
        if cls._schema_cache is not None and cls._schema_file == schema_file:
            return cls._schema_cache
        
        # 确定schema文件路径
        if schema_file is None:
            script_dir = Path(__file__).parent
            schema_file = script_dir / "../../cfg/tlv_schema.yaml"
        
        schema_file = Path(schema_file).resolve()
        
        if not schema_file.exists():
            raise FileNotFoundError(f"TLV Schema file not found: {schema_file}")
        
        # 加载YAML
        with open(schema_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            schemas = config.get('TLV_Schemas', {})
        
        # 构建类型到字段名列表的映射
        type_schema_map = {}
        for tlv_type, schema in schemas.items():
            fields = schema.get('fields', [])
            # 提取所有字段名
            field_names = [field['name'] for field in fields]
            type_schema_map[tlv_type] = field_names
        
        # 缓存结果
        cls._schema_cache = type_schema_map
        cls._schema_file = schema_file
        
        return type_schema_map
    
    @classmethod
    def get_supported_types(cls, schema_file: str = None) -> List[str]:
        """获取所有支持的TLV类型
        
        Args:
            schema_file: Schema文件路径
            
        Returns:
            TLV类型列表
        """
        schema_map = cls._load_schema(schema_file)
        return list(schema_map.keys())
    
    @classmethod
    def get_required_fields(cls, tlv_type: str, schema_file: str = None) -> List[str]:
        """获取指定TLV类型的必需字段列表
        
        Args:
            tlv_type: TLV类型名称
            schema_file: Schema文件路径
            
        Returns:
            字段名列表
        """
        schema_map = cls._load_schema(schema_file)
        return schema_map.get(tlv_type, [])
    
    @classmethod
    def validate_config_item(cls, config_item: dict, schema_file: str = None) -> List[str]:
        """验证配置项
        
        Args:
            config_item: 配置项字典
            schema_file: Schema文件路径
            
        Returns:
            错误信息列表，如果为空则表示验证通过
        """
        errors = []
        
        tlv_type = config_item.get('Type')
        if not tlv_type:
            errors.append("Missing 'Type' field")
            return errors
        
        # 加载schema
        schema_map = cls._load_schema(schema_file)
        
        if tlv_type not in schema_map:
            errors.append(f"Unknown TLV type: {tlv_type}")
            return errors
        
        required_fields = schema_map[tlv_type]
        value = config_item.get('Value', {})
        
        # 验证所有必需字段是否存在
        for field_name in required_fields:
            if field_name not in value:
                errors.append(f"Missing required field '{field_name}' in {tlv_type}")
        
        return errors
    
    @classmethod
    def validate_config_list(cls, config_list: List[dict], schema_file: str = None) -> List[str]:
        """验证配置列表
        
        Args:
            config_list: 配置项列表
            schema_file: Schema文件路径
            
        Returns:
            错误信息列表，如果为空则表示验证通过
        """
        all_errors = []
        
        for i, config_item in enumerate(config_list):
            errors = cls.validate_config_item(config_item, schema_file)
            if errors:
                all_errors.append(f"Config item {i}:")
                all_errors.extend([f"  - {err}" for err in errors])
        
        return all_errors
    
    @classmethod
    def clear_cache(cls):
        """清除schema缓存
        
        用于测试或需要重新加载schema的场景
        """
        cls._schema_cache = None
        cls._schema_file = None


# 向后兼容：保留旧的接口
def validate_config_list(config_list: List[dict]) -> List[str]:
    """验证配置列表（兼容接口）
    
    Args:
        config_list: 配置项列表
        
    Returns:
        错误信息列表
    """
    return ConfigSchema.validate_config_list(config_list)


def get_supported_types() -> List[str]:
    """获取支持的TLV类型（兼容接口）
    
    Returns:
        TLV类型列表
    """
    return ConfigSchema.get_supported_types()


if __name__ == '__main__':
    # 测试代码
    print("=== ConfigSchema 测试 ===\n")
    
    # 测试1：加载schema
    print("1. 加载支持的TLV类型:")
    types = ConfigSchema.get_supported_types()
    for tlv_type in types:
        fields = ConfigSchema.get_required_fields(tlv_type)
        print(f"  {tlv_type}:")
        print(f"    必需字段: {', '.join(fields)}")
    
    # 测试2：验证配置项
    print("\n2. 验证配置项:")
    
    # 有效配置
    valid_config = {
        'Type': 'Device.Basic',
        'Enable': True,
        'Value': {
            'TotalDRAMCapacity': '512GB',
            'DRAMShareable': True
        }
    }
    errors = ConfigSchema.validate_config_item(valid_config)
    print(f"  有效配置: {'✓ 通过' if not errors else '✗ 失败'}")
    
    # 缺少字段的配置
    invalid_config = {
        'Type': 'Device.Basic',
        'Enable': True,
        'Value': {
            'TotalDRAMCapacity': '512GB'
            # 缺少 DRAMShareable
        }
    }
    errors = ConfigSchema.validate_config_item(invalid_config)
    print(f"  无效配置: {'✓ 检测到错误' if errors else '✗ 未检测到错误'}")
    if errors:
        for error in errors:
            print(f"    - {error}")
    
    # 测试3：验证配置列表
    print("\n3. 验证配置列表:")
    config_list = [valid_config, invalid_config]
    errors = ConfigSchema.validate_config_list(config_list)
    if errors:
        print("  发现错误:")
        for error in errors:
            print(f"    {error}")
    else:
        print("  ✓ 所有配置项验证通过")
