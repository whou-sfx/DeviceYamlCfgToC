/*
 * 自动生成文件，请勿手动编辑。
 */
#ifndef __TLV_PARSER_H__
#define __TLV_PARSER_H__

#include "tlv_semantic.h"
#ifdef __SMOKE_TEST__
#include <stdint.h>

#include "../../cfg/device_config_header.h"
#else
#include "device_config_header.h"
#endif

#define MAX_TLV_COUNT 128

typedef struct {
    uint8_t type;
    uint8_t enable;
    uint16_t length;
    uint16_t value_offset;
    uint16_t tlv_offset;
} tlv_index_t;

int parse_tlv_binary(device_semantic_t *sem, uint8_t *binary, uint16_t length);
int update_tlv_header(device_semantic_t *sem);
uint32_t calculate_crc32(const uint8_t *data, uint32_t length);
int semantic_write_field(device_semantic_t *sem, const field_descriptor_t *fd, uint64_t value);
int semantic_read_field(const device_semantic_t *sem, const field_descriptor_t *fd, uint64_t *value);

#endif /* __TLV_PARSER_H__ */
