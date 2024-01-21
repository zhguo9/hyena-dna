import random
def find_sequence_at_positions(fna_file, tsv_file, output_file):
    prefix = 15
    suffix = 15
    # 读取序列信息
    try:
        with open(fna_file, 'r') as file:
            sequence = "".join(line.strip() for line in file.readlines() if not line.startswith(">"))
    except FileNotFoundError:
        return "FNA文件不存在或无法读取"
    # 读取位点信息并查找序列
    try:
        with open(tsv_file, 'r') as file:
            lines = file.readlines()
    except FileNotFoundError:
        return "TSV文件不存在"

    results = []
    hashTable = set()
    i = 1
    for line in lines:
        # print(i)
        i = i + 1
        parts = line.strip().split('\t')
        # print(parts)
        if len(parts) >= 3 and parts[8] != "protein-coding":  # 添加筛选条件
            start_position = int(parts[1])
            end_position = int(parts[2])
            strand = parts[4]  # 提取正反链信息
            # 筛去重复的行
            if start_position in hashTable:
                continue
            else:
                hashTable.add(start_position)
            # print(start_position)
            # print(hashTable)
            # if 1 <= start_position <= len(sequence) and 1 <= end_position <= len(sequence) and start_position <= end_position:
            # 把start附近的截取
            subsequence = sequence[start_position - prefix: start_position + suffix]
            if strand == "minus":  # 处理反向序列
                subsequence = reverse_complement(subsequence)
            if len(subsequence) <= 1000:  # 添加长度筛选条件
                subsequence_with_context = f"{subsequence}"
                results.append(subsequence_with_context)
                print(subsequence)
                print(start_position)

            # 把end前后的截取
            subsequence = sequence[end_position - prefix + 1: end_position + suffix + 1]
            if strand == "minus":  # 处理反向序列
                subsequence = reverse_complement(subsequence)
            if len(subsequence) <= 1000:
                subsequence_with_context = f"{subsequence}"
                results.append(subsequence_with_context)
                print(subsequence)
                print(end_position)


    if not results:
        return "没有找到有效的位点范围"

    # 将结果写入TSV文件
    try:
        with open(output_file, 'a') as out_file:
            for result in results:
                out_file.write(f"{result}\n")
    except IOError:
        return "无法写入输出文件"

    return "结果已写入文件"


def reverse_complement(sequence):
    complement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}
    return ''.join(complement.get(base, base) for base in reversed(sequence))


fna_file = "../../数据集/K12/test.fna"  # 替换为包含序列信息的FNA文件
tsv_file = "../../数据集/K12/testtsv.tsv"  # 替换为包含位点信息的TSV文件
output_file = "../../data/dna_segment/K12/train/dataset_train.tsv"  # 指定输出文件名

import os


def process_files_in_folder(folder_path):
    for root, dirs, files in os.walk(folder_path):
        print(root)
        for file in files:
            if file.endswith(".fna"):
                fna_file = os.path.join(root, file)
                tsv_file = file.replace(".fna", "tsv.tsv")  # Assuming corresponding tsv files have the same name with different extension
                tsv_file = os.path.join(root, tsv_file)
                output_file = "C:\\Users\silence\Documents\git\hyena-dna\\tmp.tsv"

                result = find_sequence_at_positions(fna_file, tsv_file, output_file)
                print(result)

    # 去除重复行
    unique_lines = set()  # 用于存储唯一的行

    try:
        # 读取文件并去除重复行
        with open(output_file, 'r') as in_file:
            for line in in_file:
                unique_lines.add(line.strip())  # 添加去除空格的行到集合中

        # 将唯一行写入新文件
        datafile = "C:\\Users\silence\Documents\git\hyena-dna\\dataset.tsv"
        with open(datafile, 'w') as out_file:
            for line in unique_lines:
                out_file.write(f"{line}\n")

        return f"去除重复行后的内容已保存到 {datafile} 文件中。"

    except IOError:
        return "处理文件时出错。"
# 请替换下面的路径为您的实际路径
base_folder = "C:\\Users\silence\Documents\git\hyena-dna\segg"

process_files_in_folder(base_folder)