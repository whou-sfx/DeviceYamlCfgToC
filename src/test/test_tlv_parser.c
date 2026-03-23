/*
 * 基础解析测试：加载Binary TLV，解析语义树并验证关键字段。
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../lib/tlv_parser.h"

/*
 * 通过 linker 把 output/test_dmld.bin 以只读数据段形式嵌入可执行文件。
 *
 * 生成方式示例（由 run_verification.sh 负责）：
 *   ld -r -b binary -o output/test_dmld_bin.o output/test_dmld.bin
 *
 * ld 会自动导出如下符号（路径分隔符/点号会替换为下划线）：
 *   _binary_output_test_dmld_bin_start
 *   _binary_output_test_dmld_bin_end
 */
extern const unsigned char _binary_output_test_dmld_bin_start[];
extern const unsigned char _binary_output_test_dmld_bin_end[];

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

static int load_embedded_default(uint8_t **out_buf, uint16_t *out_len)
{
    const unsigned char *start = _binary_output_test_dmld_bin_start;
    const unsigned char *end = _binary_output_test_dmld_bin_end;
    size_t size = (size_t)(end - start);

    if (size == 0 || size > 0xFFFF) {
        return -1;
    }

    uint8_t *buf = (uint8_t *)malloc(size);
    if (!buf) {
        return -1;
    }
    memcpy(buf, start, size);

    *out_buf = buf;
    *out_len = (uint16_t)size;
    return 0;
}

int main(int argc, char *argv[])
{
    const char *path = (argc > 1) ? argv[1] : "<embedded:output/test_dmld.bin>";
    uint8_t *buffer = NULL;
    uint16_t length = 0;
    
    printf("=== TLV Parser Test ===\n");
    printf("Binary file: %s\n", path);

    if (argc > 1) {
        if (load_file(path, &buffer, &length) != 0) {
            fprintf(stderr, "无法读取测试文件: %s\n", path);
            return 1;
        }
    } else {
        if (load_embedded_default(&buffer, &length) != 0) {
            fprintf(stderr, "无法加载内嵌默认测试文件: output/test_dmld.bin\n");
            return 1;
        }
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
        printf("  TotalDRAMCapacity: %llu (%ldGB)\n", (unsigned long long)sem.device_basic.TotalDRAMCapacity, (sem.device_basic.TotalDRAMCapacity >> 30));
    }
    if (sem.device_port_capability.present) {
        printf("✓ Device.PortCapability present\n");
        printf("  MaxPorts: %u\n", sem.device_port_capability.MaxPorts);
    }
    printf("\n");

    printf("[3] Verifying Port Level...\n");
    // 动态检测启用的 Port 数量
    uint8_t enabled_ports = 0;
    uint8_t first_enabled_port = 0xFF;
    for (uint8_t i = 0; i < MAX_PORTS; i++) {
        if (HAS_PORT(&sem, i)) {
            enabled_ports++;
            if (first_enabled_port == 0xFF) {
                first_enabled_port = i;
            }
            printf("✓ Port %u present\n", i);
            printf("  EnablePort: %u\n", sem.port[i].config.EnablePort);
            printf("  PCIeSpeed: %u (Gen%u)\n", sem.port[i].config.PCIeSpeed, sem.port[i].config.PCIeSpeed);
            printf("  PCIeWidth: %u (x%u)\n", sem.port[i].config.PCIeWidth, sem.port[i].config.PCIeWidth);
            printf("  LDMode: %u (%s)\n", sem.port[i].config.LDMode,
                   sem.port[i].config.LDMode == LD_MODE_MLD ? "MLD" : "SLD");
            printf("  MLD_StartLDid: %u\n", sem.port[i].config.MLD_StartLDid);
        }
    }
    // 验证统计的 port_count 与实际启用的数量一致
    if (enabled_ports != sem.port_count) {
        fprintf(stderr, "✗ Port count mismatch (actual enabled: %u, sem.port_count: %u)\n",
                enabled_ports, sem.port_count);
        free(buffer);
        return 1;
    }
    printf("✓ Port count: %u (verified)\n", sem.port_count);
    printf("\n");

    printf("[4] Verifying LD Level...\n");
    // 遍历所有启用的 Port，检查其 LD 数量
    for (uint8_t p = 0; p < MAX_PORTS; p++) {
        if (HAS_PORT(&sem, p)) {
            printf("✓ Port %u has %u Regular LDs\n", p, sem.port[p].regular_ld_count);
            printf("✓ Port %u has %u FM LD\n", p, sem.port[p].fm_ld_count);
        }
    }
    printf("\n");

    printf("[5] Verifying Range Level...\n");
    // 遍历所有启用的 Port 和 LD，检查 Range 数量
    for (uint8_t p = 0; p < MAX_PORTS; p++) {
        if (!HAS_PORT(&sem, p)) continue;
        for (uint8_t l = 0; l < MAX_REGULAR_LD_PER_PORT; l++) {
            // 检查该 LD 是否有启用的 Config（通过检查 LD 是否存在）
            if (!HAS_REGULAR_LD(&sem, p, l)) continue;
            printf("✓ Port %u, LD %u has %u ranges\n", p, l, sem.port[p].regular_ld[l].range_count);
            for (uint8_t r = 0; r < sem.port[p].regular_ld[l].range_count && r < MAX_RANGE_PER_REGULAR_LD; r++) {
                if (sem.port[p].regular_ld[l].range[r].present) {
                    printf("  Range %u: Start=0x%llx, Length=%llu\n",
                           r,
                           (unsigned long long)sem.port[p].regular_ld[l].range[r].Start_DPA,
                           (unsigned long long)sem.port[p].regular_ld[l].range[r].Length);
                }
            }
        }
    }
    printf("\n");

    printf("[6] Testing field read...\n");
    uint64_t value = 0;
    // 使用第一个启用的 Port 进行字段读写测试
    if (first_enabled_port == 0xFF) {
        fprintf(stderr, "✗ No enabled port for field test\n");
        free(buffer);
        return 1;
    }
    if (semantic_read_field(&sem, &sem.port[first_enabled_port].config.fd_LDMode, &value) != 0) {
        fprintf(stderr, "✗ Field read failed\n");
        free(buffer);
        return 1;
    }
    printf("✓ Read Port %u LDMode: %llu\n", first_enabled_port, (unsigned long long)value);
    
    // 测试读取 MLD_StartLDid 字段
    if (semantic_read_field(&sem, &sem.port[first_enabled_port].config.fd_MLD_StartLDid, &value) != 0) {
        fprintf(stderr, "✗ MLD_StartLDid field read failed\n");
        free(buffer);
        return 1;
    }
    printf("✓ Read Port %u MLD_StartLDid: %llu\n\n", first_enabled_port, (unsigned long long)value);

    printf("[7] Testing field write...\n");
    if (semantic_write_field(&sem, &sem.port[first_enabled_port].config.fd_LDMode, LD_MODE_SLD) != 0) {
        fprintf(stderr, "✗ Field write failed\n");
        free(buffer);
        return 1;
    }
    printf("✓ Write Port %u LDMode: %u\n", first_enabled_port, LD_MODE_SLD);

    if (!SEMANTIC_NEEDS_FLUSH(&sem)) {
        fprintf(stderr, "✗ Global dirty flag not set\n");
        free(buffer);
        return 1;
    }
    printf("✓ Global dirty flag set\n");

    if (semantic_read_field(&sem, &sem.port[first_enabled_port].config.fd_LDMode, &value) != 0) {
        fprintf(stderr, "✗ Field read back failed\n");
        free(buffer);
        return 1;
    }
    printf("✓ Read back Port %u LDMode: %llu\n\n", first_enabled_port, (unsigned long long)value);

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


