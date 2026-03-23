/*
 * 自动生成文件，请勿手动编辑。
 */
#include <string.h>

#include "tlv_parser.h"

static int build_tlv_index(const uint8_t *binary, uint16_t length,
                           tlv_index_t *index, uint16_t *count, uint16_t max_count)
{
    uint16_t offset = sizeof(binary_tlv_header_t);
    uint16_t idx = 0;
    while (offset + sizeof(tlv_entry_t) <= length) {
        const tlv_entry_t *entry = (const tlv_entry_t *)(binary + offset);
        uint16_t value_offset = offset + sizeof(tlv_entry_t);
        uint16_t value_length = entry->length;
        if (value_offset + value_length > length) {
            break;
        }
        if (idx < max_count) {
            index[idx].type = entry->type;
            index[idx].enable = entry->enable;
            index[idx].length = value_length;
            index[idx].value_offset = value_offset;
            index[idx].tlv_offset = offset;
            idx++;
        }
        offset = value_offset + value_length;
    }
    *count = idx;
    return 0;
}

static void map_device_basic(const uint8_t *buf, const tlv_index_t *idx, device_semantic_t *sem)
{
    if (idx->enable != TLV_ENABLE_ENABLED) {
        return;
    }
    const uint8_t *v = buf + idx->value_offset;
    uint16_t base = idx->value_offset;
    uint16_t len = idx->length;

    device_basic_node_t *p = &sem->device_basic;
    p->present = 1;
    p->dirty = 0;
    p->tlv_value_offset = idx->value_offset;
    p->tlv_length = idx->length;

    if (len >= 8) {
        p->TotalDRAMCapacity = (((uint64_t)v[0] << 0) | ((uint64_t)v[1] << 8) | ((uint64_t)v[2] << 16) | ((uint64_t)v[3] << 24) | ((uint64_t)v[4] << 32) | ((uint64_t)v[5] << 40) | ((uint64_t)v[6] << 48) | ((uint64_t)v[7] << 56));
        p->fd_TotalDRAMCapacity = (field_descriptor_t){ .offset = (uint16_t)(base + 0), .type = FIELD_TYPE_U64, .present = 1 };
    } else {
        p->fd_TotalDRAMCapacity = (field_descriptor_t){ .offset = (uint16_t)(base + 0), .type = FIELD_TYPE_U64, .present = 0 };
    }
}

static void map_device_port_capability(const uint8_t *buf, const tlv_index_t *idx, device_semantic_t *sem)
{
    if (idx->enable != TLV_ENABLE_ENABLED) {
        return;
    }
    const uint8_t *v = buf + idx->value_offset;
    uint16_t base = idx->value_offset;
    uint16_t len = idx->length;

    device_port_capability_node_t *p = &sem->device_port_capability;
    p->present = 1;
    p->dirty = 0;
    p->tlv_value_offset = idx->value_offset;
    p->tlv_length = idx->length;

    if (len >= 1) {
        p->MaxPorts = v[0];
        p->fd_MaxPorts = (field_descriptor_t){ .offset = (uint16_t)(base + 0), .type = FIELD_TYPE_U8, .present = 1 };
    } else {
        p->fd_MaxPorts = (field_descriptor_t){ .offset = (uint16_t)(base + 0), .type = FIELD_TYPE_U8, .present = 0 };
    }
}

static void map_port_config(const uint8_t *buf, const tlv_index_t *idx, device_semantic_t *sem)
{
    if (idx->enable != TLV_ENABLE_ENABLED) {
        return;
    }
    const uint8_t *v = buf + idx->value_offset;
    uint16_t base = idx->value_offset;
    uint16_t len = idx->length;

    uint8_t port_id = v[0];
    if (port_id >= MAX_PORTS) {
        return;
    }
    sem->port_count++;
    port_config_node_t *p = &sem->port[port_id].config;
    p->present = 1;
    p->dirty = 0;
    p->tlv_value_offset = idx->value_offset;
    p->tlv_length = idx->length;

    if (len >= 1) {
        p->PortID = v[0];
        p->fd_PortID = (field_descriptor_t){ .offset = (uint16_t)(base + 0), .type = FIELD_TYPE_U8, .present = 1 };
    } else {
        p->fd_PortID = (field_descriptor_t){ .offset = (uint16_t)(base + 0), .type = FIELD_TYPE_U8, .present = 0 };
    }
    if (len >= 2) {
        p->EnablePort = v[1];
        p->fd_EnablePort = (field_descriptor_t){ .offset = (uint16_t)(base + 1), .type = FIELD_TYPE_BOOL, .present = 1 };
    } else {
        p->fd_EnablePort = (field_descriptor_t){ .offset = (uint16_t)(base + 1), .type = FIELD_TYPE_BOOL, .present = 0 };
    }
    if (len >= 3) {
        p->PCIeSpeed = v[2];
        p->fd_PCIeSpeed = (field_descriptor_t){ .offset = (uint16_t)(base + 2), .type = FIELD_TYPE_U8, .present = 1 };
    } else {
        p->fd_PCIeSpeed = (field_descriptor_t){ .offset = (uint16_t)(base + 2), .type = FIELD_TYPE_U8, .present = 0 };
    }
    if (len >= 4) {
        p->PCIeWidth = v[3];
        p->fd_PCIeWidth = (field_descriptor_t){ .offset = (uint16_t)(base + 3), .type = FIELD_TYPE_U8, .present = 1 };
    } else {
        p->fd_PCIeWidth = (field_descriptor_t){ .offset = (uint16_t)(base + 3), .type = FIELD_TYPE_U8, .present = 0 };
    }
    if (len >= 5) {
        p->LDMode = v[4];
        p->fd_LDMode = (field_descriptor_t){ .offset = (uint16_t)(base + 4), .type = FIELD_TYPE_U8, .present = 1 };
    } else {
        p->fd_LDMode = (field_descriptor_t){ .offset = (uint16_t)(base + 4), .type = FIELD_TYPE_U8, .present = 0 };
    }
    if (len >= 6) {
        p->DCD_Supported = v[5];
        p->fd_DCD_Supported = (field_descriptor_t){ .offset = (uint16_t)(base + 5), .type = FIELD_TYPE_BOOL, .present = 1 };
    } else {
        p->fd_DCD_Supported = (field_descriptor_t){ .offset = (uint16_t)(base + 5), .type = FIELD_TYPE_BOOL, .present = 0 };
    }
}

static void map_ld_config(const uint8_t *buf, const tlv_index_t *idx, device_semantic_t *sem)
{
    if (idx->enable != TLV_ENABLE_ENABLED) {
        return;
    }
    const uint8_t *v = buf + idx->value_offset;
    uint16_t base = idx->value_offset;
    uint16_t len = idx->length;

    uint8_t port_id = v[0];
    if (port_id >= MAX_PORTS) {
        return;
    }
    uint8_t ld_type = v[2];
    ld_config_node_t *p = NULL;
    if (ld_type == LD_TYPE_FM_LD) {
        uint8_t idx_fm_ld = 0;
        if (idx_fm_ld >= MAX_FM_LD_PER_PORT) {
            return;
        }
        sem->port[port_id].fm_ld_count++;
        p = &sem->port[port_id].fm_ld[idx_fm_ld].config;
    } else {
        uint8_t ld_id = v[1];
        if (ld_id >= MAX_REGULAR_LD_PER_PORT) {
            return;
        }
        sem->port[port_id].regular_ld_count++;
        p = &sem->port[port_id].regular_ld[ld_id].config;
    }
    if (p == NULL) {
        return;
    }
    p->present = 1;
    p->dirty = 0;
    p->tlv_value_offset = idx->value_offset;
    p->tlv_length = idx->length;

    if (len >= 1) {
        p->PortID = v[0];
        p->fd_PortID = (field_descriptor_t){ .offset = (uint16_t)(base + 0), .type = FIELD_TYPE_U8, .present = 1 };
    } else {
        p->fd_PortID = (field_descriptor_t){ .offset = (uint16_t)(base + 0), .type = FIELD_TYPE_U8, .present = 0 };
    }
    if (len >= 2) {
        p->LDID = v[1];
        p->fd_LDID = (field_descriptor_t){ .offset = (uint16_t)(base + 1), .type = FIELD_TYPE_U8, .present = 1 };
    } else {
        p->fd_LDID = (field_descriptor_t){ .offset = (uint16_t)(base + 1), .type = FIELD_TYPE_U8, .present = 0 };
    }
    if (len >= 3) {
        p->LDType = v[2];
        p->fd_LDType = (field_descriptor_t){ .offset = (uint16_t)(base + 2), .type = FIELD_TYPE_U8, .present = 1 };
    } else {
        p->fd_LDType = (field_descriptor_t){ .offset = (uint16_t)(base + 2), .type = FIELD_TYPE_U8, .present = 0 };
    }
    if (len >= 4) {
        p->DOE = v[3];
        p->fd_DOE = (field_descriptor_t){ .offset = (uint16_t)(base + 3), .type = FIELD_TYPE_BOOL, .present = 1 };
    } else {
        p->fd_DOE = (field_descriptor_t){ .offset = (uint16_t)(base + 3), .type = FIELD_TYPE_BOOL, .present = 0 };
    }
    if (len >= 5) {
        p->SecurityDOE = v[4];
        p->fd_SecurityDOE = (field_descriptor_t){ .offset = (uint16_t)(base + 4), .type = FIELD_TYPE_BOOL, .present = 1 };
    } else {
        p->fd_SecurityDOE = (field_descriptor_t){ .offset = (uint16_t)(base + 4), .type = FIELD_TYPE_BOOL, .present = 0 };
    }
    if (len >= 6) {
        p->Mailbox = v[5];
        p->fd_Mailbox = (field_descriptor_t){ .offset = (uint16_t)(base + 5), .type = FIELD_TYPE_BOOL, .present = 1 };
    } else {
        p->fd_Mailbox = (field_descriptor_t){ .offset = (uint16_t)(base + 5), .type = FIELD_TYPE_BOOL, .present = 0 };
    }
}

static void map_ld_range(const uint8_t *buf, const tlv_index_t *idx, device_semantic_t *sem)
{
    if (idx->enable != TLV_ENABLE_ENABLED) {
        return;
    }
    const uint8_t *v = buf + idx->value_offset;
    uint16_t base = idx->value_offset;
    uint16_t len = idx->length;

    uint8_t port_id = v[0];
    if (port_id >= MAX_PORTS) {
        return;
    }
    uint8_t ld_id = v[1];
    if (ld_id >= MAX_REGULAR_LD_PER_PORT) {
        return;
    }
    uint8_t range_id = v[2];
    if (range_id >= MAX_RANGE_PER_REGULAR_LD) {
        return;
    }
    sem->port[port_id].regular_ld[ld_id].range_count++;
    ld_range_node_t *p = &sem->port[port_id].regular_ld[ld_id].range[range_id];
    p->present = 1;
    p->dirty = 0;
    p->tlv_value_offset = idx->value_offset;
    p->tlv_length = idx->length;

    if (len >= 1) {
        p->PortID = v[0];
        p->fd_PortID = (field_descriptor_t){ .offset = (uint16_t)(base + 0), .type = FIELD_TYPE_U8, .present = 1 };
    } else {
        p->fd_PortID = (field_descriptor_t){ .offset = (uint16_t)(base + 0), .type = FIELD_TYPE_U8, .present = 0 };
    }
    if (len >= 2) {
        p->LDID = v[1];
        p->fd_LDID = (field_descriptor_t){ .offset = (uint16_t)(base + 1), .type = FIELD_TYPE_U8, .present = 1 };
    } else {
        p->fd_LDID = (field_descriptor_t){ .offset = (uint16_t)(base + 1), .type = FIELD_TYPE_U8, .present = 0 };
    }
    if (len >= 3) {
        p->RangeID = v[2];
        p->fd_RangeID = (field_descriptor_t){ .offset = (uint16_t)(base + 2), .type = FIELD_TYPE_U8, .present = 1 };
    } else {
        p->fd_RangeID = (field_descriptor_t){ .offset = (uint16_t)(base + 2), .type = FIELD_TYPE_U8, .present = 0 };
    }
    if (len >= 11) {
        p->Start_DPA = (((uint64_t)v[3] << 0) | ((uint64_t)v[4] << 8) | ((uint64_t)v[5] << 16) | ((uint64_t)v[6] << 24) | ((uint64_t)v[7] << 32) | ((uint64_t)v[8] << 40) | ((uint64_t)v[9] << 48) | ((uint64_t)v[10] << 56));
        p->fd_Start_DPA = (field_descriptor_t){ .offset = (uint16_t)(base + 3), .type = FIELD_TYPE_U64, .present = 1 };
    } else {
        p->fd_Start_DPA = (field_descriptor_t){ .offset = (uint16_t)(base + 3), .type = FIELD_TYPE_U64, .present = 0 };
    }
    if (len >= 19) {
        p->Length = (((uint64_t)v[11] << 0) | ((uint64_t)v[12] << 8) | ((uint64_t)v[13] << 16) | ((uint64_t)v[14] << 24) | ((uint64_t)v[15] << 32) | ((uint64_t)v[16] << 40) | ((uint64_t)v[17] << 48) | ((uint64_t)v[18] << 56));
        p->fd_Length = (field_descriptor_t){ .offset = (uint16_t)(base + 11), .type = FIELD_TYPE_U64, .present = 1 };
    } else {
        p->fd_Length = (field_descriptor_t){ .offset = (uint16_t)(base + 11), .type = FIELD_TYPE_U64, .present = 0 };
    }
}

static void map_ld_dc_region(const uint8_t *buf, const tlv_index_t *idx, device_semantic_t *sem)
{
    if (idx->enable != TLV_ENABLE_ENABLED) {
        return;
    }
    const uint8_t *v = buf + idx->value_offset;
    uint16_t base = idx->value_offset;
    uint16_t len = idx->length;

    uint8_t port_id = v[0];
    if (port_id >= MAX_PORTS) {
        return;
    }
    uint8_t ld_id = v[1];
    if (ld_id >= MAX_REGULAR_LD_PER_PORT) {
        return;
    }
    uint8_t dc_region_id = v[2];
    if (dc_region_id >= MAX_DC_REGION_PER_LD) {
        return;
    }
    sem->port[port_id].regular_ld[ld_id].dc_region_count++;
    ld_dc_region_node_t *p = &sem->port[port_id].regular_ld[ld_id].dc_region[dc_region_id];
    p->present = 1;
    p->dirty = 0;
    p->tlv_value_offset = idx->value_offset;
    p->tlv_length = idx->length;

    if (len >= 1) {
        p->PortID = v[0];
        p->fd_PortID = (field_descriptor_t){ .offset = (uint16_t)(base + 0), .type = FIELD_TYPE_U8, .present = 1 };
    } else {
        p->fd_PortID = (field_descriptor_t){ .offset = (uint16_t)(base + 0), .type = FIELD_TYPE_U8, .present = 0 };
    }
    if (len >= 2) {
        p->LDID = v[1];
        p->fd_LDID = (field_descriptor_t){ .offset = (uint16_t)(base + 1), .type = FIELD_TYPE_U8, .present = 1 };
    } else {
        p->fd_LDID = (field_descriptor_t){ .offset = (uint16_t)(base + 1), .type = FIELD_TYPE_U8, .present = 0 };
    }
    if (len >= 3) {
        p->DC_RegionID = v[2];
        p->fd_DC_RegionID = (field_descriptor_t){ .offset = (uint16_t)(base + 2), .type = FIELD_TYPE_U8, .present = 1 };
    } else {
        p->fd_DC_RegionID = (field_descriptor_t){ .offset = (uint16_t)(base + 2), .type = FIELD_TYPE_U8, .present = 0 };
    }
    if (len >= 11) {
        p->Start_DPA = (((uint64_t)v[3] << 0) | ((uint64_t)v[4] << 8) | ((uint64_t)v[5] << 16) | ((uint64_t)v[6] << 24) | ((uint64_t)v[7] << 32) | ((uint64_t)v[8] << 40) | ((uint64_t)v[9] << 48) | ((uint64_t)v[10] << 56));
        p->fd_Start_DPA = (field_descriptor_t){ .offset = (uint16_t)(base + 3), .type = FIELD_TYPE_U64, .present = 1 };
    } else {
        p->fd_Start_DPA = (field_descriptor_t){ .offset = (uint16_t)(base + 3), .type = FIELD_TYPE_U64, .present = 0 };
    }
    if (len >= 19) {
        p->Decode_len = (((uint64_t)v[11] << 0) | ((uint64_t)v[12] << 8) | ((uint64_t)v[13] << 16) | ((uint64_t)v[14] << 24) | ((uint64_t)v[15] << 32) | ((uint64_t)v[16] << 40) | ((uint64_t)v[17] << 48) | ((uint64_t)v[18] << 56));
        p->fd_Decode_len = (field_descriptor_t){ .offset = (uint16_t)(base + 11), .type = FIELD_TYPE_U64, .present = 1 };
    } else {
        p->fd_Decode_len = (field_descriptor_t){ .offset = (uint16_t)(base + 11), .type = FIELD_TYPE_U64, .present = 0 };
    }
    if (len >= 27) {
        p->Block_size = (((uint64_t)v[19] << 0) | ((uint64_t)v[20] << 8) | ((uint64_t)v[21] << 16) | ((uint64_t)v[22] << 24) | ((uint64_t)v[23] << 32) | ((uint64_t)v[24] << 40) | ((uint64_t)v[25] << 48) | ((uint64_t)v[26] << 56));
        p->fd_Block_size = (field_descriptor_t){ .offset = (uint16_t)(base + 19), .type = FIELD_TYPE_U64, .present = 1 };
    } else {
        p->fd_Block_size = (field_descriptor_t){ .offset = (uint16_t)(base + 19), .type = FIELD_TYPE_U64, .present = 0 };
    }
    if (len >= 28) {
        p->Flags = v[27];
        p->fd_Flags = (field_descriptor_t){ .offset = (uint16_t)(base + 27), .type = FIELD_TYPE_U8, .present = 1 };
    } else {
        p->fd_Flags = (field_descriptor_t){ .offset = (uint16_t)(base + 27), .type = FIELD_TYPE_U8, .present = 0 };
    }
}

int parse_tlv_binary(device_semantic_t *sem, uint8_t *binary, uint16_t length)
{
    if (!sem || !binary) {
        return -1;
    }
    if (length < sizeof(binary_tlv_header_t)) {
        return -1;
    }

    SEMANTIC_INIT(sem);
    sem->tlv_binary = binary;
    sem->tlv_binary_length = length;

    tlv_index_t index[MAX_TLV_COUNT];
    uint16_t index_count = 0;
    build_tlv_index(binary, length, index, &index_count, MAX_TLV_COUNT);

    for (uint16_t i = 0; i < index_count; i++) {
        switch (index[i].type) {
            case TLV_TYPE_DEVICE_BASIC:
                map_device_basic(binary, &index[i], sem);
                break;
            case TLV_TYPE_DEVICE_PORT_CAPABILITY:
                map_device_port_capability(binary, &index[i], sem);
                break;
            case TLV_TYPE_PORT_CONFIG:
                map_port_config(binary, &index[i], sem);
                break;
            case TLV_TYPE_LD_CONFIG:
                map_ld_config(binary, &index[i], sem);
                break;
            case TLV_TYPE_LD_RANGE:
                map_ld_range(binary, &index[i], sem);
                break;
            case TLV_TYPE_LD_DC_REGION:
                map_ld_dc_region(binary, &index[i], sem);
                break;
            default:
                break;
        }
    }

    sem->parse_success = 1;
    sem->total_tlv_count = index_count;
    return 0;
}

uint32_t calculate_crc32(const uint8_t *data, uint32_t length)
{
    uint32_t crc = 0xFFFFFFFFu;
    for (uint32_t i = 0; i < length; i++) {
        crc ^= data[i];
        for (uint8_t b = 0; b < 8; b++) {
            if (crc & 1) {
                crc = (crc >> 1) ^ 0xEDB88320u;
            } else {
                crc >>= 1;
            }
        }
    }
    return ~crc;
}

int update_tlv_header(device_semantic_t *sem)
{
    if (!sem || !sem->tlv_binary) {
        return -1;
    }
    if (!sem->global_dirty) {
        return 0;
    }
    if (sem->tlv_binary_length < sizeof(binary_tlv_header_t)) {
        return -1;
    }

    binary_tlv_header_t *hdr = (binary_tlv_header_t *)sem->tlv_binary;
    hdr->length = sem->tlv_binary_length - sizeof(binary_tlv_header_t);
    hdr->crc32 = 0;
    hdr->crc32 = calculate_crc32(sem->tlv_binary, sem->tlv_binary_length);
    return 0;
}

int semantic_write_field(device_semantic_t *sem, const field_descriptor_t *fd, uint64_t value)
{
    if (!sem || !fd || !fd->present || !sem->tlv_binary) {
        return -1;
    }

    uint16_t offset = fd->offset;
    uint8_t size = field_type_size(fd->type);
    if (offset + size > sem->tlv_binary_length) {
        return -1;
    }

    uint8_t *ptr = sem->tlv_binary + offset;
    /* FIELD_TYPE_BOOL == FIELD_TYPE_U8, handle them together */
    if (fd->type == FIELD_TYPE_U8 || fd->type == FIELD_TYPE_BOOL) {
        *ptr = (uint8_t)value;
    } else if (fd->type == FIELD_TYPE_U16) {
        ptr[0] = value & 0xFF;
        ptr[1] = (value >> 8) & 0xFF;
    } else if (fd->type == FIELD_TYPE_U32) {
        ptr[0] = value & 0xFF;
        ptr[1] = (value >> 8) & 0xFF;
        ptr[2] = (value >> 16) & 0xFF;
        ptr[3] = (value >> 24) & 0xFF;
    } else if (fd->type == FIELD_TYPE_U64) {
        for (uint8_t i = 0; i < 8; i++) {
            ptr[i] = (value >> (i * 8)) & 0xFF;
        }
    } else {
        return -1;
    }

    sem->global_dirty = 1;
    return 0;
}

int semantic_read_field(const device_semantic_t *sem, const field_descriptor_t *fd, uint64_t *value)
{
    if (!sem || !fd || !fd->present || !sem->tlv_binary || !value) {
        return -1;
    }

    uint16_t offset = fd->offset;
    uint8_t size = field_type_size(fd->type);
    if (offset + size > sem->tlv_binary_length) {
        return -1;
    }

    const uint8_t *ptr = sem->tlv_binary + offset;
    *value = 0;
    /* FIELD_TYPE_BOOL == FIELD_TYPE_U8, handle them together */
    if (fd->type == FIELD_TYPE_U8 || fd->type == FIELD_TYPE_BOOL) {
        *value = *ptr;
    } else if (fd->type == FIELD_TYPE_U16) {
        *value = ptr[0] | ((uint16_t)ptr[1] << 8);
    } else if (fd->type == FIELD_TYPE_U32) {
        *value = ptr[0] | ((uint32_t)ptr[1] << 8) | ((uint32_t)ptr[2] << 16) | ((uint32_t)ptr[3] << 24);
    } else if (fd->type == FIELD_TYPE_U64) {
        for (uint8_t i = 0; i < 8; i++) {
            *value |= ((uint64_t)ptr[i]) << (i * 8);
        }
    } else {
        return -1;
    }

    return 0;
}
