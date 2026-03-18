/*
 * 自动生成文件，请勿手动编辑。
 */
#ifndef __TLV_SEMANTIC_H__
#define __TLV_SEMANTIC_H__

#ifdef __SMOKE_TEST__
#include <stdint.h>
#include <string.h>

#include "../../cfg/device_config_header.h"
#else
#include "device_config_header.h"
#endif

typedef enum {
    FIELD_TYPE_U8   = 0,
    FIELD_TYPE_U16  = 1,
    FIELD_TYPE_U32  = 2,
    FIELD_TYPE_U64  = 3,
    FIELD_TYPE_BOOL = 0,
} field_type_t;

static inline uint8_t field_type_size(field_type_t type)
{
    static const uint8_t sizes[] = {1, 2, 4, 8};
    return (type <= FIELD_TYPE_U64) ? sizes[type] : 0;
}

typedef struct {
    uint16_t offset;
    field_type_t type;
    uint8_t present;
} field_descriptor_t;

typedef struct {
    uint8_t present;
    uint8_t dirty;
    uint16_t tlv_value_offset;
    uint16_t tlv_length;

    /* 字段值 */
    uint64_t TotalDRAMCapacity;
    uint8_t DRAMShareable;

    /* 字段描述符 */
    field_descriptor_t fd_TotalDRAMCapacity;
    field_descriptor_t fd_DRAMShareable;
} device_basic_node_t;

typedef struct {
    uint8_t present;
    uint8_t dirty;
    uint16_t tlv_value_offset;
    uint16_t tlv_length;

    /* 字段值 */
    uint8_t MaxPorts;

    /* 字段描述符 */
    field_descriptor_t fd_MaxPorts;
} device_port_capability_node_t;

typedef struct {
    uint8_t present;
    uint8_t dirty;
    uint16_t tlv_value_offset;
    uint16_t tlv_length;

    /* 字段值 */
    uint8_t PortID;
    uint8_t EnablePort;
    uint8_t PCIeSpeed;
    uint8_t PCIeWidth;
    uint8_t LDMode;
    uint8_t DCD_Supported;

    /* 字段描述符 */
    field_descriptor_t fd_PortID;
    field_descriptor_t fd_EnablePort;
    field_descriptor_t fd_PCIeSpeed;
    field_descriptor_t fd_PCIeWidth;
    field_descriptor_t fd_LDMode;
    field_descriptor_t fd_DCD_Supported;
} port_config_node_t;

typedef struct {
    uint8_t present;
    uint8_t dirty;
    uint16_t tlv_value_offset;
    uint16_t tlv_length;

    /* 字段值 */
    uint8_t PortID;
    uint8_t LDID;
    uint8_t LDType;
    uint8_t DOE;
    uint8_t SecurityDOE;
    uint8_t Mailbox;

    /* 字段描述符 */
    field_descriptor_t fd_PortID;
    field_descriptor_t fd_LDID;
    field_descriptor_t fd_LDType;
    field_descriptor_t fd_DOE;
    field_descriptor_t fd_SecurityDOE;
    field_descriptor_t fd_Mailbox;
} ld_config_node_t;

typedef struct {
    uint8_t present;
    uint8_t dirty;
    uint16_t tlv_value_offset;
    uint16_t tlv_length;

    /* 字段值 */
    uint8_t PortID;
    uint8_t LDID;
    uint8_t RangeID;
    uint64_t Start_DPA;
    uint64_t Length;

    /* 字段描述符 */
    field_descriptor_t fd_PortID;
    field_descriptor_t fd_LDID;
    field_descriptor_t fd_RangeID;
    field_descriptor_t fd_Start_DPA;
    field_descriptor_t fd_Length;
} ld_range_node_t;

typedef struct {
    uint8_t present;
    uint8_t dirty;
    uint16_t tlv_value_offset;
    uint16_t tlv_length;

    /* 字段值 */
    uint8_t PortID;
    uint8_t LDID;
    uint8_t DC_RegionID;
    uint64_t Start_DPA;
    uint64_t Decode_len;
    uint64_t Block_size;
    uint8_t Flags;

    /* 字段描述符 */
    field_descriptor_t fd_PortID;
    field_descriptor_t fd_LDID;
    field_descriptor_t fd_DC_RegionID;
    field_descriptor_t fd_Start_DPA;
    field_descriptor_t fd_Decode_len;
    field_descriptor_t fd_Block_size;
    field_descriptor_t fd_Flags;
} ld_dc_region_node_t;

typedef struct {
    ld_config_node_t config;
    ld_range_node_t range[MAX_RANGE_PER_REGULAR_LD];
    uint8_t range_count;
    ld_dc_region_node_t dc_region[MAX_DC_REGION_PER_LD];
    uint8_t dc_region_count;
} regular_ld_t;

typedef struct {
    ld_config_node_t config;
} fm_ld_t;

typedef struct {
    port_config_node_t config;
    regular_ld_t regular_ld[MAX_REGULAR_LD_PER_PORT];
    uint8_t regular_ld_count;
    fm_ld_t fm_ld[MAX_FM_LD_PER_PORT];
    uint8_t fm_ld_count;
} port_t;

typedef struct {
    uint8_t* tlv_binary;
    uint16_t tlv_binary_length;
    uint8_t global_dirty;
    device_basic_node_t device_basic;
    device_port_capability_node_t device_port_capability;
    port_t port[MAX_PORTS];
    uint8_t port_count;
    uint8_t parse_success;
    uint16_t total_tlv_count;
} device_semantic_t;

#define SEMANTIC_INIT(sem) do { \
    memset((sem), 0, sizeof(device_semantic_t)); \
} while (0)

#define SEMANTIC_MARK_DIRTY(sem) do { \
    (sem)->global_dirty = 1; \
} while (0)

#define SEMANTIC_CLEAR_DIRTY(sem) do { \
    (sem)->global_dirty = 0; \
} while (0)

#define SEMANTIC_NEEDS_FLUSH(sem) ((sem)->global_dirty)

#define HAS_DEVICE_BASIC(sem) ((sem)->device_basic.present)

#define HAS_PORT(sem, port_id) \
    ((port_id) < MAX_PORTS && (sem)->port[port_id].config.present)

#define HAS_REGULAR_LD(sem, port_id, ld_id) \
    (HAS_PORT(sem, port_id) && \
     (ld_id) < MAX_REGULAR_LD_PER_PORT && \
     (sem)->port[port_id].regular_ld[ld_id].config.present)

#define HAS_RANGE(sem, port_id, ld_id, range_id) \
    (HAS_REGULAR_LD(sem, port_id, ld_id) && \
     (range_id) < MAX_RANGE_PER_REGULAR_LD && \
     (sem)->port[port_id].regular_ld[ld_id].range[range_id].present)

#define HAS_FM_LD(sem, port_id, fm_id) \
    (HAS_PORT(sem, port_id) && \
     (fm_id) < MAX_FM_LD_PER_PORT && \
     (sem)->port[port_id].fm_ld[fm_id].config.present)

#define MARK_NODE_DIRTY(node) do { \
    (node)->dirty = 1; \
} while (0)

#define CLEAR_NODE_DIRTY(node) do { \
    (node)->dirty = 0; \
} while (0)

#endif /* __TLV_SEMANTIC_H__ */
