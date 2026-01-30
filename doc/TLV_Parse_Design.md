# TLV 解析与修改设计说明

本文档汇总平铺式 TLV 的解析、树形语义构建、修改回写以及兼容策略与示例流程，供固件侧 C 代码实现参考。

## 范围与目标
- 面向 `cfg/tlv_schema.yaml` 定义的平铺 TLV 结构。
- 覆盖：二进制格式约定、解析流程、树形语义映射、修改回写、兼容策略、性能估算与优化建议。
- 不涉及具体实现代码，仅提供设计思想与处理流程。

## 二进制格式约定
### Binary Header（文件头）
参考 `README.md` 说明：
- Header 固定 32 字节，包含 `config_version`、`schema_version`、`feature_bitmap`、`length`、`crc32`。
- TLV 数据紧随 Header 之后。

### TLV Entry 格式
```
Type   (U8)   : TLV 类型 ID
Enable (U8)   : 启用标志（0=禁用，1=启用）
Length (U16)  : Value 字节长度
Value  (var)  : 具体配置数据
```
约定：
- 多字节整数使用小端序。
- Value 部分 4 字节对齐（由编码器处理）。

## 平铺 TLV 与层级语义映射
平铺 TLV 的层级关系由“关键字段组合”恢复，语义规则如下：
- Device 为根节点。
- `Port.*` 通过 `PortID` 关联到 Device。
- `LD.*` 通过 `PortID + LDID` 关联到对应 Port。
- `LD.Range` 通过 `PortID + LDID + RangeID` 关联到对应 Regular LD。
- `FM-LD` 不包含 Range。

语义结构示意（以 `cfg/deviceCfgDPortMLD.yaml` 为例）：
```
Device
├─ Basic
├─ PortCapability
├─ Port[0] (MLD)
│  ├─ LD[0..3] Regular
│  │  └─ Range[0..1]
│  └─ LD[0xF] FM-LD
└─ Port[1] (MLD)
   ├─ LD[0..3] Regular
   │  └─ Range[0..1]
   └─ LD[0xF] FM-LD
```

## 解析流程总览（C 侧）
1. 读取 Binary Header，验证 `length` 与 `crc32`。
2. 顺序扫描 TLV 列表，构建 `tlv_index`（记录 `type/enable/length/offset`）。
3. 使用索引表构建语义树：
   - `Port.Config` -> Port 节点
   - `LD.Config` -> LD 节点
   - `LD.Range` -> Range 节点
4. 节点保存对应 TLV 的 `offset` 或 `index`，支持回写更新。

## 示例流程：Port-0.Config TLV 解析
### 目标
解析 `PortID=0` 的 `Port.Config`，并挂载到语义树。

### 步骤
1. 扫描 TLV 列表，匹配 `Type == Port.Config`。
2. 从 Value 起始解析字段（按 schema 字段顺序与大小）：
   - `PortID`
   - `EnablePort`
   - `PCIeSpeed`
   - `PCIeWidth`
   - `LDMode`
3. 若 `PortID == 0`，创建/定位 `Port[0]` 节点。
4. 填充字段并保存 `tlv_offset` 以便回写。

## 修改与回写流程
1. 通过语义树定位目标节点（例如 `Port[1].LD[2].Range[1]`）。
2. 取出节点内保存的 `tlv_offset` 与 schema 中字段偏移。
3. 原地写回 Value（保持 Length 不变）。
4. 同步更新语义树中的字段值。

## 兼容策略
### TLV 拓扑变更（新增/删除 TLV）
平铺结构以 `Type` 为边界，扫描时不识别的 `Type` 直接跳过，天然向前/向后兼容。

### TLV Value 扩展（尾部新增字段）
要求：只允许在 Value 尾部追加字段，不改变旧字段顺序。

解析策略（不依赖 Version，仅使用 Length）：
- 新程序 + 旧 CFG：`Length` 小于新字段总长时，新增字段使用默认值。
- 旧程序 + 新 CFG：旧程序解析已知字段后跳过剩余字节。

示例（Port.Config 追加 `LanesPerDie`）：
```
旧版长度 = 5：PortID, EnablePort, PCIeSpeed, PCIeWidth, LDMode
新版长度 = 6：追加 LanesPerDie
```

## 性能估算与优化建议
### 粗略估算
以 `cfg/deviceCfgDPortMLD.yaml` 为例，TLV 数量约 30 条，BinaryTLV 规模为数 KB：
- 线性扫描 + 构树耗时通常在 10^1~10^2 微秒量级
- 400MHz RISC-V 预计 < 1ms

### 优化建议
- 单次扫描构建索引表，后续 O(1) 定位。
- 预分配节点池，避免频繁 malloc/free。
- 基于 schema 的固定字段偏移，减少字符串解析。
- 懒构建：只构建使用到的语义节点。
- 原地更新 Value，避免重排 TLV。

## 附：实现要点小结
- 使用小端序读取/写入多字节字段。
- 依赖 `Length` 保障 Value 扩展兼容性。
- 树节点保存 `tlv_offset` 以支持快速回写。
- 不识别的 TLV 类型直接跳过。

