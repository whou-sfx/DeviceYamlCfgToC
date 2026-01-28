# YAML配置文件转Binary TLV工具

这是一个将YAML配置文件转换为可刷写到NorFlash的Binary TLV（Type-Length-Value）格式的Python工具。

## 功能特性

- ✅ 支持将YAML配置转换为Binary TLV格式
- ✅ 32字节对齐的Header结构，包含版本信息、长度和CRC32校验
- ✅ 配置定义集中管理在C头文件（`cfg/device_config_header.h`）
- ✅ Python工具和固件C代码共享配置定义
- ✅ 自动类型推断（U8, U16, U32, U64）
- ✅ 配置验证功能
- ✅ 支持多种TLV类型（Device.Basic, Port.Config, LD.Config等）
- ✅ Feature Bitmap自动检测（根据配置内容自动设置特性位）
- ✅ Feature Bitmap手动覆盖支持（Dual-Port, MLD, DCD等）
- ✅ 二进制文件转储功能（用于调试）
- ✅ Schema驱动的TLV编码（易于扩展和维护）

## 目录结构

```
utilities/yaml_to_tlvbinary/
├── yaml_to_binary.py           # 主转换脚本
├── schema_driven_encoder.py    # Schema驱动的TLV编码器（推荐）
├── tlv_encoder.py              # 传统TLV编码器（已弃用）
├── binary_header.py            # Binary Header管理模块
├── config_schema.py            # 配置Schema定义和验证
├── header_config_parser.py     # C头文件解析器
├── feature_detector.py         # Feature Bitmap自动检测器
├── requirements.txt            # Python依赖
├── README.md                   # 本文档
└── FEATURE_DETECTION.md        # Feature Bitmap自动检测说明

cfg/
├── device_config_header.h      # C头文件：版本号和Feature Bitmap定义
└── tlv_schema.yaml             # TLV结构Schema定义
```

## Binary格式说明

### Header结构（32字节）

| 偏移 | 字段 | 类型 | 说明 |
|------|------|------|------|
| 0x00 | config_version | U16 | 配置版本号 |
| 0x02 | schema_version | U16 | Schema版本号 |
| 0x04 | feature_bitmap | U32 | 特性位图 |
| 0x08 | length | U32 | 数据长度（不包含header） |
| 0x0C | reserved | 16字节 | 保留字段 |
| 0x1C | crc32 | U32 | CRC32校验和 |

**总计：32字节（0x20）**

**注意**：Header的版本号和特性位图定义在 `../../cfg/device_config_header.h` 中。

### Feature Bitmap

Feature Bitmap是一个32位的位图，用于标识设备支持的特性：

| 特性名称 | 位位置 | 掩码 | 说明 |
|---------|--------|------|------|
| Dual-Port | bit0 | 0x01 | 双端口支持 |
| MLD | bit1 | 0x02 | Multi-Logical Device支持 |
| DCD | bit2 | 0x04 | Dynamic Capacity Device支持 |
| (保留) | bit3-31 | - | 保留供未来使用 |

查看所有定义的特性位：
```bash
python yaml_to_binary.py --list-features
```

### TLV结构

每个TLV条目的格式：

| 字段 | 类型 | 说明 |
|------|------|------|
| Type | U8 | TLV类型ID |
| Enable | U8 | 启用标志 (0=禁用, 1=启用) |
| Length | U16 | Value字段的长度 |
| Value | 可变 | 具体的配置数据 |

**重要说明**：
- Enable字段表示该配置项是否启用（1=启用，0=禁用）
- 所有配置项（无论YAML中Enable是true还是false）都会生成对应的TLV结构
- 固件可以根据Enable字段决定是否应用该配置
- TLV结构定义在`../../cfg/device_config_header.h`中

### 支持的TLV类型

| TLV类型 | Type ID | 说明 |
|---------|---------|------|
| Device.Basic | 0x01 | 设备基本信息 |
| Device.PortCapability | 0x02 | 设备端口能力 |
| Port.Config | 0x10 | 端口配置 |
| LD.Config | 0x20 | 逻辑设备配置 |
| LD.Range | 0x30 | 逻辑设备范围配置 |

## 安装依赖

```bash
cd utilities/yaml_to_tlvbinary
pip install -r requirements.txt
```

或者：

```bash
pip install PyYAML>=6.0
```

## 使用方法

### 列出可用特性位

```bash
python yaml_to_binary.py --list-features
```

输出示例：
```
============================================================
可用的Feature Bitmap定义 (来自cfg/device_config_header.h)
============================================================

特性名称              位位置      掩码      
------------------------------------------------------------
DUAL_PORT            bit0       0x01
MLD                  bit1       0x02
DCD                  bit2       0x04
```

### 基本转换（自动检测Feature Bitmap）

```bash
python yaml_to_binary.py -i ../../cfg/deviceCfg.yaml -o ../../output/device_config.bin
```

**默认行为**：工具会自动分析配置文件内容，检测并设置适当的 Feature Bitmap。

### 显示详细信息（包括自动检测过程）

```bash
python yaml_to_binary.py -i ../../cfg/deviceCfg.yaml -o ../../output/device_config.bin -v
```

输出示例：
```
使用配置版本: 1
使用Schema版本: 1
Feature Bitmap检测模式: 自动检测

开始自动检测 Feature Bitmap...
  ✓ Dual-Port 特性检测到 (掩码: 0x00000001)
  ✓ MLD 特性检测到 (掩码: 0x00000002)
  ✓ DCD 特性检测到 (掩码: 0x00000004)

自动检测到的 Feature Bitmap: 0x00000007
启用的特性: Dual-Port, MLD, DCD
```

### Feature Bitmap 自动检测规则

工具会根据以下规则自动检测特性：

1. **Dual-Port**: 如果有 ≥2 个 Port.Config 的 Enable=true
2. **MLD**: 如果任意一个 Port.Config 的 LDMode=LD_MODE_MLD 且 Enable=true
3. **DCD**: 如果任意一个 LD.Range 的 DCD_Supported=true 且 Enable=true

详细说明请参考 [`FEATURE_DETECTION.md`](FEATURE_DETECTION.md)

### 手动指定 Feature Bitmap（覆盖自动检测）

```bash
# 手动指定特定的Feature Bitmap
python yaml_to_binary.py -i ../../cfg/deviceCfg.yaml -o ../../output/device_config.bin \
    --feature-bitmap 0x03
```

### 禁用自动检测（使用默认值）

```bash
# 使用cfg/device_config_header.h中的默认值
python yaml_to_binary.py -i ../../cfg/deviceCfg.yaml -o ../../output/device_config.bin \
    --no-auto-detect
```

### 自定义版本号

```bash
python yaml_to_binary.py -i ../../cfg/deviceCfg.yaml -o ../../output/device_config.bin \
    --config-version 2 \
    --schema-version 3
```

**注意**：版本号默认从 `../../cfg/device_config_header.h` 读取。

### 转储二进制文件（调试）

```bash
python yaml_to_binary.py -d ../../output/device_config.bin
```

### 跳过配置验证

```bash
python yaml_to_binary.py -i ../../cfg/deviceCfg.yaml -o ../../output/device_config.bin --no-validate
```

## 命令行参数

| 参数 | 说明 |
|------|------|
| `-i, --input` | 输入YAML配置文件路径 |
| `-o, --output` | 输出二进制文件路径 |
| `-d, --dump` | 转储二进制文件内容（用于调试） |
| `-v, --verbose` | 显示详细信息（包括自动检测过程） |
| `--no-validate` | 跳过配置验证 |
| `--list-features` | 列出所有定义的特性位 |
| `--config-version` | 配置版本号（默认：从cfg/device_config_header.h读取） |
| `--schema-version` | Schema版本号（默认：从cfg/device_config_header.h读取） |
| `--feature-bitmap` | 手动指定特性位图（覆盖自动检测，支持十六进制如0xFF） |
| `--no-auto-detect` | 禁用Feature Bitmap自动检测，使用默认值 |

## YAML配置文件格式

配置文件示例：

```yaml
CXL_Type3_HDMH_Config:
  - Type: Device.Basic
    Enable: true
    Value:
      DeviceType: CXL_Type3
      HDMType: HDM-H
      TotalDRAMCapacity: 512GB
      DRAMShareable: true

  - Type: Port.Config
    Enable: true
    Value:
      PortID: 0
      EnablePort: true
      PCIeSpeed: Gen5
      PCIeWidth: x16
      LDMode: MLD
```

### 字段类型说明

- **字符串字段**：`DeviceType`, `HDMType`, `PCIeSpeed`, `PCIeWidth`, `LDMode`
- **布尔字段**：`DRAMShareable`, `EnablePort`, `DOE`, `SecurityDOE`, `Mailbox`
- **数值字段**：
  - `PortID`, `LDID`, `RangeID`, `MaxPorts` → U8
  - `TotalDRAMCapacity`, `Start_DPA`, `Length` → U64
- **容量字符串**：支持 `GB`, `MB`, `KB`, `B` 后缀（如 `512GB`）
- **十六进制地址**：支持下划线分隔（如 `0x0000_0000_0000`）

## 数据类型映射

工具会根据字段的取值范围自动选择合适的数据类型：

| 字段类型 | 二进制类型 | 大小 |
|----------|-----------|------|
| 小整数（0-255） | U8 | 1字节 |
| 中整数（0-65535） | U16 | 2字节 |
| 大整数（0-4G） | U32 | 4字节 |
| 超大整数/地址 | U64 | 8字节 |
| 布尔值 | U8 | 1字节（0或1） |
| 字符串 | 定长字符串 | 固定大小 |

## 代码模块说明

### yaml_to_binary.py

主转换脚本，提供命令行接口和转换流程控制。

主要类：
- `YamlToBinaryConverter`: 转换器主类

### tlv_encoder.py

TLV编码器核心模块，负责将配置数据编码为TLV格式。

主要类：
- `TLVEncoder`: TLV编码器
- `TLVType`: TLV类型枚举

主要方法：
- `encode_u8/u16/u32/u64()`: 基本类型编码
- `encode_device_basic()`: 编码Device.Basic
- `encode_port_config()`: 编码Port.Config
- `encode_ld_config()`: 编码LD.Config
- `encode_ld_range()`: 编码LD.Range

### binary_header.py

Binary Header管理模块，负责生成和解析文件头。

主要类：
- `BinaryHeader`: Header管理类

主要方法：
- `pack()`: 打包Header（不含CRC32）
- `pack_with_crc()`: 打包完整Header（含CRC32）
- `calculate_crc32()`: 计算CRC32校验和
- `verify_crc32()`: 验证CRC32校验和
- `unpack()`: 解析Header

### config_schema.py

配置Schema定义和验证模块。

主要类：
- `DataType`: 数据类型枚举
- `FieldType`: 字段类型定义
- `ConfigSchema`: Schema定义和验证

主要方法：
- `validate_config_item()`: 验证单个配置项
- `validate_config_list()`: 验证配置列表

### header_config_parser.py

C头文件解析器模块，负责解析 `cfg/device_config_header.h`。

主要类：
- `HeaderConfigParser`: C头文件解析器

主要方法：
- `get_config_version()`: 获取默认配置版本号
- `get_schema_version()`: 获取默认Schema版本号
- `get_feature_bitmap_default()`: 获取默认Feature Bitmap
- `get_feature_bit(name)`: 获取特性位位置
- `get_feature_mask(name)`: 获取特性位掩码
- `list_features()`: 列出所有定义的特性
- `create_feature_bitmap(*names)`: 创建Feature Bitmap
- `decode_feature_bitmap(bitmap)`: 解码Feature Bitmap
- `get_enum_value(enum_type, name)`: 获取枚举值

便捷函数：
- `get_config_version()`: 获取默认配置版本号
- `get_schema_version()`: 获取默认Schema版本号
- `list_features()`: 列出所有特性

### feature_detector.py

Feature Bitmap 自动检测模块，根据配置文件内容自动分析并设置特性位。

主要类：
- `FeatureDetector`: Feature Bitmap自动检测器

主要方法：
- `detect_features(config_list, verbose)`: 检测配置中的特性
- `get_feature_names(bitmap)`: 根据bitmap获取特性名称列表
- `_detect_dual_port(config_list)`: 检测Dual-Port特性
- `_detect_mld(config_list)`: 检测MLD特性
- `_detect_dcd(config_list)`: 检测DCD特性

检测规则：
1. **Dual-Port**: 有 ≥2 个 Port.Config 的 Enable=true
2. **MLD**: 任意 Port.Config 的 LDMode=LD_MODE_MLD 且 Enable=true
3. **DCD**: 任意 LD.Range 的 DCD_Supported=true 且 Enable=true

详细说明请参考 [`FEATURE_DETECTION.md`](FEATURE_DETECTION.md)

### schema_driven_encoder.py

Schema驱动的TLV编码器，基于 `cfg/tlv_schema.yaml` 定义的结构进行编码。

主要类：
- `SchemaDrivenEncoder`: Schema驱动的编码器

主要方法：
- `encode_config_list(config_list)`: 编码配置列表
- `encode_config_item(item)`: 编码单个配置项
- `encode_field(value, field_def)`: 编码字段
- `parse_enum(value, enum_type)`: 解析枚举值

优势：
- 无需硬编码TLV结构
- 易于添加新的TLV类型
- 支持复杂的字段类型和解析器
- 自动处理对齐和填充

## 示例输出

### 转换成功

```
✓ 成功加载YAML文件: cfg/deviceCfg.yaml
✓ 提取到 13 个配置项
✓ 配置验证通过
正在编码TLV数据...
✓ TLV数据编码完成，大小: 512 字节
正在生成Header...
✓ Header生成完成
BinaryHeader(
  config_version=0x0001,
  schema_version=0x0001,
  feature_bitmap=0x00000000,
  length=512,
  crc32=0x12345678
)
✓ 成功写入输出文件: output/device_config.bin
  - Header大小: 32 字节
  - TLV数据大小: 512 字节
  - 总大小: 544 字节
```

### 转储二进制文件

```
============================================================
Binary TLV文件信息
============================================================
BinaryHeader(
  config_version=0x0001,
  schema_version=0x0001,
  feature_bitmap=0x00000000,
  length=512,
  crc32=0x12345678
)

TLV数据大小: 512 字节
CRC32验证: 通过 ✓

前256字节的十六进制转储:
------------------------------------------------------------
00000000  01 00 01 00 00 00 00 00  00 02 00 00 00 00 00 00  ................
00000010  00 00 00 00 00 00 00 00  00 00 00 00 78 56 34 12  ............xV4.
...
```

## 开发和扩展

### 添加新的TLV类型

1. 在 `tlv_encoder.py` 中添加新的 `TLVType` 枚举值
2. 在 `TLVEncoder` 类中添加对应的编码方法
3. 在 `config_schema.py` 中定义新类型的Schema
4. 更新 `TYPE_SCHEMA_MAP` 映射

### 添加新的Feature Bit

1. 在 `../../cfg/device_config_header.h` 中添加新的特性位定义
2. 更新文档说明新特性的用途
3. Python工具会自动识别新定义的特性位

示例：
```c
/* 在 cfg/device_config_header.h 中添加 */
#define FEATURE_BIT_NEW_FEATURE   3   /**< 新特性位 (bit3) */
#define FEATURE_MASK_NEW_FEATURE  (1U << FEATURE_BIT_NEW_FEATURE)  /**< 0x08 */
```

### 修改Header结构

如需修改Header结构：

1. 编辑 `../../cfg/device_config_header.h` 中的结构定义
2. 更新 `binary_header.py` 中的 `BinaryHeader` 类
3. 保持32字节对齐
4. CRC32必须放在最后
5. 更新 `pack()` 和 `unpack()` 方法

## 配置文件说明

### device_config_header.h

`../../cfg/device_config_header.h` 是C头文件，定义了Binary TLV文件的Header结构和配置常量：

- **版本号定义**：`CONFIG_VERSION_DEFAULT`、`SCHEMA_VERSION_DEFAULT`
- **Feature Bitmap位定义**：`FEATURE_BIT_*`、`FEATURE_MASK_*`
- **Header结构体**：`binary_tlv_header_t`（可用于固件C代码）
- **TLV Entry结构体**：`tlv_entry_t`（可用于固件C代码）
- **辅助宏**：`TLV_ENABLE_ENABLED`、`TLV_ENABLE_DISABLED`等

**优势**：
- Python工具和固件C代码共享同一份配置定义
- 修改配置只需更新头文件，无需修改代码
- 便于版本控制和维护

### tlv_schema.yaml

`../../cfg/tlv_schema.yaml` 是TLV结构的Schema定义文件，用于Schema驱动编码器：

- **TLV类型定义**：所有支持的TLV类型（Device.Basic、Port.Config等）
- **字段定义**：每个TLV类型的字段列表（名称、类型、大小）
- **类型ID映射**：TLV类型名称到type_id的映射
- **特殊解析器**：size_string、hex_string等
- **对齐要求**：每个TLV类型的对齐设置

**优势**：
- 添加新TLV类型无需修改Python代码，只需编辑YAML配置
- 结构定义清晰，易于维护和扩展
- 自动生成编码逻辑，减少代码重复
- 降低出错风险，提高开发效率

### Schema驱动编码器

从版本2.0开始，工具使用Schema驱动的编码器（`schema_driven_encoder.py`）：

**工作原理**：
1. 从 `tlv_schema.yaml` 读取TLV结构定义
2. 根据Schema自动生成编码逻辑
3. 无需为每种TLV类型编写专门的编码方法

**添加新TLV类型的步骤**：
1. 在 `../../cfg/tlv_schema.yaml` 中添加新的TLV类型定义
2. 指定type_id（确保不与现有类型冲突）
3. 定义字段列表（name、type、size等）
4. 无需修改Python代码，编码器会自动识别

**示例**：添加新的TLV类型
```yaml
TLV_Schemas:
  MyNew.Type:
    type_id: 0x40
    description: "我的新TLV类型"
    fields:
      - name: MyField1
        type: u32
        description: "字段1"
      - name: MyField2
        type: string
        size: 16
        description: "字段2"
    alignment: 4
```

**传统编码器**：
- `tlv_encoder.py` 是传统的硬编码编码器（已弃用）
- 仅用于向后兼容，不建议新项目使用
- 添加新TLV类型需要修改Python代码

## 注意事项

1. **字节序**：所有多字节整数使用小端序（Little-Endian）
2. **对齐**：TLV Value部分自动对齐到4字节边界
3. **CRC32**：计算时Header中的CRC32字段设为0
4. **Enable字段**：所有配置项都会被编码，Enable字段反映YAML中的Enable值（1=启用，0=禁用）
5. **字符串编码**：使用UTF-8编码，定长，不足部分用0填充
6. **配置定义**：版本号、特性位图和TLV结构定义在`../../cfg/device_config_header.h`中
7. **固件兼容**：固件可以根据TLV的Enable字段决定是否应用该配置

## 故障排查

### 问题：ImportError: No module named 'yaml'

**解决**：安装PyYAML
```bash
pip install PyYAML
```

### 问题：配置验证失败

**解决**：检查YAML文件中的字段名和类型是否正确，或使用 `--no-validate` 跳过验证

### 问题：CRC32验证失败

**解决**：文件可能已损坏，请重新生成

## 许可证

本工具为项目内部使用工具，请遵循项目许可证。

## 联系方式

如有问题或建议，请联系项目维护者。

