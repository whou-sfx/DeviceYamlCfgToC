## TLV解析代码生成与使用

本目录的C代码由Python生成器自动生成，目标是解析Binary TLV并构建语义树结构，支持字段原地修改与Header重算。

### 生成代码

```bash
cd /work/src/git/sync_code/DeviceYamlCfgToC
python -m utilities.tlv_codegen.generate_tlv_parser \
  --schema /work/src/git/sync_code/DeviceYamlCfgToC/cfg/tlv_schema.yaml \
  --output-dir /work/src/git/sync_code/DeviceYamlCfgToC/src/lib
```

生成的文件：
- `src/lib/tlv_semantic.h`
- `src/lib/tlv_parser.h`
- `src/lib/tlv_parser.c`

### 基本解析流程

1. 从Flash或文件读取Binary TLV到buffer
2. 调用 `parse_tlv_binary()` 初始化语义树
3. 通过字段描述符访问字段
4. 需要写回时，调用 `update_tlv_header()` 更新Header与CRC32

### 关键API

- `int parse_tlv_binary(device_semantic_t *sem, uint8_t *binary, uint16_t length)`
- `int semantic_read_field(const device_semantic_t *sem, const field_descriptor_t *fd, uint64_t *value)`
- `int semantic_write_field(device_semantic_t *sem, const field_descriptor_t *fd, uint64_t value)`
- `int update_tlv_header(device_semantic_t *sem)`

### 示例

参考 `src/examples/tlv_parser_example.c`，展示了读取、解析、修改与写回流程。

### 测试

`src/test/test_tlv_parser.c` 使用 `output/whou_dmld.bin` 进行解析与写回验证。

