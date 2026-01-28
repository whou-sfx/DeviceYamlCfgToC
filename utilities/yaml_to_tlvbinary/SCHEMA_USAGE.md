# Schema驱动编码器使用指南

本文档介绍如何使用Schema驱动的TLV编码器，以及如何添加新的TLV类型。

## 概述

Schema驱动编码器是一个基于配置文件的通用TLV编码系统，它通过读取 `cfg/tlv_schema.yaml` 文件来获取TLV结构定义，自动生成编码逻辑。

### 优势

- ✅ **无需修改代码**：添加新TLV类型只需编辑YAML配置文件
- ✅ **结构清晰**：所有TLV定义集中在一个文件中
- ✅ **减少错误**：自动生成编码逻辑，避免手工编码错误
- ✅ **易于维护**：修改TLV结构只需更新配置文件
- ✅ **提高效率**：大幅减少重复代码

## 快速开始

### 1. 查看支持的TLV类型

```bash
cd utilities/yaml_to_tlvbinary
python3 test_schema_encoder.py
```

### 2. 使用Schema驱动编码器

工具已经默认使用Schema驱动编码器，无需任何修改：

```bash
python3 yaml_to_binary.py -i ../../cfg/deviceCfg.yaml -o ../../output/device_config.bin
```

### 3. 验证输出

```bash
python3 yaml_to_binary.py -d ../../output/device_config.bin
```

## 添加新的TLV类型

### 步骤1：编辑Schema文件

打开 `cfg/tlv_schema.yaml`，在 `TLV_Schemas` 下添加新的类型定义：

```yaml
TLV_Schemas:
  # ... 现有类型 ...
  
  # 添加新类型
  MyNew.Type:
    type_id: 0x40                    # 选择一个未使用的type_id
    description: "我的新TLV类型"      # 类型描述
    fields:                          # 字段列表（按二进制编码顺序）
      - name: Field1                 # 字段名称
        type: u32                    # 字段类型
        description: "字段1说明"      # 字段描述
        
      - name: Field2
        type: string
        size: 16                     # string类型需要指定大小
        description: "字段2说明"
        
      - name: Field3
        type: u64
        parser: size_string          # 使用特殊解析器
        description: "容量字段"
    
    alignment: 4                     # 对齐字节数（通常为4）
```

### 步骤2：更新YAML配置文件

在 `cfg/deviceCfg.yaml` 中添加新类型的配置项：

```yaml
ConfigList:
  # ... 现有配置 ...
  
  - Type: MyNew.Type
    Enable: true
    Value:
      Field1: 12345
      Field2: "test_string"
      Field3: "1GB"
```

### 步骤3：测试

```bash
cd utilities/yaml_to_tlvbinary
python3 yaml_to_binary.py -i ../../cfg/deviceCfg.yaml -o ../../output/test.bin -v
```

就这么简单！无需修改任何Python代码。

## 字段类型说明

### 基本类型

| 类型 | 大小 | 说明 | 示例 |
|------|------|------|------|
| `u8` | 1字节 | 无符号8位整数 | `255` |
| `u16` | 2字节 | 无符号16位整数 | `65535` |
| `u32` | 4字节 | 无符号32位整数 | `4294967295` |
| `u64` | 8字节 | 无符号64位整数 | `18446744073709551615` |
| `bool` | 1字节 | 布尔值 | `true` / `false` |
| `string` | 可变 | UTF-8字符串（定长） | `"CXL_Type3"` |

### 特殊解析器

#### size_string

解析容量字符串，支持以下后缀：

- `GB`: 千兆字节（1024³）
- `MB`: 兆字节（1024²）
- `KB`: 千字节（1024）
- `B`: 字节

**示例**：
```yaml
- name: Capacity
  type: u64
  parser: size_string
```

**YAML配置**：
```yaml
Capacity: "512GB"  # 将被解析为 549755813888
```

#### hex_string

解析十六进制字符串，支持下划线分隔：

**示例**：
```yaml
- name: Address
  type: u64
  parser: hex_string
```

**YAML配置**：
```yaml
Address: "0x0000_1000_0000"  # 将被解析为 68719476736
```

#### enum

解析C头文件中定义的枚举值，自动将枚举名称映射到整数值：

**优势**：
- 节省存储空间（相比字符串类型）
- 类型安全（C固件代码可使用枚举类型）
- 避免拼写错误
- 编译时检查枚举值有效性

**步骤1**：在 `cfg/device_config_header.h` 中定义枚举类型：
```c
typedef enum {
    PCIE_SPEED_GEN1 = 1,
    PCIE_SPEED_GEN2 = 2,
    PCIE_SPEED_GEN3 = 3,
    PCIE_SPEED_GEN4 = 4,
    PCIE_SPEED_GEN5 = 5,
    PCIE_SPEED_GEN6 = 6,
} pcie_speed_t;
```

**步骤2**：在Schema中指定enum解析器：
```yaml
- name: PCIeSpeed
  type: u8
  parser: enum
  enum_type: pcie_speed_t
  description: "PCIe速度"
```

**步骤3**：在YAML配置中使用枚举名称：
```yaml
PCIeSpeed: PCIE_SPEED_GEN5  # 将被解析为整数 5，编码为1字节
```

**空间节省**：
- 字符串 "Gen5"：8字节（含padding） → 枚举值 5：1字节
- 每个字段节省 7 字节

## Schema文件结构

### 完整示例

```yaml
TLV_Schemas:
  Device.Basic:                      # TLV类型名称
    type_id: 0x01                    # TLV类型ID（1字节）
    description: "设备基本信息"       # 类型描述
    
    fields:                          # 字段列表
      - name: DeviceType             # 字段名称
        type: string                 # 字段类型
        size: 32                     # 字符串大小
        description: "设备类型"       # 字段描述
        
      - name: TotalCapacity
        type: u64                    # 64位无符号整数
        parser: size_string          # 使用size_string解析器
        description: "总容量"
        
      - name: IsEnabled
        type: bool                   # 布尔类型
        description: "是否启用"
    
    alignment: 4                     # Value部分对齐到4字节
```

### 字段定义规则

1. **必需字段**：
   - `name`: 字段名称（必须与YAML配置中的名称匹配）
   - `type`: 字段类型（u8/u16/u32/u64/bool/string）

2. **条件字段**：
   - `size`: string类型必需
   - `parser`: 需要特殊解析时指定

3. **可选字段**：
   - `description`: 字段说明

4. **字段顺序**：
   - 字段按照列表顺序进行二进制编码
   - 修改顺序会改变二进制格式

## 最佳实践

### 1. Type ID分配

建议按照功能模块分配Type ID范围：

- `0x01-0x0F`: Device级别TLV
- `0x10-0x1F`: Port级别TLV
- `0x20-0x2F`: LD级别TLV
- `0x30-0x3F`: Range级别TLV
- `0x40-0xFF`: 预留

### 2. 字段命名

- 使用PascalCase命名（如 `DeviceType`）
- 保持与YAML配置文件一致
- 避免使用Python关键字

### 3. 字符串大小

- 预留足够空间（考虑未来扩展）
- 使用2的幂次（8, 16, 32, 64）
- 保持4字节对齐

### 4. 版本控制

当修改现有TLV结构时：

1. 增加 `schema_version`（在 `cfg/device_config_header.h` 中）
2. 在Schema中添加版本注释
3. 保持向后兼容或提供迁移工具

## 高级功能

### 自定义解析器

如需添加新的解析器（如 `ipv4_string`），修改 `schema_driven_encoder.py`：

```python
def parse_ipv4_string(self, ipv4_str) -> int:
    """解析IPv4地址字符串为U32"""
    if isinstance(ipv4_str, int):
        return ipv4_str
    
    parts = ipv4_str.split('.')
    return (int(parts[0]) << 24) | (int(parts[1]) << 16) | \
           (int(parts[2]) << 8) | int(parts[3])
```

然后在 `encode_field()` 方法中添加：

```python
elif parser == 'ipv4_string':
    value = self.parse_ipv4_string(value)
```

### 条件字段

如果需要根据其他字段的值决定是否编码某个字段，可以扩展Schema格式：

```yaml
fields:
  - name: HasExtension
    type: bool
  
  - name: Extension
    type: u32
    condition: HasExtension  # 仅当HasExtension为true时编码
```

## 故障排查

### 问题1：Unknown TLV type

**原因**：Schema文件中没有定义该TLV类型

**解决**：
1. 检查 `cfg/tlv_schema.yaml` 中是否有该类型定义
2. 确认类型名称拼写正确（区分大小写）

### 问题2：字段值缺失

**原因**：YAML配置中缺少必需字段

**解决**：
1. 检查YAML配置中的字段名称
2. 查看Schema定义的所有字段
3. 缺失字段会使用默认值（数字为0，字符串为空，布尔为false）

### 问题3：二进制文件大小不符

**原因**：字段大小或对齐设置不正确

**解决**：
1. 使用 `-v` 选项查看详细编码信息
2. 检查每个字段的大小
3. 确认对齐设置为4

## 示例项目

### 示例1：添加温度监控TLV

```yaml
# cfg/tlv_schema.yaml
TLV_Schemas:
  Device.Temperature:
    type_id: 0x0F
    description: "设备温度监控配置"
    fields:
      - name: SensorCount
        type: u8
        description: "传感器数量"
      
      - name: WarningThreshold
        type: u32
        description: "警告阈值（摄氏度*100）"
      
      - name: CriticalThreshold
        type: u32
        description: "临界阈值（摄氏度*100）"
      
      - name: EnableAlert
        type: bool
        description: "启用温度告警"
    
    alignment: 4
```

```yaml
# cfg/deviceCfg.yaml
ConfigList:
  - Type: Device.Temperature
    Enable: true
    Value:
      SensorCount: 4
      WarningThreshold: 7500    # 75.00°C
      CriticalThreshold: 8500   # 85.00°C
      EnableAlert: true
```

### 示例2：添加网络配置TLV

```yaml
# cfg/tlv_schema.yaml
TLV_Schemas:
  Network.Config:
    type_id: 0x50
    description: "网络配置"
    fields:
      - name: InterfaceName
        type: string
        size: 16
        description: "网络接口名称"
      
      - name: IPAddress
        type: u32
        parser: ipv4_string
        description: "IP地址"
      
      - name: SubnetMask
        type: u32
        parser: ipv4_string
        description: "子网掩码"
      
      - name: Gateway
        type: u32
        parser: ipv4_string
        description: "网关地址"
      
      - name: EnableDHCP
        type: bool
        description: "启用DHCP"
    
    alignment: 4
```

## 参考资料

- [主README文档](../../README.md)
- [工具详细文档](README.md)
- [快速入门指南](QUICKSTART.md)
- [C头文件定义](../../cfg/device_config_header.h)
- [TLV Schema定义](../../cfg/tlv_schema.yaml)

## 联系方式

如有问题或建议，请联系项目维护者。

