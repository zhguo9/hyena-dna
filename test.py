from Bio import SeqIO

# Specify the path to your FASTA file
fasta_file_path = "C:\\Users\silence\Documents\git\hyena-dna\data\\fna\gene.fna"

# Use SeqIO to read the FASTA file
sequences = SeqIO.to_dict(SeqIO.parse(fasta_file_path, "fasta"))

# Access individual sequences using their IDs
for seq_id, sequence in sequences.items():
    print(f"Sequence ID: {seq_id}")
    print(f"Sequence Length: {len(sequence)}")
    print(f"Sequence: {sequence.seq}\n")

# 快速排序

