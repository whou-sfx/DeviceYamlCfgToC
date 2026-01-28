# 更新日志

## [2.0.0] - 2026-01-28

### 新增功能

#### Schema驱动的TLV编码器
- ✅ 实现了基于YAML配置的通用TLV编码系统
- ✅ 添加 `cfg/tlv_schema.yaml` 文件定义所有TLV结构
- ✅ 创建 `schema_driven_encoder.py` 实现通用编码逻辑
- ✅ 支持通过配置文件添加新TLV类型，无需修改代码

#### 详细日志输出
- ✅ 添加 `-v/--verbose` 选项支持详细日志
- ✅ 显示每个TLV项的类型、Enable状态、属性值
- ✅ 显示TLV数据长度和编码进度
- ✅ 便于调试和验证编码过程

#### 配置集中管理
- ✅ 创建 `cfg/device_config_header.h` 集中定义版本号和Feature Bitmap
- ✅ Python工具和固件C代码共享同一份配置定义
- ✅ 添加 `header_config_parser.py` 解析C头文件
- ✅ 自动从头文件读取默认配置值

#### Enable字段支持
- ✅ TLV结构中的Reserved字段替换为Enable字段
- ✅ 所有配置项都会被编码，Enable字段反映启用状态
- ✅ 固件可根据Enable字段决定是否应用配置
- ✅ 支持动态启用/禁用配置项

### 改进

#### 代码结构
- ✅ 分离编码逻辑和Schema定义
- ✅ 提高代码可维护性和可扩展性
- ✅ 减少代码重复，降低出错风险

#### 文档
- ✅ 更新主README文档
- ✅ 更新工具README文档
- ✅ 添加Schema使用指南（SCHEMA_USAGE.md）
- ✅ 添加测试脚本和示例

#### 测试
- ✅ 创建 `test_schema_encoder.py` 测试脚本
- ✅ 验证Schema驱动编码器功能
- ✅ 确保生成的二进制文件与原版本一致

### 文件变更

#### 新增文件
- `cfg/tlv_schema.yaml` - TLV结构Schema定义
- `cfg/device_config_header.h` - C头文件配置定义
- `utilities/yaml_to_tlvbinary/schema_driven_encoder.py` - Schema驱动编码器
- `utilities/yaml_to_tlvbinary/header_config_parser.py` - C头文件解析器
- `utilities/yaml_to_tlvbinary/test_schema_encoder.py` - 测试脚本
- `utilities/yaml_to_tlvbinary/SCHEMA_USAGE.md` - Schema使用指南
- `CHANGELOG.md` - 本文档

#### 修改文件
- `utilities/yaml_to_tlvbinary/yaml_to_binary.py` - 使用Schema驱动编码器
- `utilities/yaml_to_tlvbinary/binary_header.py` - 从C头文件读取默认值
- `utilities/yaml_to_tlvbinary/tlv_encoder.py` - 添加verbose支持（已弃用）
- `utilities/yaml_to_tlvbinary/README.md` - 更新文档
- `README.md` - 更新项目文档

#### 弃用文件
- `utilities/yaml_to_tlvbinary/tlv_encoder.py` - 传统硬编码编码器（保留用于向后兼容）

### 技术细节

#### TLV结构变更
```
旧格式:
- Type (U8)
- Reserved (U8)  ← 已替换
- Length (U16)
- Value (可变)

新格式:
- Type (U8)
- Enable (U8)    ← 新增
- Length (U16)
- Value (可变)
```

#### Schema驱动编码流程
```
1. 读取 cfg/tlv_schema.yaml
2. 解析TLV类型定义
3. 根据Schema自动生成编码逻辑
4. 编码YAML配置项
5. 生成二进制TLV数据
```

#### 配置共享机制
```
cfg/device_config_header.h
    ↓
header_config_parser.py (Python)
    ↓
binary_header.py / schema_driven_encoder.py
    ↓
生成的二进制文件
    ↓
固件C代码 (使用同一个.h文件)
```

### 向后兼容性

- ✅ 保留了传统的 `tlv_encoder.py`，现有代码仍可使用
- ✅ 命令行接口保持不变
- ✅ 生成的二进制格式与之前版本兼容（除Enable字段）
- ⚠️ Enable字段的引入需要固件代码相应更新

### 升级指南

#### 从1.x升级到2.0

1. **无需修改现有YAML配置**：
   - 现有的 `cfg/deviceCfg.yaml` 可直接使用
   - Enable字段默认为true

2. **固件代码更新**：
   - 包含 `cfg/device_config_header.h`
   - 使用 `tlv_entry_t` 结构解析TLV
   - 检查 `enable` 字段决定是否应用配置

3. **添加新TLV类型**：
   - 编辑 `cfg/tlv_schema.yaml` 添加定义
   - 无需修改Python代码

### 性能

- 编码速度：与1.x版本相当
- 内存占用：略有增加（加载Schema定义）
- 二进制文件大小：与1.x版本相同

### 已知问题

- 无

### 未来计划

- [ ] 支持条件字段（根据其他字段值决定是否编码）
- [ ] 添加更多特殊解析器（如IPv4、MAC地址等）
- [ ] 支持嵌套TLV结构
- [ ] 提供二进制文件的可视化工具
- [ ] 添加Schema版本检查和迁移工具

---

## [1.0.0] - 2026-01-27

### 初始版本

- ✅ 基本的YAML到Binary TLV转换功能
- ✅ 32字节Header结构
- ✅ CRC32校验
- ✅ 配置验证
- ✅ 二进制文件转储功能
- ✅ 支持多种TLV类型
- ✅ Feature Bitmap支持

---

## 贡献者

感谢所有为本项目做出贡献的开发者。

## 许可证

本项目为内部工具，请遵循项目许可证。

