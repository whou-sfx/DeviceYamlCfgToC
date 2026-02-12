#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

say() { echo -e "$*"; }
die() { echo "ERROR: $*" 1>&2; exit 1; }

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "缺少命令: $1"
}

need_py_mod() {
  local mod="$1"
  python3 -c "import ${mod}" >/dev/null 2>&1 || {
    say "缺少Python依赖模块: ${mod}"
    say "请安装依赖后重试，例如："
    say "  pip install -r utilities/yaml_to_tlvbinary/requirements.txt"
    say "或："
    say "  pip install 'PyYAML>=6.0'"
    exit 1
  }
}

need_cmd python3
need_cmd gcc
need_py_mod yaml

# 可通过环境变量覆盖
INPUT_YAML="${INPUT_YAML:-${PROJECT_ROOT}/cfg/deviceCfgDPortMLD.yaml}"
OUTPUT_DIR="${OUTPUT_DIR:-${PROJECT_ROOT}/output}"
OUTPUT_BIN="${OUTPUT_BIN:-${OUTPUT_DIR}/test_dmld.bin}"
SCHEMA_YAML="${SCHEMA_YAML:-${PROJECT_ROOT}/cfg/tlv_schema.yaml}"
LIB_DIR="${LIB_DIR:-${PROJECT_ROOT}/src/lib}"
TEST_EXE="${TEST_EXE:-${OUTPUT_DIR}/test_tlv_parser}"

YAML_TO_BIN="${PROJECT_ROOT}/utilities/yaml_to_tlvbinary/yaml_to_binary.py"

say "=== DeviceYamlCfgToC Verification Runner ==="
say "Project root: ${PROJECT_ROOT}"
say "INPUT_YAML : ${INPUT_YAML}"
say "OUTPUT_BIN : ${OUTPUT_BIN}"
say ""

[[ -f "${INPUT_YAML}" ]] || die "输入YAML不存在: ${INPUT_YAML}"
[[ -f "${SCHEMA_YAML}" ]] || die "Schema不存在: ${SCHEMA_YAML}"
[[ -f "${YAML_TO_BIN}" ]] || die "找不到脚本: ${YAML_TO_BIN}"

mkdir -p "${OUTPUT_DIR}"

say "== [1] YAML -> Binary TLV =="
python3 "${YAML_TO_BIN}" -i "${INPUT_YAML}" -o "${OUTPUT_BIN}" -v
say ""

say "== [2] Dump Binary TLV =="
python3 "${YAML_TO_BIN}" -d "${OUTPUT_BIN}"
say ""

say "== [3] Generate C parser code =="
cd "${PROJECT_ROOT}"
python3 -m utilities.tlv_codegen.generate_tlv_parser \
  --schema "${SCHEMA_YAML}" \
  --output-dir "${LIB_DIR}"
say ""

say "== [4] Build test executable =="
say "Embedding default binary: ${OUTPUT_BIN}"
EMBED_OBJ="${OUTPUT_DIR}/test_dmld_bin.o"
# 注意：ld 生成的符号名会基于“输入文件名”派生。
# 这里必须使用相对路径 output/test_dmld.bin，保证符号名稳定为：
#   _binary_output_test_dmld_bin_start/_end
EMBED_SRC_REL="output/test_dmld.bin"
[[ -f "${PROJECT_ROOT}/${EMBED_SRC_REL}" ]] || die "找不到要嵌入的默认bin: ${PROJECT_ROOT}/${EMBED_SRC_REL}"
cd "${PROJECT_ROOT}"
ld -r -b binary -o "${EMBED_OBJ}" "${EMBED_SRC_REL}"

gcc -std=c11 -Wall -Wextra -I"${PROJECT_ROOT}" \
  "${PROJECT_ROOT}/src/test/test_tlv_parser.c" \
  "${PROJECT_ROOT}/src/lib/tlv_parser.c" \
  "${EMBED_OBJ}" \
  -fno-pie -no-pie \
  -o "${TEST_EXE}"
say "Built: ${TEST_EXE}"
say ""

say "== [5] Run tests =="
"${TEST_EXE}" "${OUTPUT_BIN}"
say ""

say "=== All tests passed ==="


