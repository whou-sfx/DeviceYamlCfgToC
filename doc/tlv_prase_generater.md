# TLV Parse C代码自动生成方案

本文档说明如何使用Python基于 `cfg/tlv_schema.yaml` 自动生成固件侧TLV解析C代码的设计方案与关键代码demo。该方案面向平铺式TLV结构，配合 `doc/TLV_Parse_Design.md` 的解析流程设计使用，侧重“代码生成+语义结构+回写能力”的落地方式。

## 目标与约束
- 输入：包含Header的Binary TLV ByteArray。
- 输出：固件可用的C解析代码（无动态内存分配，内存占用尽量节省）。
- 语义结构采用Struct组织, 按照语义组成树形结构，成员值有当前值和保存字段在ByteArray中的offset，实现BinaryTLV BinaryArray的修改。
- 语义结构中的MAX_PORTS, MAX_REGULAR_LD, MAX_FM_LD, MAX_RANGE_PER_REGULAR_LD的定义通过  `cfg/device_config_header.h` 中定义
- TLV类型与枚举优先使用 `cfg/device_config_header.h` 中定义。
- 语义定义的树形结构，单独用一个.c/.h文件存放，用于Firmware使用配置的接口文件, 其他的firmware只要引用该该文件就可以访问当前的配置
- 额外新增结构或枚举可单独放在生成的头文件中。

## 参考数据源
- `cfg/tlv_schema.yaml`：TLV类型与字段顺序、类型、对齐要求。
- `cfg/device_config_header.h`：Header结构、TLV类型枚举、字段枚举、最大资源定义。
- `doc/tlv_codegen_target.md`： 根据binaryTLV构建的目标语义树映树的实现说明。
 `utilities/yaml_to_tlvbinary/README.md`：编码与Header格式说明。

## Python代码生成整体流程
1. 读取 `cfg/tlv_schema.yaml`，生成每个TLV类型的字段列表、类型大小与对齐规则。
2. 解析 `cfg/device_config_header.h`，抽取TLV类型ID与枚举值映射。
3. 以 `doc/tlv_codegen_target.md` 目标构建的结构，解析binaryTLV结构，初始化目标结构
4. 输出：
   - `generated/tlv_semantic.h`
   - `generated/tlv_parser.h`
   - `generated/tlv_parser.c`

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


## 生成文件组织建议
- `generated/tlv_semantic.h`：语义结构体定义、容量宏
- `generated/tlv_parser.h`：解析API与写回API声明
- `generated/tlv_parser.c`：解析与字段映射实现

## 兼容性与扩展建议
- 使用 `Length` 判断字段可用范围，支持尾部新增字段。
- 不识别的TLV类型直接跳过，保证前向兼容。
- 通过 `cfg/tlv_schema.yaml` 扩展TLV类型，无需手改C逻辑。

