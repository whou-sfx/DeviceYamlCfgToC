# DeviceYamlCfgToC

将YAML设备配置文件转换为可刷写到NorFlash的Binary TLV格式的工具集。

## 项目结构

```
DeviceYamlCfgToC/
├── cfg/                        # 配置文件目录
│   ├── deviceCfg.yaml         # 设备YAML配置文件
│   ├── device_config_header.h # Header配置定义（C头文件）
│   └── tlv_schema.yaml        # TLV结构Schema定义
├── output/                     # 输出目录
│   └── device_config.bin      # 生成的二进制文件
├── src/                        # 源代码目录（预留）
├── utilities/                  # Python工具集
│   ├── yaml_to_tlvbinary/     # TLV转换工具包
│   │   ├── __init__.py            # Python包初始化
│   │   ├── yaml_to_binary.py      # 主转换脚本
│   │   ├── schema_driven_encoder.py # Schema驱动编码器（推荐）
│   │   ├── tlv_encoder.py         # 传统TLV编码器（已弃用）
│   │   ├── binary_header.py       # Binary Header管理
│   │   ├── config_schema.py       # 配置Schema定义
│   │   ├── header_config_parser.py # C头文件解析器
│   │   ├── requirements.txt       # Python依赖
│   │   ├── example_usage.sh       # 示例使用脚本
│   │   ├── README.md             # 详细文档
│   │   └── QUICKSTART.md         # 快速入门指南
└── README.md                  # 本文档
```

## 功能特性

✅ **YAML到Binary TLV转换**
- 支持多种TLV类型（Device.Basic, Port.Config, LD.Config, LD.Range等）
- Schema驱动编码器：通过YAML配置定义TLV结构，无需修改代码
- 枚举类型支持：自动映射C枚举到整数值，节省存储空间
- 自动类型推断和转换（U8, U16, U32, U64）
- 支持容量字符串（如"512GB"）、十六进制地址和枚举类型
- 添加新TLV类型只需编辑配置文件

✅ **32字节对齐的Header**
- 包含config_version, schema_version, feature_bitmap
- 配置定义集中管理在 `cfg/device_config_header.h`
- 自动计算数据长度
- CRC32校验和保护
- Python工具和固件C代码共享配置定义

✅ **配置验证**
- 自动验证YAML配置的完整性
- 检查必需字段
- 可选的验证跳过

✅ **调试工具**
- 二进制文件转储功能
- CRC32验证
- 十六进制查看器

## 快速开始

### 1. 安装依赖

```bash
pip install PyYAML
```

### 2. 查看可用的特性位定义

```bash
cd utilities/yaml_to_tlvbinary
python3 yaml_to_binary.py --list-features
```

### 3. 转换配置

```bash
cd utilities/yaml_to_tlvbinary
python3 yaml_to_binary.py -i ../../cfg/deviceCfg.yaml -o ../../output/device_config.bin -v
```

### 4. 验证输出

```bash
python3 yaml_to_binary.py -d ../../output/device_config.bin
```

或者使用示例脚本一键完成：

```bash
cd utilities/yaml_to_tlvbinary
bash example_usage.sh
```

## Binary格式说明

### Header结构（32字节）

```
Offset | Field           | Type | Size | Description
-------|-----------------|------|------|------------------
0x00   | config_version  | U16  | 2    | 配置版本号
0x02   | schema_version  | U16  | 2    | Schema版本号
0x04   | feature_bitmap  | U32  | 4    | 特性位图
0x08   | length          | U32  | 4    | 数据长度（不含header）
0x0C   | reserved        | -    | 16   | 保留字段
0x1C   | crc32           | U32  | 4    | CRC32校验和
```

**注意**：Header的版本号和特性位图定义在 `cfg/device_config_header.h` 中，该文件可同时用于Python工具和固件C代码。

### Feature Bitmap定义

Feature Bitmap是一个32位的位图，用于标识设备支持的特性。当前定义的特性位：

| 特性名称 | 位位置 | 掩码 | 说明 |
|---------|--------|------|------|
| Dual-Port | bit0 | 0x01 | 双端口支持 |
| MLD | bit1 | 0x02 | Multi-Logical Device支持 |
| DCD | bit2 | 0x04 | Dynamic Capacity Device支持 |
| (保留) | bit3-31 | - | 保留供未来使用 |

**默认值**：0x00（所有特性禁用）

可以通过以下命令查看所有定义的特性位：

```bash
cd utilities/yaml_to_tlvbinary
python3 yaml_to_binary.py --list-features
```

### TLV结构

```
Field    | Type | Description
---------|------|------------------
Type     | U8   | TLV类型ID
Enable   | U8   | 启用标志 (0=禁用, 1=启用)
Length   | U16  | Value字段长度
Value    | var  | 具体配置数据
```

**注意**：
- Enable字段表示该配置项是否启用（1=启用，0=禁用）
- 所有配置项（无论Enable是true还是false）都会生成对应的TLV结构
- 固件可以根据Enable字段决定是否应用该配置

### 支持的TLV类型

| TLV类型 | Type ID | 说明 |
|---------|---------|------|
| Device.Basic | 0x01 | 设备基本信息 |
| Device.PortCapability | 0x02 | 设备端口能力 |
| Port.Config | 0x10 | 端口配置 |
| LD.Config | 0x20 | 逻辑设备配置 |
| LD.Range | 0x30 | 逻辑设备范围配置 |

## 使用示例

### 基本转换

```bash
python3 utilities/yaml_to_tlvbinary/yaml_to_binary.py \
    -i cfg/deviceCfg.yaml \
    -o output/device_config.bin
```

### 带详细信息的转换

```bash
python3 utilities/yaml_to_tlvbinary/yaml_to_binary.py \
    -i cfg/deviceCfg.yaml \
    -o output/device_config.bin \
    -v
```

### 自定义版本和特性

```bash
python3 utilities/yaml_to_tlvbinary/yaml_to_binary.py \
    -i cfg/deviceCfg.yaml \
    -o output/device_config.bin \
    --config-version 2 \
    --schema-version 3 \
    --feature-bitmap 0x07
```

**注意**：如果不指定版本号和特性位图，工具会自动使用 `cfg/device_config_header.h` 中定义的默认值。

### 启用特定特性

```bash
# 启用Dual-Port特性
python3 utilities/yaml_to_tlvbinary/yaml_to_binary.py \
    -i cfg/deviceCfg.yaml \
    -o output/device_config.bin \
    --feature-bitmap 0x01

# 启用Dual-Port和MLD特性
python3 utilities/yaml_to_tlvbinary/yaml_to_binary.py \
    -i cfg/deviceCfg.yaml \
    -o output/device_config.bin \
    --feature-bitmap 0x03
```

### 转储二进制文件

```bash
python3 utilities/yaml_to_tlvbinary/yaml_to_binary.py -d output/device_config.bin
```

输出示例：

```
============================================================
Binary TLV文件信息
============================================================
BinaryHeader(
  config_version=0x0001,
  schema_version=0x0001,
  feature_bitmap=0x00000000,
  length=256,
  crc32=0xBDB1AE0A
)

TLV数据大小: 256 字节
CRC32验证: 通过 ✓
```

## YAML配置格式

配置文件示例（`cfg/deviceCfg.yaml`）：

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

### 字段类型

- **字符串**: `DeviceType`, `HDMType`, `PCIeSpeed`, `LDMode`
- **布尔值**: `DRAMShareable`, `EnablePort`, `DOE`, `Mailbox`
- **整数**: `PortID`, `LDID`, `RangeID`, `MaxPorts`
- **容量**: `TotalDRAMCapacity`, `Length` (支持GB/MB/KB/B后缀)
- **地址**: `Start_DPA` (支持十六进制，如`0x0000_0000_0000`)

## 文档

- [详细文档](utilities/README.md) - 完整的API和使用说明
- [快速入门](utilities/QUICKSTART.md) - 快速上手指南

## 开发

### 添加新的TLV类型

1. 在`utilities/yaml_to_tlvbinary/tlv_encoder.py`中添加编码方法
2. 在`utilities/yaml_to_tlvbinary/config_schema.py`中定义Schema
3. 更新文档

### 添加新的Feature Bit

1. 在`cfg/device_config_header.h`中添加新的特性位定义
2. 更新文档说明新特性的用途
3. Python工具会自动识别新定义的特性位

示例：
```c
/* 在 cfg/device_config_header.h 中添加 */
#define FEATURE_BIT_NEW_FEATURE   3   /**< 新特性位 (bit3) */
#define FEATURE_MASK_NEW_FEATURE  (1U << FEATURE_BIT_NEW_FEATURE)  /**< 0x08 */
```

### 运行测试

```bash
cd utilities/yaml_to_tlvbinary
bash example_usage.sh
```

## 技术细节

- **编程语言**: Python 3.7+
- **依赖**: PyYAML >= 6.0
- **字节序**: Little-Endian (小端序)
- **对齐**: TLV Value部分4字节对齐
- **校验**: CRC32 (zlib.crc32)

## 配置文件说明

### device_config_header.h

`cfg/device_config_header.h` 是C头文件，定义了Binary TLV文件的Header结构和配置常量：

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

`cfg/tlv_schema.yaml` 是TLV结构的Schema定义文件，用于Schema驱动编码器：

- **TLV类型定义**：所有支持的TLV类型及其结构
- **字段定义**：每个TLV类型的字段列表（名称、类型、大小）
- **类型ID映射**：TLV类型名称到type_id的映射
- **特殊解析器**：size_string、hex_string等

**添加新TLV类型**：
1. 在 `cfg/tlv_schema.yaml` 中添加新的TLV类型定义
2. 指定type_id（确保不与现有类型冲突）
3. 定义字段列表（name、type、size等）
4. 无需修改Python代码，编码器会自动识别

**示例**：
```yaml
TLV_Schemas:
  MyNew.Type:
    type_id: 0x40
    description: "我的新TLV类型"
    fields:
      - name: MyField1
        type: u32
      - name: MyField2
        type: string
        size: 16
    alignment: 4
```

## 注意事项

1. 所有多字节整数使用小端序编码
2. Header固定为32字节，必须对齐
3. CRC32计算时，Header中的CRC32字段设为0
4. 所有配置项都会被编码，Enable字段反映配置项的启用状态（1=启用，0=禁用）
5. 字符串使用UTF-8编码，定长，不足部分用0填充
6. 版本号和特性位图的默认值定义在`cfg/device_config_header.h`中
7. TLV结构定义在`cfg/device_config_header.h`中，可用于固件C代码

## U32/u64 访问对齐问题
tlv_binary中，存在一些U64/U32类型的属性对应的值，如果直接struct解析，会造成总线非对齐访问，
在EL2 CPU总线访问中必然会出发异常。当前方案不存在这种问题，解决的策略为对于U32/U64是通过逐个
字节拼接来读写的。tlv_parser.c 里可以看到对 Start_DPA/Length 都是 ((uint64_t)v[i] << ...) 的形式）
semantic_write_field() 也是按字节写回。
**所以“规避”的关键是：不要在任何地方把 TLV value 当成 packed struct 直接解引用。**


