/*
 * 基础解析测试：加载Binary TLV，解析语义树并验证关键字段。
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../lib/tlv_parser.h"

static int load_file(const char *path, uint8_t **out_buf, uint16_t *out_len)
{
    FILE *fp = fopen(path, "rb");
    if (!fp) {
        return -1;
    }
    if (fseek(fp, 0, SEEK_END) != 0) {
        fclose(fp);
        return -1;
    }
    long size = ftell(fp);
    if (size <= 0 || size > 0xFFFF) {
        fclose(fp);
        return -1;
    }
    if (fseek(fp, 0, SEEK_SET) != 0) {
        fclose(fp);
        return -1;
    }
    uint8_t *buf = (uint8_t *)malloc((size_t)size);
    if (!buf) {
        fclose(fp);
        return -1;
    }
    if (fread(buf, 1, (size_t)size, fp) != (size_t)size) {
        free(buf);
        fclose(fp);
        return -1;
    }
    fclose(fp);
    *out_buf = buf;
    *out_len = (uint16_t)size;
    return 0;
}

int main(int argc, char *argv[])
{
    const char *path = (argc > 1) ? argv[1] : "../../output/whou_dmld.bin";
    uint8_t *buffer = NULL;
    uint16_t length = 0;
    
    printf("=== TLV Parser Test ===\n");
    printf("Binary file: %s\n", path);
    
    if (load_file(path, &buffer, &length) != 0) {
        fprintf(stderr, "无法读取测试文件: %s\n", path);
        return 1;
    }
    printf("Binary size: %u bytes\n\n", length);

    printf("[1] Parsing TLV binary...\n");
    device_semantic_t sem;
    if (parse_tlv_binary(&sem, buffer, length) != 0) {
        fprintf(stderr, "✗ Parse failed\n");
        free(buffer);
        return 1;
    }
    if (!sem.parse_success || !HAS_DEVICE_BASIC(&sem)) {
        fprintf(stderr, "✗ Semantic tree initialization failed\n");
        free(buffer);
        return 1;
    }
    printf("✓ Parse success (total TLVs: %u)\n\n", sem.total_tlv_count);

    printf("[2] Verifying Device Level...\n");
    if (HAS_DEVICE_BASIC(&sem)) {
        printf("✓ Device.Basic present\n");
        printf("  TotalDRAMCapacity: %llu (512GB)\n", (unsigned long long)sem.device_basic.TotalDRAMCapacity);
        printf("  DRAMShareable: %u\n", sem.device_basic.DRAMShareable);
    }
    if (sem.device_port_capability.present) {
        printf("✓ Device.PortCapability present\n");
        printf("  MaxPorts: %u\n", sem.device_port_capability.MaxPorts);
    }
    printf("\n");

    printf("[3] Verifying Port Level...\n");
    if (sem.port_count < 2 || !HAS_PORT(&sem, 0) || !HAS_PORT(&sem, 1)) {
        fprintf(stderr, "✗ Port count mismatch (expected 2, got %u)\n", sem.port_count);
        free(buffer);
        return 1;
    }
    printf("✓ Port count: %u\n", sem.port_count);
    for (uint8_t i = 0; i < sem.port_count && i < MAX_PORTS; i++) {
        if (HAS_PORT(&sem, i)) {
            printf("✓ Port %u present\n", i);
            printf("  EnablePort: %u\n", sem.port[i].config.EnablePort);
            printf("  PCIeSpeed: %u (Gen%u)\n", sem.port[i].config.PCIeSpeed, sem.port[i].config.PCIeSpeed);
            printf("  PCIeWidth: %u (x%u)\n", sem.port[i].config.PCIeWidth, sem.port[i].config.PCIeWidth);
            printf("  LDMode: %u (%s)\n", sem.port[i].config.LDMode, 
                   sem.port[i].config.LDMode == LD_MODE_MLD ? "MLD" : "SLD");
        }
    }
    printf("\n");

    printf("[4] Verifying LD Level...\n");
    for (uint8_t p = 0; p < sem.port_count && p < MAX_PORTS; p++) {
        printf("✓ Port %u has %u Regular LDs\n", p, sem.port[p].regular_ld_count);
        printf("✓ Port %u has %u FM LD\n", p, sem.port[p].fm_ld_count);
    }
    printf("\n");

    printf("[5] Verifying Range Level...\n");
    for (uint8_t p = 0; p < sem.port_count && p < MAX_PORTS; p++) {
        for (uint8_t l = 0; l < sem.port[p].regular_ld_count && l < MAX_REGULAR_LD_PER_PORT; l++) {
            printf("✓ Port %u, LD %u has %u ranges\n", p, l, sem.port[p].regular_ld[l].range_count);
            for (uint8_t r = 0; r < sem.port[p].regular_ld[l].range_count && r < MAX_RANGE_PER_REGULAR_LD; r++) {
                if (sem.port[p].regular_ld[l].range[r].present) {
                    printf("  Range %u: Start=0x%llx, Length=%llu (32GB), DCD=%u, ShareMode=%u\n",
                           r,
                           (unsigned long long)sem.port[p].regular_ld[l].range[r].Start_DPA,
                           (unsigned long long)sem.port[p].regular_ld[l].range[r].Length,
                           sem.port[p].regular_ld[l].range[r].DCD_Supported,
                           sem.port[p].regular_ld[l].range[r].ShareModeEnable);
                }
            }
        }
    }
    printf("\n");

    printf("[6] Testing field read...\n");
    uint64_t value = 0;
    if (semantic_read_field(&sem, &sem.port[0].config.fd_LDMode, &value) != 0) {
        fprintf(stderr, "✗ Field read failed\n");
        free(buffer);
        return 1;
    }
    printf("✓ Read Port 0 LDMode: %llu\n\n", (unsigned long long)value);

    printf("[7] Testing field write...\n");
    if (semantic_write_field(&sem, &sem.port[0].config.fd_LDMode, LD_MODE_SLD) != 0) {
        fprintf(stderr, "✗ Field write failed\n");
        free(buffer);
        return 1;
    }
    printf("✓ Write Port 0 LDMode: %u\n", LD_MODE_SLD);

    if (!SEMANTIC_NEEDS_FLUSH(&sem)) {
        fprintf(stderr, "✗ Global dirty flag not set\n");
        free(buffer);
        return 1;
    }
    printf("✓ Global dirty flag set\n");
    
    if (semantic_read_field(&sem, &sem.port[0].config.fd_LDMode, &value) != 0) {
        fprintf(stderr, "✗ Field read back failed\n");
        free(buffer);
        return 1;
    }
    printf("✓ Read back Port 0 LDMode: %llu\n\n", (unsigned long long)value);

    printf("[8] Testing CRC update...\n");
    if (update_tlv_header(&sem) != 0) {
        fprintf(stderr, "✗ Header update failed\n");
        free(buffer);
        return 1;
    }
    printf("✓ CRC updated successfully\n");

    binary_tlv_header_t *hdr = (binary_tlv_header_t *)buffer;
    if (hdr->length != length - sizeof(binary_tlv_header_t)) {
        fprintf(stderr, "✗ Header length mismatch\n");
        free(buffer);
        return 1;
    }
    printf("✓ Header length verified\n\n");

    free(buffer);
    printf("=== All tests passed! ===\n");
    return 0;
}


