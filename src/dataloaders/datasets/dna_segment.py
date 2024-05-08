from itertools import islice
from functools import partial
import os
import functools
# import json
# from pathlib import Path
# from pyfaidx import Fasta
# import polars as pl
# import pandas as pd
import torch
import time
import re
from random import randrange, random
import random
import numpy as np
from pathlib import Path

from src.dataloaders.datasets.hg38_char_tokenizer import CharacterTokenizer
from genomic_benchmarks.data_check import info
from genomic_benchmarks.data_check import list_datasets
from genomic_benchmarks.loc2seq import download_dataset
from genomic_benchmarks.dataset_getters import pytorch_datasets
from genomic_benchmarks.data_check import is_downloaded
from src.dataloaders.base import default_data_path

"""

Genomic Benchmarks Dataset, from:
https://github.com/ML-Bioinfo-CEITEC/genomic_benchmarks


"""


# helper functions

def exists(val):
    return val is not None


def identity(t):
    return t


def cast_list(t):
    return t if isinstance(t, list) else [t]


def coin_flip():
    return random() > 0.5


# genomic function transforms

seq_indices_embed = torch.zeros(256).long()
seq_indices_embed[ord('a')] = 0
seq_indices_embed[ord('c')] = 1
seq_indices_embed[ord('g')] = 2
seq_indices_embed[ord('t')] = 3
seq_indices_embed[ord('n')] = 4
seq_indices_embed[ord('A')] = 0
seq_indices_embed[ord('C')] = 1
seq_indices_embed[ord('G')] = 2
seq_indices_embed[ord('T')] = 3
seq_indices_embed[ord('N')] = 4
seq_indices_embed[ord('.')] = -1

one_hot_embed = torch.zeros(256, 4)
one_hot_embed[ord('a')] = torch.Tensor([1., 0., 0., 0.])
one_hot_embed[ord('c')] = torch.Tensor([0., 1., 0., 0.])
one_hot_embed[ord('g')] = torch.Tensor([0., 0., 1., 0.])
one_hot_embed[ord('t')] = torch.Tensor([0., 0., 0., 1.])
one_hot_embed[ord('n')] = torch.Tensor([0., 0., 0., 0.])
one_hot_embed[ord('A')] = torch.Tensor([1., 0., 0., 0.])
one_hot_embed[ord('C')] = torch.Tensor([0., 1., 0., 0.])
one_hot_embed[ord('G')] = torch.Tensor([0., 0., 1., 0.])
one_hot_embed[ord('T')] = torch.Tensor([0., 0., 0., 1.])
one_hot_embed[ord('N')] = torch.Tensor([0., 0., 0., 0.])
one_hot_embed[ord('.')] = torch.Tensor([0.25, 0.25, 0.25, 0.25])

reverse_complement_map = torch.Tensor([3, 2, 1, 0, 4]).long()


def torch_fromstring(seq_strs):
    batched = not isinstance(seq_strs, str)
    seq_strs = cast_list(seq_strs)
    np_seq_chrs = list(map(lambda t: np.fromstring(t, dtype=np.uint8), seq_strs))
    seq_chrs = list(map(torch.from_numpy, np_seq_chrs))
    return torch.stack(seq_chrs) if batched else seq_chrs[0]


# 把字符串转换成对应的序列索引
def str_to_seq_indices(seq_strs):
    seq_chrs = torch_fromstring(seq_strs)
    return seq_indices_embed[seq_chrs.long()]


# 把字符串转换成对应的独热编码
def str_to_one_hot(seq_strs):
    seq_chrs = torch_fromstring(seq_strs)
    return one_hot_embed[seq_chrs.long()]


def seq_indices_to_one_hot(t, padding=-1):
    is_padding = t == padding
    t = t.clamp(min=0)
    one_hot = F.one_hot(t, num_classes=5)
    out = one_hot[..., :4].float()
    out = out.masked_fill(is_padding[..., None], 0.25)
    return out


# augmentations

string_complement_map = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A', 'a': 't', 'c': 'g', 'g': 'c', 't': 'a'}


def string_reverse_complement(seq):
    """
        获取互补链
    """
    rev_comp = ''
    for base in seq[::-1]:
        if base in string_complement_map:
            rev_comp += string_complement_map[base]
        # if bp not complement map, use the same bp
        else:
            rev_comp += base
    return rev_comp


def seq_indices_reverse_complement(seq_indices):
    """
        获取互补的索引编码
    """
    complement = reverse_complement_map[seq_indices.long()]
    return torch.flip(complement, dims=(-1,))


def one_hot_reverse_complement(one_hot):
    """
        获取翻转的独热编码
    """
    *_, n, d = one_hot.shape
    assert d == 4, 'must be one hot encoding with last dimension equal to 4'
    return torch.flip(one_hot, (-1, -2))


class DNASegmentDataset(torch.utils.data.Dataset):
    '''
    Loop thru bed file, retrieve (chr, start, end), query fasta file for sequence.
    Returns a generator that retrieves the sequence.
    '''

    def __init__(
            self,
            split,
            max_length,
            dataset_name="K12",
            d_output=2,  # default binary classification
            dest_path=None,
            tokenizer=None,
            tokenizer_name=None,
            use_padding=None,
            add_eos=False,
            rc_aug=False,
            return_augs=False
    ):

        self.max_length = max_length
        self.use_padding = use_padding
        self.tokenizer_name = tokenizer_name
        self.tokenizer = tokenizer
        self.return_augs = return_augs
        self.add_eos = add_eos
        self.d_output = d_output  # needed for decoder to grab
        self.rc_aug = rc_aug

        # change "val" split to "test".  No val available, just test
        if split == "val":
            split = "test"

        # use Path object
        base_path = Path(dest_path) / dataset_name / split

        self.all_seqs = []
        self.all_labels = []
        label_mapper = {}

        for i, x in enumerate(base_path.iterdir()):
            label_mapper[x.stem] = i

        position = 16

        begin = 0
        iN = 1
        end = 2

        if split == "train":
            base_path = Path(dest_path) / dataset_name / split
            for path in base_path.iterdir():
                # print(path)
                with open(path, "r", encoding="gbk") as f:
                    # 读取一行
                    line = f.readline()
                    random.seed(41)
                    tmp = 0
                    while line:
                        # 随机初始化前面、后面有多少个in（范围在1 ~ 3）
                        # print(len(line), line)
                        # inNumBef = random.randint(1,3)
                        # inNumAft = random.randint(1,3)
                        inNumBef = 1
                        inNumAft = 1
                        # inNumBef = 4
                        # inNumAft = 4
                        # print("inNumBef:",inNumBef,"    inNumAft:",inNumAft)
                        # 把 in 加入
                        for i in range(inNumBef):
                            extra = 'D' + 'D' + 'S'
                            # print(len(line[i: i + position * 2]))
                            self.all_seqs.append((line[i+16: i + 16 + position * 2] + extra))
                            self.all_labels.append(iN)

                        # 把end加入
                        extra =  'D' + "D" + 'S'
                        # print(len())
                        self.all_seqs.append((line[inNumBef+ 16 : inNumBef + 16 + position * 2] + extra))
                        self.all_labels.append(end)

                        # 把 begin 加入
                        extra = 'D' + "D" + 'S'
                        # print(len(line[inNumBef + 1 + 4: inNumBef + 1 + 4 + 32]))
                        self.all_seqs.append((line[inNumBef + 1 + 16 : inNumBef + 1 +  16 + 32] + extra))
                        self.all_labels.append(begin)

                        # 把 in 加入
                        # for i in range(inNumAft):
                        #     extra = 'D' + 'D' + 'S'
                        #     self.all_seqs.append((line[inNumBef + i + 2:inNumBef + i + position * 2 + 2] + extra))
                        #     self.all_labels.append(iN)

                        line = f.readline()
                        # for i in self.all_seqs:
                        #     print(i)
                        # if tmp == 5:
                        #     break
                        # else:
                        #     tmp += 1

        if split == "test":
            base_path = Path(dest_path) / dataset_name / split
            for path in base_path.iterdir():
                # print(path)
                with open(path, "r", encoding="gbk") as f:
                    # 读取一行
                    line = f.readline()
                    random.seed(41)
                    tmp = 0
                    while line:
                        # 随机初始化前面、后面有多少个in（范围在1 ~ 3）
                        extra = 'D' + 'D' + 'S'
                        for i in range (32):
                            print(len(line),line[i : i + 32])
                            self.all_seqs.append((line[i : i + 32] + extra))
                            self.all_labels.append(0)
                        line = f.readline()

    def __len__(self):
        return len(self.all_seqs)

    def __getitem__(self, idx):
        x = self.all_seqs[idx]
        y = self.all_labels[idx]
        match = re.search(r'\d+', x)
        if match:
            position = int(match.group(0))
        else :
            position = 1

        while x and x[-1].isdigit():
            x = x[:-1]
        # position = 11 / position

        # apply rc_aug here if using
        if self.rc_aug and coin_flip():
            x = string_reverse_complement(x)

        seq = self.tokenizer(x,
                             add_special_tokens=False,
                             padding="max_length" if self.use_padding else None,
                             max_length=self.max_length,
                             truncation=True,
                             )  # add cls and eos token (+2)
        seq = seq["input_ids"]  # get input_ids

        # need to handle eos here
        if self.add_eos:
            # append list seems to be faster than append tensor
            seq.append(self.tokenizer.sep_token_id)

        # convert to tensor
        seq = torch.LongTensor(seq)  # hack, remove the initial cls tokens for now
        # need to wrap in list
        target = torch.LongTensor([y])  # offset by 1, includes eos
        # print(seq, target)
        return seq, target


if __name__ == '__main__':
    """Quick test loading dataset.

    example
    python -m src.dataloaders.datasets.genomic_bench_dataset

    """

    max_length = 36  # max len of seq grabbed
    use_padding = True
    dest_path = "../../../data/dna_segment/"

    tokenizer = CharacterTokenizer(
        characters=['A', 'C', 'G', 'T', 'N', 'D', 'S'],
        # not sure why tokenizer needs max len
        model_max_length=max_length + 2,  # add 2 since default adds eos/eos tokens, crop later
        add_special_tokens=False,
        padding_side='left',
    )

    ds = DNASegmentDataset(
        max_length=max_length,
        use_padding=use_padding,
        split='val',  #
        tokenizer=tokenizer,
        tokenizer_name='char',
        dest_path=dest_path,
        # add_eos=False,
    )
    print("len of dataSet:", len(ds))
    it = iter(ds)
    elem = next(it)
    for _ in range(8):  # 这里的 3 表示你想要执行的循环次数
        try:
            elem = next(it)
            print(elem)
        except StopIteration:
            print("Reached the end of the iterator.")
            break


    # print('elem[0].shape', elem[0].shape)
    # print(elem)
    # breakpoint()
