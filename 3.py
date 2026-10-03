import os
import json
import shutil
import argparse
from datetime import datetime


def archive_files(folder_path, rules, ext_filter=None):
    """
    按关键词规则把文件移动到子文件夹，并生成报告。
    rules: dict，如 {"数据结构": "ds", "操作系统": "os"}
    """
    if not os.path.isdir(folder_path):
        print(f"错误：'{folder_path}' 不是有效的文件夹！")
        return

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

    print(f"\n正在归档文件夹: {folder_path}")
    print(f"归档规则: {rules}")

    moved = []
    skipped = []

    for filename in sorted(os.listdir(folder_path)):
        filepath = os.path.join(folder_path, filename)
        if not os.path.isfile(filepath):
            continue

        if ext_list:
            _, file_ext = os.path.splitext(filename)
            if file_ext.lower() not in ext_list:
                continue

        target_folder = "other"
        for keyword, folder_name in rules.items():
            if keyword in filename:
                target_folder = folder_name
                break

        dst_dir = os.path.join(folder_path, target_folder)
        dst_path = os.path.join(dst_dir, filename)

        if os.path.exists(dst_path):
            skipped.append((filename, f"目标已存在: {target_folder}/{filename}"))
            continue

        moved.append((filepath, dst_path, target_folder, filename))

    success = []
    failed = []
    for src, dst, category, name in moved:
        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
            success.append((src, dst, category))
        except Exception as e:
            failed.append((name, str(e)))
            skipped.append((name, f"移动失败: {e}"))

    report = {
        "归档时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "源目录": folder_path,
        "规则": rules,
        "统计": {
            "处理成功": len(success),
            "跳过": len(skipped) - len(failed),
            "失败": len(failed),
        },
        "已移动文件": [
            {"原路径": s, "目标路径": d, "归档类别": c} for s, d, c in success
        ],
        "跳过/失败": [
            {"文件名": n, "原因": r} for n, r in skipped
        ],
    }

    output_dir = os.path.join(folder_path, "archive_output")
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, "archive_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    manifest = {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source_root": folder_path,
        "moves": [{"from": d, "to": s} for s, d, _ in success],
    }
    manifest_path = os.path.join(output_dir, "archive_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 50)
    print("归档完成")
    print("=" * 50)
    print(f"  处理成功: {len(success)}")
    print(f"  跳过:     {len(skipped) - len(failed)}")
    print(f"  失败:     {len(failed)}")
    print()
    if success:
        print("已移动文件:")
        for s, d, c in success:
            print(f"    [{c}] {os.path.basename(s)}  ->  {d}")
    if skipped:
        print("\n跳过/失败:")
        for n, r in skipped:
            print(f"    {n}  ({r})")
    print()
    print(f"归档报告: {report_path}")
    print(f"撤销清单: {manifest_path}")


def undo_archive(manifest_path):
    """根据 manifest 撤销上一次归档，把文件移回原位置。"""
    if not os.path.isfile(manifest_path):
        print(f"错误：找不到撤销清单: {manifest_path}")
        return

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    moves = manifest.get("moves", [])
    if not moves:
        print("清单中没有可撤销的移动。")
        return

    print(f"\n撤销清单: {manifest_path}")
    print(f"共 {len(moves)} 个文件待还原。")
    print("=" * 50)

    success, failed = 0, 0
    for item in moves:
        cur = item["from"]
        orig = item["to"]

        if not os.path.exists(cur):
            print(f"[跳过] {os.path.basename(cur)} 不存在，可能已被手动处理")
            failed += 1
            continue
        if os.path.exists(orig):
            print(f"[冲突] 原位置已存在文件，不覆盖: {orig}")
            failed += 1
            continue

        try:
            os.makedirs(os.path.dirname(orig), exist_ok=True)
            shutil.move(cur, orig)
            print(f"    还原: {os.path.basename(cur)}  ->  {orig}")
            success += 1
        except Exception as e:
            print(f"[失败] {os.path.basename(cur)}: {e}")
            failed += 1

    print("=" * 50)
    print(f"撤销完成: 成功 {success} 个，失败/跳过 {failed} 个。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="作业文件批量归档脚本 - 需求3：归档与报告")
    sub = parser.add_subparsers(dest="command")

    p_archive = sub.add_parser("archive", help="归档文件并生成报告")
    p_archive.add_argument("folder", nargs="?", default=None, help="要归档的文件夹路径")
    p_archive.add_argument("--rules", help="归档规则，如 '数据结构:ds,操作系统:os'", default=None)
    p_archive.add_argument("--ext", help="只归档指定扩展名，如 .pdf,.docx", default=None)

    p_undo = sub.add_parser("undo", help="撤销上一次归档")
    p_undo.add_argument("manifest", nargs="?", default=None, help="archive_manifest.json 的路径")

    args = parser.parse_args()

    if not args.command:
        print("\n请选择操作：")
        print("  1. 归档文件并生成报告")
        print("  2. 撤销上一次归档")
        choice = input("请输入 1 或 2：").strip()

        if choice == "1":
            folder = input("请输入要归档的文件夹路径：").strip()
            rules_str = input("请输入归档规则（如 '数据结构:ds,操作系统:os'）：").strip()
            rules = {}
            for pair in rules_str.split(","):
                if ":" in pair:
                    kw, fld = pair.split(":", 1)
                    rules[kw.strip()] = fld.strip()
            if rules:
                archive_files(folder, rules, None)
            else:
                print("错误：归档规则格式不对，应为 '关键词:文件夹名,...'")

        elif choice == "2":
            manifest = input("请输入 archive_manifest.json 的路径：").strip()
            undo_archive(manifest)

        else:
            print("无效选择。")

    elif args.command == "archive":
        folder = args.folder
        if not folder:
            folder = input("请输入要归档的文件夹路径：").strip()

        rules_str = args.rules
        if not rules_str:
            rules_str = input("请输入归档规则（如 '数据结构:ds,操作系统:os'）：").strip()

        rules = {}
        for pair in rules_str.split(","):
            if ":" in pair:
                kw, fld = pair.split(":", 1)
                rules[kw.strip()] = fld.strip()

        if not rules:
            print("错误：归档规则不能为空，格式为 '关键词:文件夹名,...'")
        else:
            archive_files(folder, rules, args.ext)

    elif args.command == "undo":
        manifest = args.manifest
        if not manifest:
            manifest = input("请输入 archive_manifest.json 的路径：").strip()
        undo_archive(manifest)
