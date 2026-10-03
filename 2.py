import os
import argparse
from datetime import datetime


def build_rename_plan(folder_path, fields, new_order, sep="_", ext_filter=None):
    """生成改名计划，返回 [(旧路径, 新路径), ...] 以及跳过/冲突列表"""
    field_index = {name: i for i, name in enumerate(fields)}
    for name in new_order:
        if name not in field_index:
            print(f"错误：排序字段 '{name}' 不在字段列表 {fields} 中")
            return None, None, None

    ext_list = None
    if ext_filter:
        ext_list = []
        for ext in ext_filter.split(","):
            ext = ext.strip().lower()
            if not ext:
                continue
            if not ext.startswith("."):
                ext = "." + ext
            ext_list.append(ext)

    plan = []
    skipped = []
    for filename in sorted(os.listdir(folder_path)):
        filepath = os.path.join(folder_path, filename)
        if not os.path.isfile(filepath):
            continue

        if ext_list:
            _, file_ext = os.path.splitext(filename)
            if file_ext.lower() not in ext_list:
                continue

        stem, ext = os.path.splitext(filename)
        parts = [p.strip() for p in stem.split(sep)]
        if len(parts) != len(fields):
            skipped.append((filename, f"字段数量不匹配：期望 {len(fields)} 个，实际 {len(parts)} 个"))
            continue

        new_parts = [parts[field_index[name]] for name in new_order]
        new_filename = sep.join(new_parts) + ext
        new_filepath = os.path.join(folder_path, new_filename)
        plan.append((filepath, new_filepath, filename, new_filename))

    # 冲突检测：目标不能已存在（除自身外），且不能有两个文件改到同一目标
    existing = set(os.listdir(folder_path))
    target_count = {}
    for _, _, _, new_name in plan:
        target_count[new_name] = target_count.get(new_name, 0) + 1

    conflicts = []
    final_plan = []
    for old_path, new_path, old_name, new_name in plan:
        if new_name in existing and new_name != old_name:
            conflicts.append((old_name, new_name, "目标文件名已存在，不允许覆盖"))
            continue
        if target_count[new_name] > 1:
            conflicts.append((old_name, new_name, "多个文件将改到同一目标名"))
            continue
        final_plan.append((old_path, new_path, old_name, new_name))

    return final_plan, skipped, conflicts


def cmd_rename(folder_path, fields_str, order_str, sep="_", ext_filter=None, apply=False):
    if not os.path.isdir(folder_path):
        print(f"错误：'{folder_path}' 不是有效的文件夹！")
        return

    fields = [s.strip() for s in fields_str.split(",") if s.strip()]
    new_order = [s.strip() for s in order_str.split(",") if s.strip()]

    if len(fields) < 2:
        print("错误：至少需要 2 个字段才能重排。")
        return

    plan, skipped, conflicts = build_rename_plan(folder_path, fields, new_order, sep, ext_filter)
    if plan is None:
        return

    print(f"\n目录: {folder_path}")
    print(f"字段: {fields}  ->  新顺序: {new_order}  (分隔符: '{sep}')")
    print("=" * 60)

    if skipped:
        print(f"[跳过] {len(skipped)} 个文件不符合字段规则：")
        for name, reason in skipped:
            print(f"    - {name}  ({reason})")
        print()

    if conflicts:
        print(f"[冲突] {len(conflicts)} 个改名存在冲突（不会执行）：")
        for old, new, reason in conflicts:
            print(f"    - {old}  ->  {new}  ({reason})")
        print()

    if not plan:
        print("没有可执行的改名操作。")
        return

    print(f"改名计划（共 {len(plan)} 个）：")
    for _, _, old_name, new_name in plan:
        print(f"    {old_name}  ->  {new_name}")
    print("=" * 60)

    if not apply:
        print("\n[预览模式] 未执行任何改名。加 --apply 以实际执行。")
        return

    # 执行改名
    success, failed = 0, 0
    for old_path, new_path, old_name, new_name in plan:
        try:
            os.rename(old_path, new_path)
            success += 1
        except OSError as e:
            failed += 1
            print(f"[失败] {old_name} -> {new_name}: {e}")
    print(f"\n执行完成：成功 {success} 个，失败 {failed} 个。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="作业文件批量归档脚本 - 需求2：批量改名")
    parser.add_argument("folder", nargs="?", default=None, help="目标文件夹路径")
    parser.add_argument("--fields", help="字段名，逗号分隔，如 学号,姓名,作业名")
    parser.add_argument("--order", help="新顺序字段名，逗号分隔，如 作业名,学号")
    parser.add_argument("--sep", default="_", help="字段分隔符，默认下划线")
    parser.add_argument("--ext", help="只处理指定扩展名，如 .pdf,.docx", default=None)
    parser.add_argument("--apply", action="store_true", help="实际执行改名（默认只预览）")

    args = parser.parse_args()

    folder = args.folder
    if not folder:
        folder = input("请输入目标文件夹路径：").strip()

    fields = args.fields
    if not fields:
        fields = input("请输入字段名（逗号分隔，如 学号,姓名,作业名）：").strip()

    order = args.order
    if not order:
        order = input("请输入新顺序字段名（逗号分隔，如 作业名,学号）：").strip()

    cmd_rename(folder, fields, order, args.sep, args.ext, args.apply)
