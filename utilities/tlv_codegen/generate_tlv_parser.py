#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""命令行生成器入口。"""

import argparse
from pathlib import Path

from .tlv_code_generator import TLVCodeGenerator


def main() -> None:
    parser = argparse.ArgumentParser(description="TLV解析C代码生成器")
    parser.add_argument(
        "--schema",
        default=str(Path(__file__).parent / "../../cfg/tlv_schema.yaml"),
        help="TLV schema YAML路径",
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).parent / "../../src/lib"),
        help="输出目录（生成tlv_semantic.h/ tlv_parser.h/ tlv_parser.c）",
    )
    args = parser.parse_args()

    generator = TLVCodeGenerator(args.schema)
    generator.generate(args.output_dir)
    print(f"生成完成: {args.output_dir}")


if __name__ == "__main__":
    main()


