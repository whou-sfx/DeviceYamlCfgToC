/**
 * @file device_config_header.h
 * @brief Device Configuration Header Definitions
 * 
 * 此头文件定义了Binary TLV配置文件的Header结构和常量。
 * 可同时用于Python工具和固件C代码。
 */

#ifndef DEVICE_CONFIG_HEADER_H
#define DEVICE_CONFIG_HEADER_H

#include <stdint.h>

#define MAX_PORTS 2
#define MAX_LD_PER_PORT 4
#define MAX_FM_LD_PER_PORT 1
#define MAX_REGULAR_LD_PER_PORT 4
#define MAX_RANGE_PER_REGULAR_LD 2
#define MAX_DC_REGION_PER_LD 4


/*============================================================================
 * Header结构定义
 *============================================================================*/

/**
 * Binary TLV文件Header结构 (32字节对齐)
 * 
 * 结构布局:
 *   Offset | Field           | Type | Size | Description
 *   -------|-----------------|------|------|------------------
 *   0x00   | config_version  | U16  | 2    | 配置版本号
 *   0x02   | schema_version  | U16  | 2    | Schema版本号
 *   0x04   | feature_bitmap  | U32  | 4    | 特性位图
 *   0x08   | length          | U32  | 4    | 数据长度（不含header）
 *   0x0C   | reserved        | -    | 16   | 保留字段
 *   0x1C   | crc32           | U32  | 4    | CRC32校验和
 */
typedef struct __attribute__((packed)) {
    uint16_t config_version;    /**< 配置版本号 */
    uint16_t schema_version;    /**< Schema版本号 */
    uint32_t feature_bitmap;    /**< 特性位图 */
    uint32_t length;            /**< 数据长度（不包含header） */
    uint8_t  reserved[16];      /**< 保留字段 */
    uint32_t crc32;             /**< CRC32校验和 */
} binary_tlv_header_t;

/* 确保Header大小为32字节 */
/* C/C++ static assert 兼容 */
#ifdef __cplusplus
  #define STATIC_ASSERT(cond, msg) static_assert((cond), msg)
#else
  #define STATIC_ASSERT(cond, msg) _Static_assert((cond), msg)
#endif
/*============================================================================
 * TLV结构定义
 *============================================================================*/

/**
 * TLV (Type-Length-Value) 条目结构
 * 
 * 每个配置项都编码为一个TLV条目：
 *   Offset | Field  | Type | Size | Description
 *   -------|--------|------|------|------------------
 *   0x00   | Type   | U8   | 1    | TLV类型ID
 *   0x01   | Enable | U8   | 1    | 启用标志 (0=禁用, 1=启用)
 *   0x02   | Length | U16  | 2    | Value字段长度
 *   0x04   | Value  | var  | N    | 具体配置数据
 */
typedef struct __attribute__((packed)) {
    uint8_t  type;      /**< TLV类型ID */
    uint8_t  enable;    /**< 启用标志: 0=禁用, 1=启用 */
    uint16_t length;    /**< Value字段长度（字节数） */
    uint8_t  value[];   /**< 可变长度的配置数据 */
} tlv_entry_t;

/**
 * TLV类型定义
 */
typedef enum {
    TLV_TYPE_DEVICE_BASIC           = 0x01,  /**< 设备基本信息 */
    TLV_TYPE_DEVICE_PORT_CAPABILITY = 0x02,  /**< 设备端口能力 */
    TLV_TYPE_PORT_CONFIG            = 0x10,  /**< 端口配置 */
    TLV_TYPE_LD_CONFIG              = 0x20,  /**< 逻辑设备配置 */
    TLV_TYPE_LD_RANGE               = 0x30,  /**< 逻辑设备范围配置 */
    TLV_TYPE_LD_DC_REGION           = 0x31,  /**< 逻辑设备DC区域配置 */
} tlv_type_t;

/**
 * TLV Enable字段值定义
 */
#define TLV_ENABLE_DISABLED  0  /**< 配置项禁用 */
#define TLV_ENABLE_ENABLED   1  /**< 配置项启用 */

/*============================================================================
 * Header版本定义
 *============================================================================*/

/** 默认配置版本号 */
#define CONFIG_VERSION_DEFAULT  1

/** 默认Schema版本号 */
#define SCHEMA_VERSION_DEFAULT  1

/*============================================================================
 * Feature Bitmap位定义
 *============================================================================*/

/**
 * Feature Bitmap位位置定义
 * 
 * 每个特性占用1个bit位，从bit0开始分配。
 */
#define FEATURE_BIT_DUAL_PORT   0   /**< Dual-Port特性位 (bit0) */
#define FEATURE_BIT_MLD         1   /**< MLD (Multi-Logical Device)特性位 (bit1) */
#define FEATURE_BIT_DCD         2   /**< DCD (Dynamic Capacity Device)特性位 (bit2) */
/* bits 3-31: 保留供未来使用 */

/**
 * Feature Bitmap掩码定义
 * 
 * 用于设置或检查特定特性位。
 */
#define FEATURE_MASK_DUAL_PORT  (1U << FEATURE_BIT_DUAL_PORT)  /**< 0x01 - Dual-Port掩码 */
#define FEATURE_MASK_MLD        (1U << FEATURE_BIT_MLD)        /**< 0x02 - MLD掩码 */
#define FEATURE_MASK_DCD        (1U << FEATURE_BIT_DCD)        /**< 0x04 - DCD掩码 */

/**
 * 组合特性掩码示例
 */
#define FEATURE_MASK_ALL_PORTS  (FEATURE_MASK_DUAL_PORT)       /**< 所有端口相关特性 */
#define FEATURE_MASK_ALL_LD     (FEATURE_MASK_MLD)             /**< 所有LD相关特性 */

/*============================================================================
 * 默认Feature Bitmap值
 *============================================================================*/

/**
 * 默认Feature Bitmap值
 * 
 * 默认所有特性位为0（禁用）。
 * 可通过命令行参数或配置文件覆盖。
 */
#define FEATURE_BITMAP_DEFAULT  0x00

/*============================================================================
 * Feature Bitmap辅助宏
 *============================================================================*/

/**
 * 检查特性位是否设置
 * @param bitmap Feature bitmap值
 * @param mask   特性掩码
 * @return 非零表示特性已启用
 */
#define FEATURE_IS_ENABLED(bitmap, mask)  ((bitmap) & (mask))

/**
 * 设置特性位
 * @param bitmap Feature bitmap值
 * @param mask   特性掩码
 */
#define FEATURE_SET(bitmap, mask)         ((bitmap) |= (mask))

/**
 * 清除特性位
 * @param bitmap Feature bitmap值
 * @param mask   特性掩码
 */
#define FEATURE_CLEAR(bitmap, mask)       ((bitmap) &= ~(mask))

/**
 * 切换特性位
 * @param bitmap Feature bitmap值
 * @param mask   特性掩码
 */
#define FEATURE_TOGGLE(bitmap, mask)      ((bitmap) ^= (mask))

/*============================================================================
 * 使用示例
 *============================================================================*/

#if 0  /* 示例代码，不编译 */

/* 示例1: 创建启用Dual-Port和MLD的配置 */
uint32_t features = FEATURE_BITMAP_DEFAULT;
FEATURE_SET(features, FEATURE_MASK_DUAL_PORT);
FEATURE_SET(features, FEATURE_MASK_MLD);
/* features = 0x03 */

/* 示例2: 检查是否启用DCD */
if (FEATURE_IS_ENABLED(features, FEATURE_MASK_DCD)) {
    /* DCD已启用 */
}

/* 示例3: 初始化Header */
binary_tlv_header_t header = {
    .config_version = CONFIG_VERSION_DEFAULT,
    .schema_version = SCHEMA_VERSION_DEFAULT,
    .feature_bitmap = FEATURE_BITMAP_DEFAULT,
    .length = 0,
    .crc32 = 0
};

#endif /* 示例代码结束 */

/*============================================================================
 * TLV字段枚举定义
 *============================================================================*/

/**
 * @brief PCIe速度枚举
 * 
 * 使用语义化值，Gen版本号对应枚举值
 */
typedef enum {
    PCIE_SPEED_GEN1 = 1,    /**< PCIe Gen1 (2.5 GT/s) */
    PCIE_SPEED_GEN2 = 2,    /**< PCIe Gen2 (5 GT/s) */
    PCIE_SPEED_GEN3 = 3,    /**< PCIe Gen3 (8 GT/s) */
    PCIE_SPEED_GEN4 = 4,    /**< PCIe Gen4 (16 GT/s) */
    PCIE_SPEED_GEN5 = 5,    /**< PCIe Gen5 (32 GT/s) */
    PCIE_SPEED_GEN6 = 6,    /**< PCIe Gen6 (64 GT/s) */
} pcie_speed_t;

/**
 * @brief PCIe通道宽度枚举
 * 
 * 使用语义化值，通道数对应枚举值
 */
typedef enum {
    PCIE_WIDTH_X1  = 1,     /**< PCIe x1 */
    PCIE_WIDTH_X2  = 2,     /**< PCIe x2 */
    PCIE_WIDTH_X4  = 4,     /**< PCIe x4 */
    PCIE_WIDTH_X8  = 8,     /**< PCIe x8 */
    PCIE_WIDTH_X16 = 16,    /**< PCIe x16 */
} pcie_width_t;

/**
 * @brief 逻辑设备模式枚举
 */
typedef enum {
    LD_MODE_SLD = 0,        /**< Single Logical Device - 单一逻辑设备 */
    LD_MODE_MLD = 1,        /**< Multiple Logical Devices - 多逻辑设备 */
} ld_mode_t;

/**
 * @brief 逻辑设备类型枚举
 */
typedef enum {
    LD_TYPE_REGULAR_LD = 0, /**< Regular LD - 常规逻辑设备 */
    LD_TYPE_FM_LD      = 1, /**< Fabric Manager LD - Fabric管理器逻辑设备 */
} ld_type_t;

#endif /* DEVICE_CONFIG_HEADER_H */

