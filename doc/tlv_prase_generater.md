# TLV Parse C代码自动生成方案

本文档说明如何使用Python基于 `cfg/tlv_schema.yaml` 自动生成固件侧TLV解析C代码的设计方案与关键代码demo。该方案面向平铺式TLV结构，配合 `doc/TLV_Parse_Design.md` 的解析流程设计使用，侧重“代码生成+语义结构+回写能力”的落地方式。

## 目标与约束
- 输入：包含Header的Binary TLV ByteArray。
- 输出：固件可用的C解析代码（无动态内存分配，内存占用尽量节省）。
- 语义结构采用Struct组织，成员保存字段在ByteArray中的offset，实现原地修改。
- TLV类型与枚举优先使用 `cfg/device_config_header.h` 中定义。
- 额外新增结构或枚举可单独放在生成的头文件中。

## 参考数据源
- `cfg/tlv_schema.yaml`：TLV类型与字段顺序、类型、对齐要求。
- `cfg/device_config_header.h`：Header结构、TLV类型枚举、字段枚举。
- `doc/TLV_Parse_Design.md`：解析流程与语义树映射规则（本方案沿用其语义关系）。
- `utilities/yaml_to_tlvbinary/README.md`：编码与Header格式说明。

## Python代码生成整体流程
1. 读取 `cfg/tlv_schema.yaml`，生成每个TLV类型的字段列表、类型大小与对齐规则。
2. 解析 `cfg/device_config_header.h`，抽取TLV类型ID与枚举值映射。
3. 生成C侧结构体、TLV索引结构、解析函数模板与字段offset映射。
4. 输出：
   - `generated/tlv_semantic.h`
   - `generated/tlv_parser.h`
   - `generated/tlv_parser.c`
   - 可选：`generated/tlv_offsets.h`

## C侧解析架构设计
### 解析主流程
- 解析Header并校验长度/CRC。
- 顺序扫描TLV列表，构建索引表 `tlv_index[]`。
- 根据TLV类型调用对应解析函数，挂载到语义结构。
- 语义结构内部保存字段offset，用于原地写回。

### 内存模型
- 固定容量静态数组，不使用malloc/free。
- 容量由配置定义：
  - `MAX_PORTS`、`MAX_LD_PER_PORT`、`MAX_RANGE_PER_LD`
- 仅保留必要的字段offset与状态标志，降低内存占用。

## 关键数据结构设计

### TLV索引结构
```c
typedef struct {
    uint8_t type;
    uint8_t enable;
    uint16_t length;
    uint32_t value_offset;   // Value起始偏移（相对ByteArray起始）
} tlv_index_t;
```

### 语义结构示例（Port.Config）
```c
typedef struct {
    uint8_t present;
    uint32_t tlv_value_offset;
    uint16_t tlv_length;

    // 字段offset（相对ByteArray起始）
    uint32_t off_PortID;
    uint32_t off_EnablePort;
    uint32_t off_PCIeSpeed;
    uint32_t off_PCIeWidth;
    uint32_t off_LDMode;
} port_config_node_t;

typedef struct {
    port_config_node_t port[MAX_PORTS];
    // 省略 LD / Range ...
} device_semantic_t;
```

## 关键代码demo

### 1) TLV索引构建
```c
size_t offset = sizeof(binary_tlv_header_t);
while (offset + sizeof(tlv_entry_t) <= len) {
    const tlv_entry_t* e = (const tlv_entry_t*)(buf + offset);
    uint32_t value_offset = offset + 4;

    if (*index_cnt < index_cap) {
        index[*index_cnt] = (tlv_index_t){
            .type = e->type,
            .enable = e->enable,
            .length = e->length,
            .value_offset = value_offset,
        };
        (*index_cnt)++;
    }

    uint32_t step = 4 + e->length;
    step = (step + 3) & ~3u; // 4字节对齐
    offset += step;
}
```

### 2) Port.Config字段offset映射
```c
static void map_port_config(const uint8_t* buf,
                            const tlv_index_t* idx,
                            device_semantic_t* sem)
{
    const uint8_t* v = buf + idx->value_offset;
    uint32_t base = idx->value_offset;

    uint8_t port_id = v[0];
    if (port_id < MAX_PORTS) {
        port_config_node_t* p = &sem->port[port_id];
        p->present = 1;
        p->tlv_value_offset = idx->value_offset;
        p->tlv_length = idx->length;

        p->off_PortID     = base + 0;
        p->off_EnablePort = base + 1;
        p->off_PCIeSpeed  = base + 2;
        p->off_PCIeWidth  = base + 3;
        p->off_LDMode     = base + 4;
    }
}
```

### 3) 原地写回更新字段
```c
static inline void write_u8(uint8_t* buf, uint32_t off, uint8_t v) {
    buf[off] = v;
}

void set_port_ldmode(uint8_t* buf, device_semantic_t* sem,
                     uint8_t port_id, uint8_t ldmode)
{
    port_config_node_t* p = &sem->port[port_id];
    if (!p->present) return;
    write_u8(buf, p->off_LDMode, ldmode);
}
```

## Python生成器关键逻辑示意

### 字段offset自动生成
```python
offset = 0
for field in fields:
    emit(f"p->off_{field.name} = base + {offset};")
    offset += field_size(field.type)
```

### TLV类型到处理函数映射
```python
handlers = {
    "Port.Config": "map_port_config",
    "LD.Config": "map_ld_config",
    "LD.Range": "map_ld_range",
}
```

## 生成文件组织建议
- `generated/tlv_semantic.h`：语义结构体定义、容量宏
- `generated/tlv_parser.h`：解析API与写回API声明
- `generated/tlv_parser.c`：解析与字段映射实现
- `generated/tlv_offsets.h`：字段offset宏（可选）

## 兼容性与扩展建议
- 使用 `Length` 判断字段可用范围，支持尾部新增字段。
- 不识别的TLV类型直接跳过，保证前向兼容。
- 通过 `cfg/tlv_schema.yaml` 扩展TLV类型，无需手改C逻辑。

## 与已有设计文档的关系
本方案与 `doc/TLV_Parse_Design.md` 保持一致，文档中描述的平铺TLV解析与语义映射规则仍是核心逻辑。本文件关注“自动生成C代码”的实现组织方式与关键代码模板。

