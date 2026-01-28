#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YAML配置文件转Binary TLV工具
主转换脚本

注意：默认版本号和特性位图定义来自 cfg/device_config_header.h
"""

import sys
import os
import argparse
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tlv_encoder import TLVEncoder
from schema_driven_encoder import SchemaDrivenEncoder
from binary_header import BinaryHeader
from config_schema import ConfigSchema
from header_config_parser import get_parser, list_features


class YamlToBinaryConverter:
    """YAML到Binary TLV转换器"""
    
    def __init__(self, config_version: Optional[int] = None, 
                 schema_version: Optional[int] = None,
                 feature_bitmap: Optional[int] = None):
        """初始化转换器
        
        Args:
            config_version: 配置版本号，None则使用cfg/device_config_header.h中的默认值
            schema_version: Schema版本号，None则使用cfg/device_config_header.h中的默认值
            feature_bitmap: 特性位图，None则使用cfg/device_config_header.h中的默认值
        """
        # 使用Schema驱动的编码器
        self.encoder = SchemaDrivenEncoder()  # 稍后会设置verbose
        self.header = BinaryHeader(config_version, schema_version, feature_bitmap)
        self.verbose = False
    
    def load_yaml(self, yaml_file: str) -> Dict[str, Any]:
        """加载YAML配置文件
        
        Args:
            yaml_file: YAML文件路径
            
        Returns:
            配置字典
        """
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if self.verbose:
                print(f"✓ 成功加载YAML文件: {yaml_file}")
            
            return config
        except Exception as e:
            raise RuntimeError(f"加载YAML文件失败: {e}")
    
    def extract_config_list(self, config: Dict[str, Any]) -> List[dict]:
        """从配置字典中提取配置列表
        
        Args:
            config: 配置字典
            
        Returns:
            配置项列表
        """
        # 假设YAML文件的根键是配置名称，值是配置项列表
        if not config:
            raise ValueError("配置文件为空")
        
        # 获取第一个键的值（配置列表）
        root_key = list(config.keys())[0]
        config_list = config[root_key]
        
        if not isinstance(config_list, list):
            raise ValueError(f"配置项必须是列表类型，但得到: {type(config_list)}")
        
        if self.verbose:
            print(f"✓ 提取到 {len(config_list)} 个配置项")
        
        return config_list
    
    def validate_config(self, config_list: List[dict]) -> None:
        """验证配置
        
        Args:
            config_list: 配置项列表
        """
        errors = ConfigSchema.validate_config_list(config_list)
        
        if errors:
            print("配置验证失败:")
            for error in errors:
                print(f"  {error}")
            raise ValueError("配置验证失败")
        
        if self.verbose:
            print("✓ 配置验证通过")
    
    def convert(self, yaml_file: str, output_file: str, 
                validate: bool = True) -> None:
        """转换YAML文件到Binary TLV
        
        Args:
            yaml_file: 输入YAML文件路径
            output_file: 输出二进制文件路径
            validate: 是否验证配置
        """
        # 加载YAML
        config = self.load_yaml(yaml_file)
        
        # 提取配置列表
        config_list = self.extract_config_list(config)
        
        # 验证配置
        if validate:
            self.validate_config(config_list)
        
        # 设置encoder的verbose标志
        self.encoder.verbose = self.verbose
        
        # 编码TLV数据
        if self.verbose:
            print("正在编码TLV数据...")
        
        tlv_data = self.encoder.encode_config_list(config_list)
        
        if self.verbose:
            print(f"✓ TLV数据编码完成，大小: {len(tlv_data)} 字节")
        
        # 生成Header
        if self.verbose:
            print("正在生成Header...")
        
        header_data = self.header.pack_with_crc(tlv_data)
        
        if self.verbose:
            print(f"✓ Header生成完成")
            print(self.header)
        
        # 写入输出文件
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'wb') as f:
            f.write(header_data)
            f.write(tlv_data)
        
        total_size = len(header_data) + len(tlv_data)
        
        if self.verbose:
            print(f"✓ 成功写入输出文件: {output_file}")
            print(f"  - Header大小: {len(header_data)} 字节")
            print(f"  - TLV数据大小: {len(tlv_data)} 字节")
            print(f"  - 总大小: {total_size} 字节")
    
    def dump_binary(self, binary_file: str) -> None:
        """转储二进制文件内容（用于调试）
        
        Args:
            binary_file: 二进制文件路径
        """
        with open(binary_file, 'rb') as f:
            data = f.read()
        
        # 解析Header
        header = BinaryHeader.unpack(data[:BinaryHeader.HEADER_SIZE])
        tlv_data = data[BinaryHeader.HEADER_SIZE:]
        
        print("=" * 60)
        print("Binary TLV文件信息")
        print("=" * 60)
        print(header)
        print(f"\nTLV数据大小: {len(tlv_data)} 字节")
        
        # 验证CRC32
        is_valid = header.verify_crc32(
            data[:BinaryHeader.HEADER_SIZE], 
            tlv_data
        )
        print(f"CRC32验证: {'通过 ✓' if is_valid else '失败 ✗'}")
        
        # 转储十六进制数据（前256字节）
        print("\n前256字节的十六进制转储:")
        print("-" * 60)
        for i in range(0, min(256, len(data)), 16):
            hex_str = ' '.join(f'{b:02X}' for b in data[i:i+16])
            ascii_str = ''.join(
                chr(b) if 32 <= b < 127 else '.' 
                for b in data[i:i+16]
            )
            print(f"{i:08X}  {hex_str:<48}  {ascii_str}")


def main():
    """主函数"""
    # 获取配置解析器以获取默认值
    try:
        config_parser = get_parser()
        default_config_version = config_parser.get_config_version()
        default_schema_version = config_parser.get_schema_version()
        default_feature_bitmap = config_parser.get_feature_bitmap_default()
    except Exception:
        default_config_version = 1
        default_schema_version = 1
        default_feature_bitmap = 0
    
    parser = argparse.ArgumentParser(
        description='将YAML配置文件转换为Binary TLV格式\n'
                    '注意：默认版本号和特性位图定义来自 cfg/device_config_header.h',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 转换YAML到二进制
  %(prog)s -i cfg/deviceCfg.yaml -o output/device_config.bin
  
  # 转换并显示详细信息
  %(prog)s -i cfg/deviceCfg.yaml -o output/device_config.bin -v
  
  # 转储二进制文件内容
  %(prog)s -d output/device_config.bin
  
  # 自定义版本号和特性位图
  %(prog)s -i cfg/deviceCfg.yaml -o output/device_config.bin \\
           --config-version 2 --schema-version 3 --feature-bitmap 0xFF
  
  # 列出可用的特性位定义
  %(prog)s --list-features
        """
    )
    
    parser.add_argument('-i', '--input', type=str,
                        help='输入YAML配置文件路径')
    parser.add_argument('-o', '--output', type=str,
                        help='输出二进制文件路径')
    parser.add_argument('-d', '--dump', type=str,
                        help='转储二进制文件内容（用于调试）')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='显示详细信息')
    parser.add_argument('--no-validate', action='store_true',
                        help='跳过配置验证')
    parser.add_argument('--config-version', type=int, default=None,
                        help=f'配置版本号 (默认: {default_config_version}, 来自cfg/device_config_header.h)')
    parser.add_argument('--schema-version', type=int, default=None,
                        help=f'Schema版本号 (默认: {default_schema_version}, 来自cfg/device_config_header.h)')
    parser.add_argument('--feature-bitmap', type=lambda x: int(x, 0), default=None,
                        help=f'特性位图 (默认: 0x{default_feature_bitmap:02X}, 支持十六进制如0xFF)')
    parser.add_argument('--list-features', action='store_true',
                        help='列出cfg/device_config_header.h中定义的所有特性位')
    
    args = parser.parse_args()
    
    # 列出特性位模式
    if args.list_features:
        print("=" * 60)
        print("可用的Feature Bitmap定义 (来自cfg/device_config_header.h)")
        print("=" * 60)
        try:
            features = list_features()
            if features:
                print(f"\n{'特性名称':<20} {'位位置':<10} {'掩码':<10}")
                print("-" * 60)
                for name, info in sorted(features.items(), key=lambda x: x[1]['bit']):
                    print(f"{name:<20} bit{info['bit']:<7} 0x{info['mask']:02X}")
                print("\n使用示例:")
                print("  # 启用Dual-Port特性")
                print("  --feature-bitmap 0x01")
                print("\n  # 启用Dual-Port和MLD特性")
                print("  --feature-bitmap 0x03")
            else:
                print("未找到特性位定义")
        except Exception as e:
            print(f"错误: 无法读取特性位定义: {e}")
        return 0
    
    # 转储模式
    if args.dump:
        converter = YamlToBinaryConverter()
        converter.verbose = True
        try:
            converter.dump_binary(args.dump)
            return 0
        except Exception as e:
            print(f"错误: {e}", file=sys.stderr)
            return 1
    
    # 转换模式
    if not args.input or not args.output:
        parser.print_help()
        print("\n错误: 需要指定 -i/--input 和 -o/--output 参数", file=sys.stderr)
        return 1
    
    # 创建转换器（None值会使用cfg/device_config_header.h中的默认值）
    converter = YamlToBinaryConverter(
        config_version=args.config_version,
        schema_version=args.schema_version,
        feature_bitmap=args.feature_bitmap
    )
    converter.verbose = args.verbose
    
    # 如果是verbose模式，显示使用的版本信息
    if args.verbose:
        print(f"使用配置版本: {converter.header.config_version}")
        print(f"使用Schema版本: {converter.header.schema_version}")
        print(f"使用Feature Bitmap: 0x{converter.header.feature_bitmap:08X}")
        if converter.header.feature_bitmap:
            try:
                features = get_parser().decode_feature_bitmap(converter.header.feature_bitmap)
                if features:
                    print(f"启用的特性: {', '.join(features)}")
            except:
                pass
        print()
    
    try:
        converter.convert(
            args.input, 
            args.output, 
            validate=not args.no_validate
        )
        
        if not args.verbose:
            print(f"✓ 转换成功: {args.output}")
        
        return 0
    
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

