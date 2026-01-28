# 快速入门指南

## 1. 安装依赖

```bash
pip install PyYAML
```

或者：

```bash
cd utilities
pip install -r requirements.txt
```

## 2. 基本使用

### 转换YAML配置到二进制文件

```bash
cd utilities
python3 yaml_to_binary.py -i ../cfg/deviceCfg.yaml -o ../output/device_config.bin
```

### 查看详细信息

```bash
python3 yaml_to_binary.py -i ../cfg/deviceCfg.yaml -o ../output/device_config.bin -v
```

### 转储二进制文件内容（调试）

```bash
python3 yaml_to_binary.py -d ../output/device_config.bin
```

## 3. 使用示例脚本

```bash
cd utilities
bash example_usage.sh
```

这个脚本会自动：
1. 转换YAML配置到二进制文件
2. 显示详细的转换信息
3. 转储二进制文件内容用于验证

## 4. 输出文件格式

生成的二进制文件包含：

### Header (32字节)
- `config_version` (U16): 配置版本号
- `schema_version` (U16): Schema版本号
- `feature_bitmap` (U32): 特性位图
- `length` (U32): 数据长度
- `reserved` (16字节): 保留字段
- `crc32` (U32): CRC32校验和

### TLV数据
- 多个TLV条目，每个包含：
  - `Type` (U8): TLV类型
  - `Reserved` (U8): 保留
  - `Length` (U16): Value长度
  - `Value`: 具体数据

## 5. 自定义选项

### 设置版本号

```bash
python3 yaml_to_binary.py \
    -i ../cfg/deviceCfg.yaml \
    -o ../output/device_config.bin \
    --config-version 2 \
    --schema-version 3
```

### 设置特性位图

```bash
python3 yaml_to_binary.py \
    -i ../cfg/deviceCfg.yaml \
    -o ../output/device_config.bin \
    --feature-bitmap 0xFF
```

### 跳过验证

```bash
python3 yaml_to_binary.py \
    -i ../cfg/deviceCfg.yaml \
    -o ../output/device_config.bin \
    --no-validate
```

## 6. 验证输出

使用hexdump查看生成的二进制文件：

```bash
hexdump -C ../output/device_config.bin | head -20
```

或使用内置的转储功能：

```bash
python3 yaml_to_binary.py -d ../output/device_config.bin
```

## 7. 刷写到NorFlash

生成的二进制文件可以直接刷写到NorFlash：

```bash
# 示例（具体命令取决于你的硬件和工具）
flashrom -p <programmer> -w ../output/device_config.bin
```

或者使用你的设备特定的刷写工具。

## 常见问题

### Q: 如何修改YAML配置？

A: 编辑 `cfg/deviceCfg.yaml` 文件，确保保持正确的格式和字段名。

### Q: 如何添加新的TLV类型？

A: 需要修改以下文件：
1. `tlv_encoder.py` - 添加编码方法
2. `config_schema.py` - 添加Schema定义

### Q: CRC32验证失败怎么办？

A: 重新生成二进制文件，如果问题持续，可能是文件在传输过程中损坏。

### Q: 支持哪些数据类型？

A: U8, U16, U32, U64, 布尔值, 字符串, 容量字符串(如"512GB"), 十六进制地址

## 更多信息

详细文档请参考 [README.md](README.md)

