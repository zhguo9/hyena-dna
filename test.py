def find_sequence_at_positions(fna_file, tsv_file, output_file):
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

    for line in lines:
        parts = line.strip().split('\t')
        if len(parts) >= 3 and parts[8] != "protein-coding":  # 添加筛选条件
            start_position = int(parts[1])
            end_position = int(parts[2])
            if 1 <= start_position <= len(sequence) and 1 <= end_position <= len(
                    sequence) and start_position <= end_position:
                subsequence = sequence[start_position - 1:end_position]
                if len(subsequence) <= 1000:  # 添加长度筛选条件
                    results.append((f"位点 {start_position}-{end_position}", subsequence))

    if not results:
        return "没有找到有效的位点范围"

    # 将结果写入TSV文件
    try:
        with open(output_file, 'w') as out_file:
            for result in results:
                out_file.write(f"{result[0]}\t{result[1]}\n")
    except IOError:
        return "无法写入输出文件"

    return "结果已写入文件"

fna_file = "C:\\Users\\hp\\Desktop\\数据\\test.fna"  # 替换为包含序列信息的FNA文件
tsv_file = "C:\\Users\\hp\\Desktop\\数据\\testtsv.tsv"  # 替换为包含位点信息的TSV文件
output_file = "C:\\Users\\hp\\Desktop\\数据\\output.tsv"   # 指定输出文件名

result = find_sequence_at_positions(fna_file, tsv_file, output_file)
print(result)






输出是不是就可以用了