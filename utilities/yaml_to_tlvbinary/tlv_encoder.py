#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TLV编码器模块
用于将配置数据编码为Binary TLV格式
"""

import struct
from typing import Any, List, Tuple
from enum import IntEnum


class TLVType(IntEnum):
    """TLV类型定义"""
    DEVICE_BASIC = 0x01
    DEVICE_PORT_CAPABILITY = 0x02
    PORT_CONFIG = 0x10
    LD_CONFIG = 0x20
    LD_RANGE = 0x30


class TLVEncoder:
    """TLV编码器类"""
    
    def __init__(self, verbose: bool = False):
        """初始化TLV编码器
        
        Args:
            verbose: 是否输出详细日志
        """
        self.tlv_data = bytearray()
        self.verbose = verbose
    
    def encode_u8(self, value: int) -> bytes:
        """编码U8类型"""
        return struct.pack('<B', value)
    
    def encode_u16(self, value: int) -> bytes:
        """编码U16类型"""
        return struct.pack('<H', value)
    
    def encode_u32(self, value: int) -> bytes:
        """编码U32类型"""
        return struct.pack('<I', value)
    
    def encode_u64(self, value: int) -> bytes:
        """编码U64类型"""
        return struct.pack('<Q', value)
    
    def encode_bool(self, value: bool) -> bytes:
        """编码布尔类型为U8"""
        return self.encode_u8(1 if value else 0)
    
    def encode_string(self, value: str, max_len: int = 32) -> bytes:
        """编码字符串类型"""
        encoded = value.encode('utf-8')
        if len(encoded) > max_len:
            encoded = encoded[:max_len]
        # 补齐到max_len长度
        return encoded + b'\x00' * (max_len - len(encoded))
    
    def parse_size_string(self, size_str) -> int:
        """解析大小字符串 (如 "512GB", "64GB") 为字节数"""
        # 如果已经是整数，直接返回
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
        """解析十六进制字符串 (如 "0x0000_0000_0000")"""
        # 如果已经是整数，直接返回
        if isinstance(hex_str, int):
            return hex_str
        
        # 移除下划线和空格
        hex_str = str(hex_str).replace('_', '').replace(' ', '').strip()
        return int(hex_str, 16)
    
    def encode_device_basic(self, value: dict) -> bytes:
        """编码Device.Basic TLV"""
        data = bytearray()
        
        # DeviceType (字符串, 32字节)
        data.extend(self.encode_string(value.get('DeviceType', ''), 32))
        
        # HDMType (字符串, 16字节)
        data.extend(self.encode_string(value.get('HDMType', ''), 16))
        
        # TotalDRAMCapacity (U64)
        capacity = self.parse_size_string(value.get('TotalDRAMCapacity', '0'))
        data.extend(self.encode_u64(capacity))
        
        # DRAMShareable (U8)
        data.extend(self.encode_bool(value.get('DRAMShareable', False)))
        
        # 对齐到4字节
        while len(data) % 4 != 0:
            data.append(0)
        
        return bytes(data)
    
    def encode_device_port_capability(self, value: dict) -> bytes:
        """编码Device.PortCapability TLV"""
        data = bytearray()
        
        # MaxPorts (U8)
        data.extend(self.encode_u8(value.get('MaxPorts', 0)))
        
        # 对齐到4字节
        while len(data) % 4 != 0:
            data.append(0)
        
        return bytes(data)
    
    def encode_port_config(self, value: dict) -> bytes:
        """编码Port.Config TLV"""
        data = bytearray()
        
        # PortID (U8)
        data.extend(self.encode_u8(value.get('PortID', 0)))
        
        # EnablePort (U8)
        data.extend(self.encode_bool(value.get('EnablePort', False)))
        
        # PCIeSpeed (字符串映射到U8: Gen3=3, Gen4=4, Gen5=5, Gen6=6)
        speed_str = value.get('PCIeSpeed', 'Gen5')
        speed_map = {'Gen3': 3, 'Gen4': 4, 'Gen5': 5, 'Gen6': 6}
        speed = speed_map.get(speed_str, 5)
        data.extend(self.encode_u8(speed))
        
        # PCIeWidth (U8: x1=1, x2=2, x4=4, x8=8, x16=16)
        width_str = value.get('PCIeWidth', 'x16')
        if isinstance(width_str, int):
            width = width_str
        else:
            width = int(str(width_str).replace('x', ''))
        data.extend(self.encode_u8(width))
        
        # LDMode (U8: SLD=0, MLD=1)
        ld_mode = value.get('LDMode', 'SLD')
        mode_value = 1 if ld_mode == 'MLD' else 0
        data.extend(self.encode_u8(mode_value))
        
        # 对齐到4字节
        while len(data) % 4 != 0:
            data.append(0)
        
        return bytes(data)
    
    def encode_ld_config(self, value: dict) -> bytes:
        """编码LD.Config TLV"""
        data = bytearray()
        
        # PortID (U8)
        data.extend(self.encode_u8(value.get('PortID', 0)))
        
        # LDID (U8)
        data.extend(self.encode_u8(value.get('LDID', 0)))
        
        # LDType (U8: FM-LD=0, Regular-LD=1)
        ld_type = value.get('LDType', 'Regular-LD')
        type_value = 0 if ld_type == 'FM-LD' else 1
        data.extend(self.encode_u8(type_value))
        
        # DOE (U8)
        data.extend(self.encode_bool(value.get('DOE', False)))
        
        # SecurityDOE (U8)
        data.extend(self.encode_bool(value.get('SecurityDOE', False)))
        
        # Mailbox (U8)
        data.extend(self.encode_bool(value.get('Mailbox', False)))
        
        # 对齐到4字节
        while len(data) % 4 != 0:
            data.append(0)
        
        return bytes(data)
    
    def encode_ld_range(self, value: dict) -> bytes:
        """编码LD.Range TLV"""
        data = bytearray()
        
        # PortID (U8)
        data.extend(self.encode_u8(value.get('PortID', 0)))
        
        # LDID (U8)
        data.extend(self.encode_u8(value.get('LDID', 0)))
        
        # RangeID (U8)
        data.extend(self.encode_u8(value.get('RangeID', 0)))
        
        # 填充1字节对齐
        data.append(0)
        
        # Start_DPA (U64)
        start_dpa = self.parse_hex_string(value.get('Start_DPA', '0x0'))
        data.extend(self.encode_u64(start_dpa))
        
        # Length (U64)
        length = self.parse_size_string(value.get('Length', '0'))
        data.extend(self.encode_u64(length))
        
        # DCD_Supported (U8)
        data.extend(self.encode_bool(value.get('DCD_Supported', False)))
        
        # ShareModeEnable (U8)
        data.extend(self.encode_bool(value.get('ShareModeEnable', False)))
        
        # 对齐到4字节
        while len(data) % 4 != 0:
            data.append(0)
        
        return bytes(data)
    
    def encode_tlv(self, tlv_type: int, value_data: bytes, enable: bool = True) -> bytes:
        """编码单个TLV结构
        
        TLV格式:
        - Type (U8): 1字节
        - Enable (U8): 1字节 (0=禁用, 1=启用)
        - Length (U16): 2字节 (Value的长度)
        - Value (可变长度)
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
        """编码单个配置项"""
        tlv_type_str = config_item.get('Type', '')
        value = config_item.get('Value', {})
        enable = config_item.get('Enable', True)  # 获取Enable状态
        
        # 如果verbose模式，打印TLV信息
        if self.verbose:
            enable_str = '启用' if enable else '禁用'
            print(f"编码TLV: {tlv_type_str} (Enable={enable_str})")
            for key, val in value.items():
                print(f"  {key}: {val}")
        
        # 根据类型选择编码方法
        type_map = {
            'Device.Basic': (TLVType.DEVICE_BASIC, self.encode_device_basic),
            'Device.PortCapability': (TLVType.DEVICE_PORT_CAPABILITY, self.encode_device_port_capability),
            'Port.Config': (TLVType.PORT_CONFIG, self.encode_port_config),
            'LD.Config': (TLVType.LD_CONFIG, self.encode_ld_config),
            'LD.Range': (TLVType.LD_RANGE, self.encode_ld_range),
        }
        
        if tlv_type_str not in type_map:
            raise ValueError(f"Unknown TLV type: {tlv_type_str}")
        
        tlv_type, encoder_func = type_map[tlv_type_str]
        value_data = encoder_func(value)
        
        tlv_data = self.encode_tlv(tlv_type, value_data, enable)  # 传递enable参数
        
        # 如果verbose模式，打印TLV大小信息
        if self.verbose:
            enable_val = 1 if enable else 0
            print(f"  → TLV大小: {len(tlv_data)}字节 (Type=0x{tlv_type:02X}, Enable={enable_val}, Length={len(value_data)})")
        
        return tlv_data
    
    def encode_config_list(self, config_list: List[dict]) -> bytes:
        """编码配置列表
        
        注意：所有配置项都会被编码，Enable字段会反映在TLV的Enable字段中
        """
        data = bytearray()
        
        if self.verbose:
            print(f"\n开始编码 {len(config_list)} 个配置项...")
            print("=" * 70)
        
        for i, config_item in enumerate(config_list):
            if self.verbose:
                print(f"\n[{i+1}/{len(config_list)}] ", end="")
            
            # 编码所有配置项，无论Enable是true还是false
            tlv_data = self.encode_config_item(config_item)
            data.extend(tlv_data)
        
        if self.verbose:
            print("\n" + "=" * 70)
        
        return bytes(data)

