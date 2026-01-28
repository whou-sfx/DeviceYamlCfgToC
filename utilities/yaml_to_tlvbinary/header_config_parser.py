#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Header Config Parser模块
用于解析C头文件中的配置定义
"""

import re
import os
from typing import Dict, Optional
from pathlib import Path


class HeaderConfigParser:
    """C头文件配置解析器
    
    解析device_config_header.h中的#define宏定义，
    提取版本号和特性位图的配置常量。
    """
    
    # 默认头文件路径（相对于此脚本的位置）
    DEFAULT_HEADER_PATH = "../../cfg/device_config_header.h"
    
    def __init__(self, header_file: Optional[str] = None):
        """初始化解析器
        
        Args:
            header_file: C头文件路径，如果为None则使用默认路径
        """
        if header_file is None:
            # 使用相对于此脚本的默认路径
            script_dir = Path(__file__).parent
            header_file = script_dir / self.DEFAULT_HEADER_PATH
        
        self.header_file = Path(header_file).resolve()
        self._defines: Dict[str, int] = {}
        self._enums: Dict[str, Dict[str, int]] = {}  # 枚举类型到枚举值的映射
        self._parse_header()
    
    def _parse_header(self) -> None:
        """解析头文件中的#define定义"""
        if not self.header_file.exists():
            raise FileNotFoundError(
                f"Header file not found: {self.header_file}"
            )
        
        with open(self.header_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 移除C风格注释
        content = self._remove_c_comments(content)
        
        # 解析#define宏
        self._parse_defines(content)
        
        # 解析枚举定义
        self._parse_enums(content)
    
    def _remove_c_comments(self, text: str) -> str:
        """移除C风格的注释
        
        Args:
            text: 源文本
            
        Returns:
            移除注释后的文本
        """
        # 移除多行注释 /* ... */
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        
        # 移除单行注释 //
        text = re.sub(r'//.*?$', '', text, flags=re.MULTILINE)
        
        return text
    
    def _parse_defines(self, content: str) -> None:
        """解析#define宏定义
        
        Args:
            content: 头文件内容
        """
        # 匹配 #define NAME VALUE 格式
        # 支持十进制、十六进制和位移运算
        # 使用更宽松的匹配，直到行尾或注释
        pattern = r'#define\s+([A-Z_][A-Z0-9_]*)\s+(.+?)(?:/\*|$)'
        
        # 收集所有定义
        all_defines = []
        for match in re.finditer(pattern, content, re.MULTILINE):
            name = match.group(1)
            value_str = match.group(2).strip()
            all_defines.append((name, value_str))
        
        # 多次解析以处理依赖关系
        max_iterations = 10
        for iteration in range(max_iterations):
            parsed_count = 0
            for name, value_str in all_defines:
                if name in self._defines:
                    continue
                
                # 尝试计算值
                try:
                    value = self._evaluate_value(value_str)
                    self._defines[name] = value
                    parsed_count += 1
                except (ValueError, SyntaxError, NameError):
                    # 无法解析的值跳过，可能在下一次迭代中解析
                    pass
            
            # 如果没有新的定义被解析，退出循环
            if parsed_count == 0:
                break
    
    def _evaluate_value(self, value_str: str) -> int:
        """计算宏定义的值
        
        Args:
            value_str: 值字符串
            
        Returns:
            计算后的整数值
        """
        # 移除U后缀（如 1U）
        value_str = re.sub(r'U\b', '', value_str, flags=re.IGNORECASE)
        
        # 替换已知的宏定义
        for name, value in self._defines.items():
            value_str = re.sub(r'\b' + name + r'\b', str(value), value_str)
        
        # 移除括号外的空格
        value_str = value_str.strip()
        
        # 处理括号表达式
        if value_str.startswith('(') and value_str.endswith(')'):
            value_str = value_str[1:-1].strip()
        
        # 尝试直接转换
        try:
            # 支持十六进制
            if value_str.startswith('0x') or value_str.startswith('0X'):
                return int(value_str, 16)
            # 支持十进制
            return int(value_str)
        except ValueError:
            pass
        
        # 尝试计算表达式（仅支持安全的位运算）
        # 只允许数字、空格和位运算符
        if re.match(r'^[\d\s\+\-\*\/\(\)\<\>\&\|\^]+$', value_str):
            try:
                # 使用eval计算，但限制命名空间以提高安全性
                return int(eval(value_str, {"__builtins__": {}}, {}))
            except:
                pass
        
        raise ValueError(f"Cannot evaluate value: {value_str}")
    
    def get(self, name: str, default: Optional[int] = None) -> Optional[int]:
        """获取宏定义的值
        
        Args:
            name: 宏名称
            default: 默认值
            
        Returns:
            宏的值，如果不存在则返回默认值
        """
        return self._defines.get(name, default)
    
    def get_config_version(self) -> int:
        """获取默认配置版本号"""
        return self.get('CONFIG_VERSION_DEFAULT', 1)
    
    def get_schema_version(self) -> int:
        """获取默认Schema版本号"""
        return self.get('SCHEMA_VERSION_DEFAULT', 1)
    
    def get_feature_bitmap_default(self) -> int:
        """获取默认Feature Bitmap值"""
        return self.get('FEATURE_BITMAP_DEFAULT', 0)
    
    def get_feature_bit(self, feature_name: str) -> Optional[int]:
        """获取特性位的位位置
        
        Args:
            feature_name: 特性名称（如'DUAL_PORT', 'MLD', 'DCD'）
            
        Returns:
            位位置，如果不存在则返回None
        """
        key = f'FEATURE_BIT_{feature_name.upper()}'
        return self.get(key)
    
    def get_feature_mask(self, feature_name: str) -> Optional[int]:
        """获取特性位的掩码
        
        Args:
            feature_name: 特性名称（如'DUAL_PORT', 'MLD', 'DCD'）
            
        Returns:
            掩码值，如果不存在则返回None
        """
        key = f'FEATURE_MASK_{feature_name.upper()}'
        return self.get(key)
    
    def list_features(self) -> Dict[str, Dict[str, int]]:
        """列出所有定义的特性
        
        Returns:
            特性字典，格式: {feature_name: {'bit': bit_pos, 'mask': mask_value}}
        """
        features = {}
        
        # 查找所有FEATURE_BIT_*定义
        for name, value in self._defines.items():
            if name.startswith('FEATURE_BIT_'):
                feature_name = name[12:]  # 移除'FEATURE_BIT_'前缀
                mask_name = f'FEATURE_MASK_{feature_name}'
                
                features[feature_name] = {
                    'bit': value,
                    'mask': self._defines.get(mask_name, 1 << value)
                }
        
        return features
    
    def create_feature_bitmap(self, *feature_names: str) -> int:
        """根据特性名称创建Feature Bitmap
        
        Args:
            *feature_names: 特性名称列表（如'DUAL_PORT', 'MLD'）
            
        Returns:
            组合的Feature Bitmap值
        """
        bitmap = 0
        for name in feature_names:
            mask = self.get_feature_mask(name)
            if mask is not None:
                bitmap |= mask
        return bitmap
    
    def decode_feature_bitmap(self, bitmap: int) -> list:
        """解码Feature Bitmap，返回启用的特性列表
        
        Args:
            bitmap: Feature Bitmap值
            
        Returns:
            启用的特性名称列表
        """
        enabled_features = []
        features = self.list_features()
        
        for feature_name, info in features.items():
            if bitmap & info['mask']:
                enabled_features.append(feature_name)
        
        return enabled_features
    
    def _parse_enums(self, content: str) -> None:
        """解析C头文件中的枚举定义
        
        Args:
            content: 头文件内容
        """
        # 匹配 typedef enum { ... } enum_name_t; 格式
        enum_pattern = re.compile(
            r'typedef\s+enum\s*\{([^}]+)\}\s*(\w+)\s*;',
            re.MULTILINE | re.DOTALL
        )
        
        for match in enum_pattern.finditer(content):
            enum_body, enum_name = match.groups()
            self._enums[enum_name] = self._parse_enum_values(enum_body)
    
    def _parse_enum_values(self, enum_body: str) -> Dict[str, int]:
        """解析枚举体中的值定义
        
        Args:
            enum_body: 枚举体内容
            
        Returns:
            枚举名称到值的映射
        """
        enum_values = {}
        current_value = 0
        
        # 移除Doxygen注释
        enum_body = re.sub(r'/\*\*<.*?\*/', '', enum_body)
        
        # 匹配枚举项: NAME 或 NAME = VALUE
        pattern = r'([A-Z_][A-Z0-9_]*)\s*(?:=\s*(\d+))?'
        
        for match in re.finditer(pattern, enum_body):
            name = match.group(1)
            value_str = match.group(2)
            
            if value_str:
                # 显式指定了值
                current_value = int(value_str, 0)
            
            enum_values[name] = current_value
            current_value += 1
        
        return enum_values
    
    def get_enum_value(self, enum_type: str, enum_name: str) -> int:
        """获取枚举值
        
        Args:
            enum_type: 枚举类型名称（如 "pcie_speed_t"）
            enum_name: 枚举名称（如 "PCIE_SPEED_GEN5"）
            
        Returns:
            枚举对应的整数值
            
        Raises:
            ValueError: 如果枚举类型或枚举名称不存在
        """
        if enum_type not in self._enums:
            raise ValueError(f"Unknown enum type: {enum_type}")
        
        if enum_name not in self._enums[enum_type]:
            raise ValueError(f"Unknown enum name: {enum_name} in {enum_type}")
        
        return self._enums[enum_type][enum_name]
    
    def list_enums(self) -> Dict[str, Dict[str, int]]:
        """列出所有枚举定义
        
        Returns:
            枚举类型到枚举值映射的字典
        """
        return self._enums.copy()
    
    def __str__(self) -> str:
        """返回解析器的字符串表示"""
        return (f"HeaderConfigParser(\n"
                f"  header_file={self.header_file},\n"
                f"  config_version={self.get_config_version()},\n"
                f"  schema_version={self.get_schema_version()},\n"
                f"  feature_bitmap_default=0x{self.get_feature_bitmap_default():08X},\n"
                f"  enums_count={len(self._enums)}\n"
                f")")


# 创建全局单例实例
_parser_instance: Optional[HeaderConfigParser] = None


def get_parser(header_file: Optional[str] = None) -> HeaderConfigParser:
    """获取HeaderConfigParser单例实例
    
    Args:
        header_file: C头文件路径，如果为None则使用默认路径
        
    Returns:
        HeaderConfigParser实例
    """
    global _parser_instance
    
    if _parser_instance is None or header_file is not None:
        _parser_instance = HeaderConfigParser(header_file)
    
    return _parser_instance


# 便捷函数
def get_config_version() -> int:
    """获取默认配置版本号"""
    return get_parser().get_config_version()


def get_schema_version() -> int:
    """获取默认Schema版本号"""
    return get_parser().get_schema_version()


def get_feature_bitmap_default() -> int:
    """获取默认Feature Bitmap值"""
    return get_parser().get_feature_bitmap_default()


def list_features() -> Dict[str, Dict[str, int]]:
    """列出所有定义的特性"""
    return get_parser().list_features()


def create_feature_bitmap(*feature_names: str) -> int:
    """根据特性名称创建Feature Bitmap"""
    return get_parser().create_feature_bitmap(*feature_names)


def decode_feature_bitmap(bitmap: int) -> list:
    """解码Feature Bitmap"""
    return get_parser().decode_feature_bitmap(bitmap)


if __name__ == '__main__':
    # 测试代码
    parser = get_parser()
    print(parser)
    print("\n可用特性:")
    for name, info in parser.list_features().items():
        print(f"  {name}: bit={info['bit']}, mask=0x{info['mask']:02X}")
    
    # 测试创建bitmap
    bitmap = create_feature_bitmap('DUAL_PORT', 'MLD')
    print(f"\n启用Dual-Port和MLD: 0x{bitmap:02X}")
    print(f"解码结果: {decode_feature_bitmap(bitmap)}")

