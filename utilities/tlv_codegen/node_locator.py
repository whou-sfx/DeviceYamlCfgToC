"""TLV节点定位逻辑生成器（Schema驱动）。"""

from typing import Dict, List

from .name_utils import node_struct_name
from .type_mapper import CTypeMapper


class NodeLocator:
    """根据TLV类型和Schema中的locator元数据生成节点定位代码片段。"""
    
    def __init__(self, schemas: Dict[str, dict], hierarchy: dict = None):
        self.schemas = schemas
        self.hierarchy = hierarchy or {}
        self.device_tlvs = self.hierarchy.get('Device_Level_TLVs', [])

    def _get_device_field_name(self, tlv_name: str) -> str:
        """从 hierarchy 配置中获取 device_semantic_t 的字段名"""
        structures = self.hierarchy.get('Structures', [])
        for struct in structures:
            if struct['name'] == 'device_semantic_t':
                for field in struct['fields']:
                    if field.get('from_tlv') == tlv_name:
                        return field['name']
        from .name_utils import tlv_name_to_snake
        return tlv_name_to_snake(tlv_name)

    def _calculate_field_offset(self, fields: List[dict], field_name: str) -> int:
        """计算指定字段在TLV value中的字节偏移"""
        offset = 0
        for field in fields:
            if field['name'] == field_name:
                return offset
            ftype = field['type']
            if ftype == 'string':
                offset += field.get('size', 32)
            else:
                offset += CTypeMapper.size(ftype)
        raise KeyError(f"Field {field_name} not found in schema")

    def _generate_step_code(self, step: dict, fields: List[dict], path_prefix: str,
                            update_counter: bool = True) -> List[str]:
        """为单个 locator step 生成 C 代码"""
        lines = []

        # 提取变量（从TLV字段或固定值）
        if 'fixed_index' in step:
            var_name = f"idx_{step['array']}"
            lines.append(f"uint8_t {var_name} = {step['fixed_index']};")
        elif 'source' in step:
            var_name = step['var']
            offset = self._calculate_field_offset(fields, step['source'])
            lines.append(f"uint8_t {var_name} = v[{offset}];")
        else:
            raise ValueError(f"Step must have either 'source' or 'fixed_index': {step}")

        # 边界检查
        if 'max' in step:
            lines.append(f"if ({var_name} >= {step['max']}) {{")
            lines.append("    return;")
            lines.append("}")

        # 更新计数器（仅当 update_counter=True 时）
        if update_counter and 'counter' in step:
            counter_path = f"{path_prefix}{step['counter']}"
            # 改为递增模式：直接 ++，不再使用 max 逻辑
            lines.append(f"{counter_path}++;")

        return lines, var_name

    def _generate_dispatch_code(self, dispatch: dict, fields: List[dict], path_prefix: str) -> List[str]:
        """生成 dispatch 分支代码"""
        lines = []

        # 提取 dispatch 变量
        dispatch_var = dispatch['var']
        dispatch_source = dispatch['source']
        offset = self._calculate_field_offset(fields, dispatch_source)
        lines.append(f"uint8_t {dispatch_var} = v[{offset}];")

        # 声明指针（后续分支赋值）
        lines.append("ld_config_node_t *p = NULL;")

        # 生成各个 case
        cases = dispatch.get('cases', [])
        for i, case in enumerate(cases):
            if case.get('default'):
                if i == 0:
                    raise ValueError("default case cannot be first")
                lines.append("} else {")
            elif i == 0:
                match_val = case['match']
                lines.append(f"if ({dispatch_var} == {match_val}) {{")
            else:
                match_val = case['match']
                lines.append(f"}} else if ({dispatch_var} == {match_val}) {{")

            # 处理该分支的 steps
            case_steps = case.get('steps', [])
            case_path = path_prefix
            for j, step in enumerate(case_steps):
                # 该分支的最后一个 step 才更新计数器
                is_last_step = (j == len(case_steps) - 1)
                step_lines, var_name = self._generate_step_code(step, fields, case_path, update_counter=is_last_step)
                for line in step_lines:
                    lines.append(f"    {line}")

                if 'array' in step:
                    case_path += f"{step['array']}[{var_name}]."

            # 生成目标指针赋值
            target = case.get('target', 'config')
            lines.append(f"    p = &{case_path}{target};")

        lines.append("}")

        # NULL 检查
        lines.append("if (p == NULL) {")
        lines.append("    return;")
        lines.append("}")

        return lines

    def _generate_locator_from_metadata(self, tlv_name: str, schema: dict) -> Dict[str, List[str]]:
        """从 schema 的 locator 元数据生成定位代码"""
        locator_cfg = schema.get('locator')
        if not locator_cfg:
            raise KeyError(f"No locator metadata for TLV: {tlv_name}")

        fields = schema.get('fields', [])
        lines = []
        path = "sem->"

        # 处理 steps
        steps = locator_cfg.get('steps', [])
        for i, step in enumerate(steps):
            # 只有最后一个 step 才更新计数器
            is_last_step = (i == len(steps) - 1) and ('dispatch' not in locator_cfg)
            step_lines, var_name = self._generate_step_code(step, fields, path, update_counter=is_last_step)
            lines.extend(step_lines)

            if 'array' in step:
                path += f"{step['array']}[{var_name}]."

        # 处理 dispatch（如果有）
        if 'dispatch' in locator_cfg:
            dispatch_lines = self._generate_dispatch_code(locator_cfg['dispatch'], fields, path)
            lines.extend(dispatch_lines)
        else:
            # 无 dispatch，直接生成指针赋值
            target = locator_cfg.get('target', '')
            node_type = node_struct_name(tlv_name)
            if target:
                lines.append(f"{node_type} *p = &{path}{target};")
            else:
                # 去掉末尾的点
                path = path.rstrip('.')
                lines.append(f"{node_type} *p = &{path};")

        return {
            "node_type": node_struct_name(tlv_name),
            "pre_lines": lines,
        }

    def get_locator(self, tlv_name: str) -> Dict[str, List[str]]:
        """获取指定TLV的定位代码"""
        # Device 级 TLV：从 hierarchy 查找字段名
        if tlv_name in self.device_tlvs:
            node_type = node_struct_name(tlv_name)
            field_name = self._get_device_field_name(tlv_name)
            return {
                "node_type": node_type,
                "pre_lines": [f"{node_type} *p = &sem->{field_name};"],
            }
        
        # 非 Device 级 TLV：从 schema 的 locator 元数据生成
        if tlv_name not in self.schemas:
            raise KeyError(f"TLV {tlv_name} not found in schemas")
        
        schema = self.schemas[tlv_name]
        return self._generate_locator_from_metadata(tlv_name, schema)


