#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Binary Header模块
用于生成和管理Binary TLV文件的头部信息

注意：默认版本号和特性位图定义来自 cfg/device_config_header.h
"""

import struct
import zlib
from typing import Tuple, Optional

try:
    from header_config_parser import get_parser
    _header_parser = get_parser()
    _CONFIG_VERSION_DEFAULT = _header_parser.get_config_version()
    _SCHEMA_VERSION_DEFAULT = _header_parser.get_schema_version()
    _FEATURE_BITMAP_DEFAULT = _header_parser.get_feature_bitmap_default()
except Exception as e:
    # 如果无法加载配置文件，使用硬编码的默认值
    print(f"Warning: Cannot load header config, using hardcoded defaults: {e}")
    _CONFIG_VERSION_DEFAULT = 1
    _SCHEMA_VERSION_DEFAULT = 1
    _FEATURE_BITMAP_DEFAULT = 0
    _header_parser = None


class BinaryHeader:
    """Binary Header类
    
    Header结构 (32字节对齐):
    - config_version (U16): 配置版本号
    - schema_version (U16): Schema版本号
    - feature_bitmap (U32): 特性位图
    - length (U32): 数据长度(不包含header)
    - reserved (16字节): 保留字段
    - crc32 (U32): CRC32校验和(整个文件包括header,但crc32字段本身为0)
    
    总共: 2 + 2 + 4 + 4 + 16 + 4 = 32字节
    
    注意：
    - 默认值定义在 cfg/device_config_header.h 中
    - Feature bitmap位定义请参考该头文件
    """
    
    HEADER_SIZE = 32
    MAGIC_NUMBER = 0xDEADBEEF  # 可选的魔数，用于识别文件格式
    
    def __init__(self, config_version: Optional[int] = None, 
                 schema_version: Optional[int] = None, 
                 feature_bitmap: Optional[int] = None):
        """初始化Header
        
        Args:
            config_version: 配置版本号 (U16)，None则使用cfg/device_config_header.h中的默认值
            schema_version: Schema版本号 (U16)，None则使用cfg/device_config_header.h中的默认值
            feature_bitmap: 特性位图 (U32)，None则使用cfg/device_config_header.h中的默认值
        """
        self.config_version = config_version if config_version is not None else _CONFIG_VERSION_DEFAULT
        self.schema_version = schema_version if schema_version is not None else _SCHEMA_VERSION_DEFAULT
        self.feature_bitmap = feature_bitmap if feature_bitmap is not None else _FEATURE_BITMAP_DEFAULT
        self.length = 0
        self.crc32 = 0
    
    def pack(self, data_length: int) -> bytes:
        """打包Header(不包含CRC32)
        
        Args:
            data_length: 数据部分的长度
            
        Returns:
            打包后的header字节数据(crc32字段为0)
        """
        self.length = data_length
        
        header = bytearray()
        
        # config_version (U16)
        header.extend(struct.pack('<H', self.config_version))
        
        # schema_version (U16)
        header.extend(struct.pack('<H', self.schema_version))
        
        # feature_bitmap (U32)
        header.extend(struct.pack('<I', self.feature_bitmap))
        
        # length (U32)
        header.extend(struct.pack('<I', self.length))
        
        # reserved (16字节)
        header.extend(b'\x00' * 16)
        
        # crc32 (U32) - 先填充0
        header.extend(struct.pack('<I', 0))
        
        assert len(header) == self.HEADER_SIZE, \
            f"Header size mismatch: {len(header)} != {self.HEADER_SIZE}"
        
        return bytes(header)
    
    def calculate_crc32(self, header_without_crc: bytes, data: bytes) -> int:
        """计算CRC32校验和
        
        Args:
            header_without_crc: Header数据(crc32字段为0)
            data: 数据部分
            
        Returns:
            CRC32校验和
        """
        # 计算整个文件的CRC32(header中crc32字段为0)
        full_data = header_without_crc + data
        return zlib.crc32(full_data) & 0xFFFFFFFF
    
    def pack_with_crc(self, data: bytes) -> bytes:
        """打包完整的Header(包含CRC32)
        
        Args:
            data: 数据部分
            
        Returns:
            完整的header字节数据(包含crc32)
        """
        # 先打包header(crc32为0)
        header_without_crc = self.pack(len(data))
        
        # 计算CRC32
        self.crc32 = self.calculate_crc32(header_without_crc, data)
        
        # 更新header中的crc32字段
        header = bytearray(header_without_crc)
        header[-4:] = struct.pack('<I', self.crc32)
        
        return bytes(header)
    
    @classmethod
    def unpack(cls, header_data: bytes) -> 'BinaryHeader':
        """解包Header
        
        Args:
            header_data: Header字节数据
            
        Returns:
            BinaryHeader对象
        """
        if len(header_data) < cls.HEADER_SIZE:
            raise ValueError(f"Header data too short: {len(header_data)} < {cls.HEADER_SIZE}")
        
        # 解析各字段
        config_version = struct.unpack('<H', header_data[0:2])[0]
        schema_version = struct.unpack('<H', header_data[2:4])[0]
        feature_bitmap = struct.unpack('<I', header_data[4:8])[0]
        length = struct.unpack('<I', header_data[8:12])[0]
        crc32 = struct.unpack('<I', header_data[28:32])[0]
        
        header = cls(config_version, schema_version, feature_bitmap)
        header.length = length
        header.crc32 = crc32
        
        return header
    
    def verify_crc32(self, header_data: bytes, data: bytes) -> bool:
        """验证CRC32校验和
        
        Args:
            header_data: 完整的header数据(包含crc32)
            data: 数据部分
            
        Returns:
            True if CRC32 matches, False otherwise
        """
        # 提取存储的CRC32
        stored_crc32 = struct.unpack('<I', header_data[28:32])[0]
        
        # 创建crc32字段为0的header
        header_without_crc = bytearray(header_data)
        header_without_crc[28:32] = b'\x00\x00\x00\x00'
        
        # 计算CRC32
        calculated_crc32 = self.calculate_crc32(bytes(header_without_crc), data)
        
        return stored_crc32 == calculated_crc32
    
    def __str__(self) -> str:
        """返回Header的字符串表示"""
        result = (f"BinaryHeader(\n"
                f"  config_version=0x{self.config_version:04X},\n"
                f"  schema_version=0x{self.schema_version:04X},\n"
                f"  feature_bitmap=0x{self.feature_bitmap:08X},\n"
                f"  length={self.length},\n"
                f"  crc32=0x{self.crc32:08X}\n"
                f")")
        
        # 如果可以解析特性位图，添加特性信息
        if _header_parser and self.feature_bitmap:
            features = _header_parser.decode_feature_bitmap(self.feature_bitmap)
            if features:
                result += f"\n  Enabled features: {', '.join(features)}"
        
        return result

