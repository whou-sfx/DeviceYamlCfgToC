#!/bin/bash
# 示例使用脚本

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 输入输出路径
INPUT_YAML="$PROJECT_ROOT/cfg/deviceCfg.yaml"
OUTPUT_DIR="$PROJECT_ROOT/output"
OUTPUT_BIN="$OUTPUT_DIR/device_config.bin"

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

echo "=========================================="
echo "YAML配置文件转Binary TLV工具 - 示例"
echo "=========================================="
echo ""

# 检查输入文件是否存在
if [ ! -f "$INPUT_YAML" ]; then
    echo "错误: 输入文件不存在: $INPUT_YAML"
    exit 1
fi

echo "输入文件: $INPUT_YAML"
echo "输出文件: $OUTPUT_BIN"
echo ""

# 执行转换（带详细信息）
echo "正在转换..."
echo ""
python3 "$SCRIPT_DIR/yaml_to_binary.py" \
    -i "$INPUT_YAML" \
    -o "$OUTPUT_BIN" \
    -v \
    --config-version 1 \
    --schema-version 1 \
    --feature-bitmap 0x0

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "转换成功！"
    echo "=========================================="
    echo ""
    
    # 显示文件信息
    echo "输出文件信息:"
    ls -lh "$OUTPUT_BIN"
    echo ""
    
    # 转储二进制文件
    echo "=========================================="
    echo "转储二进制文件内容"
    echo "=========================================="
    echo ""
    python3 "$SCRIPT_DIR/yaml_to_binary.py" -d "$OUTPUT_BIN"
else
    echo ""
    echo "转换失败！"
    exit 1
fi

