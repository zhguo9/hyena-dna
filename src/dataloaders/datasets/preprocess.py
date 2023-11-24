def find_sequence_at_positions(fna_file, tsv_file, output_file):
    # 读取序列信息
    try:
        with open(fna_file, 'r') as file:
            sequence = "".join(line.strip() for line in file.readlines() if not line.startswith(">"))
    except FileNotFoundError:
        return "FNA文件不存在或无法读取"

    print(len(sequence))

    # 读取位点信息并查找序列
    try:
        with open(tsv_file, 'r') as file:
            lines = file.readlines()
    except FileNotFoundError:
        return "TSV文件不存在"

    results = []
    gene_gaps = []

    for line in lines:
        parts = line.strip().split('\t')
        # 如果不是编码区域
        if len(parts) >= 3 and parts[8] != "protein-coding":  # 添加筛选条件
            start_position = int(parts[1])
            end_position = int(parts[2])
            strand = parts[4]  # 提取正反链信息

            if 1 <= start_position <= len(sequence) and 1 <= end_position <= len(
                    sequence) and start_position <= end_position:
                subsequence = sequence[start_position - 1:end_position]

                if strand == "minus":  # 处理反向序列
                    subsequence = reverse_complement(subsequence)

                if len(subsequence) <= 1000:  # 添加长度筛选条件
                    results.append((f"{start_position}", f"{end_position}", subsequence))

    # 寻找基因间隔区
    gene_positions = [(parts[0], int(parts[1]), int(parts[2])) for parts in lines if
                      len(parts) >= 3 and parts[8] == "protein-coding"]
    gene_positions.sort(key=lambda x: x[1])  # 按基因起始位置升序排序

    for i in range(len(gene_positions) - 1):
        current_gene_end = gene_positions[i][2]
        next_gene_start = gene_positions[i + 1][1]
        gap_length = next_gene_start - current_gene_end
        gene_gaps.append((current_gene_end, next_gene_start, gap_length))

    if not results:
        return "没有找到有效的位点范围"

    # 将结果写入TSV文件
    try:
        with open(output_file, 'w') as out_file:
            for result in results:
                out_file.write(f"{result[0]}\t{result[1]}\t{result[2]}\n")

            out_file.write("\n间隔区信息:\n")
            for gap in gene_gaps:
                out_file.write(f"起始位置 {gap[0]}, 结束位置 {gap[1]}, 长度 {gap[2]}\n")
    except IOError:
        return "无法写入输出文件"

    return "结果已写入文件: " + output_file


def reverse_complement(sequence):
    complement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}
    return ''.join(complement.get(base, base) for base in reversed(sequence))


fna_file = "test.fna"  # 替换为包含序列信息的FNA文件
tsv_file = "testtsv.tsv"  # 替换为包含位点信息的TSV文件
output_file = "processed.tsv"  # 指定输出文件名

result = find_sequence_at_positions(fna_file, tsv_file, output_file, )

print(result)

##在更新的程序中，添加了一个名为 gene_gaps 的列表，用于存储基因间隔区的信息。
#在遍历位点信息时，筛选出 parts[8] 不等于 "protein-coding" 的部分，这样可以将非编码基因位置排除在基因间隔区的计算之外。
# 然后，我根据基因位置信息计算基因间隔区的起始位置、结束位置和长度，并将其存储在 gene_gaps 列表中。
##最后，在将结果写入输出文件时，我添加了一个额外的部分，将基因间隔区的信息写入文件。
