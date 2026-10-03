import os
import argparse
from datetime import datetime


def scan_directory(folder_path, ext_filter=None):
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

    print(f"\n扫描文件夹: {folder_path}")
    if ext_list:
        print(f"过滤扩展名: {', '.join(ext_list)}")
    print("-" * 70)
    print(f"{'文件名':<35} {'大小 (KB)':<12} {'修改时间':<20}")
    print("-" * 70)

    total = 0
    count = 0
    for filename in sorted(os.listdir(folder_path)):
        filepath = os.path.join(folder_path, filename)

        if not os.path.isfile(filepath):
            continue

        if ext_list:
            _, file_ext = os.path.splitext(filename)
            if file_ext.lower() not in ext_list:
                continue

        try:
            size_kb = os.path.getsize(filepath) / 1024
            mtime = os.path.getmtime(filepath)
        except OSError as e:
            print(f"{filename:<35} [无法读取: {e}]")
            continue

        mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        display_name = filename if len(filename) <= 35 else filename[:32] + "..."
        print(f"{display_name:<35} {size_kb:<12.2f} {mtime_str:<20}")
        total += size_kb
        count += 1

    print("-" * 70)
    print(f"共 {count} 个文件，合计 {total:.2f} KB")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="作业文件批量归档脚本 - 需求1：扫描与列出")
    parser.add_argument("folder", nargs="?", default=None, help="要扫描的文件夹路径")
    parser.add_argument("--ext", help="按扩展名过滤，支持多个（逗号分隔），例如 .pdf,.docx", default=None)

    args = parser.parse_args()

    folder = args.folder
    if not folder:
        folder = input("请输入要扫描的文件夹路径：").strip()

    scan_directory(folder, args.ext)
