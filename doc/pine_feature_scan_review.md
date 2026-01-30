# Pine Feature 宏扫描与处理建议

本文档基于对代码目录的宏使用点扫描结果整理而成，覆盖 `__MLD__`、`__SINGLE_PORT__`、`__DUAL_PORT__`、`__DCD__`、`__USING_PSS0__`、`__USING_PSS1__` 等特性相关宏，并给出迁移为运行期配置的处理建议。

## 扫描范围与方法

- 扫描范围：`/work/src/pine_fw`
- 扫描方式：使用 `rg` 搜索宏名的使用点

## 宏使用点汇总

### `__MLD__`

影响面最广，覆盖初始化、能力寄存器、任务与 mailbox 等核心路径。

- 初始化与配置：`platform/riscv32/bl2/pcie_init.cpp`、`inc/cxl_spec.h`、`inc/config.h`
- 任务与中断：`main/task_tbl.cpp`、`cpu/riscv32/pss_intr_handler.cpp`
- CXL 设备与 mailbox：`cxl/cxl_dev/*`、`cxl/cxl_mb/*`、`cxl/cxl_mb_task.cpp`
- 驱动与功能模块：`driver/drv_pine/cxl/cxl.cpp`、`driver/drv_pine/cxla_fms/*`
- 其他：`doe/doe_task.cpp`、`cxl/cxl_background/bg_task.cpp`、`cxl/cxl_cpmu/cxl_cpmu.cpp`、`cxl/cxl_chmu/*`



#### Details

- task_tbl.cpp/cxl_mb_task: 静态配置的task-tbl如何根据配置动态初始化
- doe_task.cpp: cmd_tbl 静态配置的doe cmd tbl
- bg_task:  ld_pcie_init for other ld (wait link to cxl mode), reset_hdm_decoder()
- pss_intr_handler, mailbox.cpp, cxl.cpp, pcie_init.cpp: doe_isr_handler, hdmdecoder_commit_isr, mem_en, ld_valid(UFID_X)
- cxla_fms, cxla_fms_hdmdec, cxla_fms_dcd.cpp, doe_task, UFID_X
- cxl_spec.h/config.h : MLD来控制的一些寄存器定义和属性size长度
- fm_api： MLD enable起来支持的一部分 code，可以直接拿掉
- cxla_fms_aes.cpp,  range_based_enc ,  ld_based_enc ,  应该可以直接拿掉
- cxl_chmu.h , cxl_cpmu.cpp,  宏定义，应该也可以拿掉



### `__SINGLE_PORT__` + `__USING_PSS0__` / `__USING_PSS1__`

主要用于单端口与 PSS 选择相关的早期初始化与任务分配。

- BL2 初始化/DDR：`platform/riscv32/bl2/bl2_main.cpp`、`platform/riscv32/bl2/ddr_init.cpp`
- 任务表：`main/task_tbl.cpp`
- 驱动与 DOE：`driver/drv_pine/cxl/cxl.cpp`、`driver/drv_pine/cxla_fms/cxla_fms.cpp`、`driver/drv_pine/doe/doe.cpp`
- 全局配置：`inc/config.h`

### `__DUAL_PORT__`

使用点较少，主要在少量功能模块中分支。

- `cxl/cxl_dev/cxl_dev.cpp`
- `cxl/cxl_cpmu/cxl_cpmu.cpp`

### `__DCD__`

集中于 DCD 功能相关的设备逻辑、CDAT 与 mailbox。

- CXL 设备与 CDAT：`cxl/cxl_dev/*`、`cxl/cdat.*`
- Mailbox 任务与 API：`cxl/cxl_mb_task.cpp`、`cxl/cxl_mb/*`
- 全局配置：`inc/config.h`

## 处理建议（从宏到运行期配置）

### 1) 宏分层策略

- 保留为编译期宏（平台/硅片差异）：`__FPGA__`、`__ASIC__`、`__ZEBU__`、`__QUINCE__` 等
- 迁移为运行期配置（功能与拓扑差异）：`__MLD__`、`__SINGLE_PORT__`、`__DUAL_PORT__`、`__USING_PSS0__`、`__USING_PSS1__`、`__DCD__`

### 2) 迁移优先级建议

- 优先迁移：
  - `main/task_tbl.cpp`（任务表按 Port/LD 动态实例化）
  - `cxl/cxl_mb_task.cpp` 与 `cxl/cxl_mb/*`（Mailbox 行为由 LD/Port 配置驱动）
- 中等优先级：
  - `platform/riscv32/bl2/pcie_init.cpp`（PCIe/CXL Capability 初始化改为模板+参数填充）
- 谨慎迁移：
  - `platform/riscv32/bl2/bl2_main.cpp`、`platform/riscv32/bl2/ddr_init.cpp`（早期启动与 DDR 可能保留最少编译期开关）

### 2.1) 静态 task_tbl + 启用标志过滤

适用于固件内存受限且不希望大改调度框架的场景, 保留最大容量静态表, 运行期按配置启用/禁用条目。

- 思路:
  - `task_tbl` 仍保持静态最大长度, 不使用动态分配。
  - 为每个 task 增加 `enabled` 标志或复用现有 `pauseflag`/`alwaysched` 作为软禁用位。
  - 初始化阶段根据 `device_cfg` 计算 `port_cnt`/`ld_cnt`/`pss_sel`, 逐条设置启用状态。
- 落点建议:
  - `main/task_tbl.cpp`: 保留当前条目集合, 将原 `#if __MLD__`、`#if __SINGLE_PORT__` 分支改为运行期 `if` 写 `enabled`。
  - 调度器遍历时跳过 `enabled == 0` 的条目, 或在构建阶段将禁用条目标记为不可调度。
- 优点:
  - 最小改动, 逻辑清晰, 便于逐步替换宏。
- 缺点:
  - 静态内存占用仍为最大配置, 调度器需多做一次过滤判断。
- Note  cxl_mb_task中的primary 和 secondary mailbox task的初始化和支持command构建也可以按照最大集合默认初始化， 由于对应的task会在task scheduler调度的时候disable，所以它的exec也不不会执行， 都初始化了也没有问题
- doe_task也是相同的处理方案

### 2.2) Function 数量动态化（SLD/MLD）

目标是在硬件上限 `FUNC_MAX_CNT=5` 不变的前提下, 由运行期配置决定实际 function 数量, 替代 `FUNC_CNT` 的编译期宏分支。

- 核心思路:
  - 保持 `FUNC_MAX_CNT` 为上限常量, 新增运行期 `func_cnt` 获取接口, 由配置返回 `1`(SLD) 或 `5`(MLD)。
  - 所有基于 `FUNC_CNT` 的循环改为 `func_cnt`, 避免固定为 MLD/SLD。
- 关键落点:
  - `inc/config.h`: 将 `invalid_fid()` 由宏判断改为基于 `func_cnt` 的运行期判断, 但仍保留 `UFID_0` 为 FMLD 的语义。
  - `platform/riscv32/bl2/pcie_init.cpp`:
    - `wait_for_mld_negotiated()` 在 `func_cnt > 1` 时执行, 并使用运行期数量遍历。
    - `ld_pcie_init()` 仅对 `UFID_1..func_cnt-1` 执行 `pcie_cfgs()`。
- 最小改动原则:
  - 数组维度继续使用最大集合(如 `[PORT_CNT][FUNC_MAX_CNT]`), 运行期仅限制有效范围。
- Note， CXL_NUM_EXTENTS_SUPPORTED 这个宏，用来处理dcd 相关的命令的时候，也可以通过API来获取运行时配置来构建dcd处理的报文
- 寄存器的配置和isr的handle流程，也是可以按照类似的方式处理
- 

### 3) 建议的运行期模型

- `device_cfg`
  - `ports[]`：`mode`（SLD/MLD）、`ld_count`、`pss_sel`、`is_dual_port`
  - `lds[]`：`dcd_en`、`ranges[]`（每 LD 至多 2 段连续 DPA）
- 初始化流程：解析 TLV 配置 → 合法性检查 → PCIe/CXL 初始化 → 任务实例化

## 迁移风险与校验点

- DPA Range 重叠/对齐/容量检查
- SLD/MLD 与 LD 数量一致性校验
- DCD 仅在允许的 LD/Port 组合启用
- 任务依赖关系与数量正确性验证

