#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Feature Bitmap 自动检测器

此模块根据配置文件内容自动检测硬件特性，生成对应的 feature_bitmap 值。

检测规则：
1. Dual-Port: 如果有 ≥2 个 Port.Config 的 Enable=true
2. MLD: 如果任意一个 Port.Config 的 LDMode=LD_MODE_MLD 且 Enable=true
3. DCD: 如果任意一个 LD.Range 的 DCD_Supported=true 且该 LD.Range 的 Enable=true

注意：此模块与配置文件结构紧密耦合，如果修改了相关 TLV 类型或字段，
需要同步更新此模块的检测逻辑。
"""

from typing import List, Dict, Tuple
from header_config_parser import HeaderConfigParser


class FeatureDetector:
    """Feature Bitmap 自动检测器
    
    根据配置文件内容自动检测硬件特性，生成对应的 feature_bitmap 值。
    """
    
    def __init__(self, header_parser=None):
        """初始化检测器
        
        Args:
            header_parser: HeaderConfigParser 实例，如果为 None 则创建新实例
        """
        self.header_parser = header_parser or HeaderConfigParser()
        
    def detect_features(self, config_list: List[dict], verbose: bool = False) -> Tuple[int, Dict[str, bool]]:
        """检测配置中的特性
        
        Args:
            config_list: 配置项列表，每个配置项包含 Type、Enable、Value 等字段
            verbose: 是否输出详细信息
            
        Returns:
            (feature_bitmap, detection_results) 元组
            - feature_bitmap: 检测到的 feature bitmap 值
            - detection_results: 各特性的检测结果字典
        """
        results = {}
        bitmap = 0
        
        # 检测 Dual-Port
        dual_port_detected = self._detect_dual_port(config_list)
        results['Dual-Port'] = dual_port_detected
        if dual_port_detected:
            mask = self.header_parser.get('FEATURE_MASK_DUAL_PORT')
            bitmap |= mask
            if verbose:
                print(f"  ✓ Dual-Port 特性检测到 (掩码: 0x{mask:08X})")
        elif verbose:
            print(f"  ✗ Dual-Port 特性未检测到")
        
        # 检测 MLD
        mld_detected = self._detect_mld(config_list)
        results['MLD'] = mld_detected
        if mld_detected:
            mask = self.header_parser.get('FEATURE_MASK_MLD')
            bitmap |= mask
            if verbose:
                print(f"  ✓ MLD 特性检测到 (掩码: 0x{mask:08X})")
        elif verbose:
            print(f"  ✗ MLD 特性未检测到")
        
        # 检测 DCD
        dcd_detected = self._detect_dcd(config_list)
        results['DCD'] = dcd_detected
        if dcd_detected:
            mask = self.header_parser.get('FEATURE_MASK_DCD')
            bitmap |= mask
            if verbose:
                print(f"  ✓ DCD 特性检测到 (掩码: 0x{mask:08X})")
        elif verbose:
            print(f"  ✗ DCD 特性未检测到")
        
        return bitmap, results
    
    def _detect_dual_port(self, config_list: List[dict]) -> bool:
        """检测是否启用双端口
        
        规则：有 ≥2 个 Port.Config 且 Enable=true
        
        Args:
            config_list: 配置项列表
            
        Returns:
            True 如果检测到双端口特性，否则 False
        """
        enabled_ports = [
            item for item in config_list
            if item.get('Type') == 'Port.Config' 
            and item.get('Enable', False)
        ]
        return len(enabled_ports) >= 2
    
    def _detect_mld(self, config_list: List[dict]) -> bool:
        """检测是否启用 MLD (Multi-Logical Device)
        
        规则：任意 Port.Config 的 LDMode=LD_MODE_MLD 且 Enable=true
        
        Args:
            config_list: 配置项列表
            
        Returns:
            True 如果检测到 MLD 特性，否则 False
        """
        for item in config_list:
            if (item.get('Type') == 'Port.Config' 
                and item.get('Enable', False)):
                ld_mode = item.get('Value', {}).get('LDMode')
                if ld_mode == 'LD_MODE_MLD':
                    return True
        return False
    
    def _detect_dcd(self, config_list: List[dict]) -> bool:
        """检测是否启用 DCD (Dynamic Capacity Device)
        
        规则：任意 LD.Range 的 DCD_Supported=true 且 Enable=true
        
        Args:
            config_list: 配置项列表
            
        Returns:
            True 如果检测到 DCD 特性，否则 False
        """
        for item in config_list:
            if (item.get('Type') == 'LD.Range' 
                and item.get('Enable', False)):
                dcd_supported = item.get('Value', {}).get('DCD_Supported')
                if dcd_supported:
                    return True
        return False
    
    def get_feature_names(self, bitmap: int) -> List[str]:
        """根据 bitmap 值获取启用的特性名称列表
        
        Args:
            bitmap: feature bitmap 值
            
        Returns:
            启用的特性名称列表
        """
        features = []
        
        dual_port_mask = self.header_parser.get('FEATURE_MASK_DUAL_PORT')
        if bitmap & dual_port_mask:
            features.append('Dual-Port')
        
        mld_mask = self.header_parser.get('FEATURE_MASK_MLD')
        if bitmap & mld_mask:
            features.append('MLD')
        
        dcd_mask = self.header_parser.get('FEATURE_MASK_DCD')
        if bitmap & dcd_mask:
            features.append('DCD')
        
        return features


def main():
    """测试函数"""
    import yaml
    from pathlib import Path
    
    # 加载测试配置
    cfg_file = Path(__file__).parent.parent.parent / "cfg" / "deviceCfg.yaml"
    
    if not cfg_file.exists():
        print(f"配置文件不存在: {cfg_file}")
        return
    
    with open(cfg_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    config_list = data.get('CXL_Type3_HDMH_Config', [])
    
    # 创建检测器并检测特性
    detector = FeatureDetector()
    print("开始检测 Feature Bitmap...")
    print()
    
    bitmap, results = detector.detect_features(config_list, verbose=True)
    
    print()
    print(f"检测结果:")
    print(f"  Feature Bitmap: 0x{bitmap:08X}")
    print(f"  启用的特性: {', '.join(detector.get_feature_names(bitmap)) or '无'}")
    print()
    print(f"详细结果:")
    for feature, detected in results.items():
        status = "✓ 启用" if detected else "✗ 未启用"
        print(f"  {feature}: {status}")


if __name__ == '__main__':
    main()

