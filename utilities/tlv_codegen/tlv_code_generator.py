"""TLV解析C代码生成器主模块。"""

from pathlib import Path
from typing import Dict

import yaml

from .parser_generator import ParserGenerator
from .struct_generator import StructGenerator


class TLVCodeGenerator:
    def __init__(self, schema_file: str):
        self.schema_file = Path(schema_file)
        self.schemas: Dict[str, dict] = {}
        self.hierarchy: dict = {}

    def load_schema(self) -> None:
        if not self.schema_file.exists():
            raise FileNotFoundError(f"Schema file not found: {self.schema_file}")
        with self.schema_file.open("r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        self.schemas = config.get("TLV_Schemas", {})
        if not self.schemas:
            raise ValueError(f"No TLV_Schemas found in {self.schema_file}")
        
        # 读取 Hierarchy 配置
        self.hierarchy = config.get("Hierarchy", {})

    def generate(self, output_dir: str) -> None:
        if not self.schemas:
            self.load_schema()

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        struct_gen = StructGenerator(self.schemas, self.hierarchy)
        parser_gen = ParserGenerator(self.schemas, self.hierarchy)

        (output_path / "tlv_semantic.h").write_text(struct_gen.generate(), encoding="utf-8")
        (output_path / "tlv_parser.h").write_text(parser_gen.generate_header(), encoding="utf-8")
        (output_path / "tlv_parser.cpp").write_text(parser_gen.generate_source(), encoding="utf-8")



