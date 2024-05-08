import numpy as np
import csv
import torch
import json
import torch.nn as nn
import tqdm
import os
import torch.nn.functional as F
from torch.optim.lr_scheduler import LambdaLR
import hydra
from torch.utils.data import Dataset, DataLoader
from omegaconf import DictConfig
import os
import sys
import datetime
import logging
import warnings

current_dir = os.path.dirname(os.path.abspath(__file__))
path_dna = os.path.join(current_dir, 'data\\dna_segment\\K12\\test\\dataset_test.tsv')
path_data_dir = os.path.join(current_dir, 'data\\sourceData\\')
checkpoint_dir = os.path.join(current_dir, 'checkoutpoints')

mapping = {0: 'A', 1: 'C', 2: 'G', 3: 'T'}

def reverse_complement(sequence):
    complement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}
    return ''.join(complement.get(base, base) for base in reversed(sequence))

def inference() -> None:
    # 打开文件
    length = 0
    with open(path_dna) as file:
        # 初始化列表
        first_chars = []

        # 逐行读取文件
        for line in file:
            length = length + 1
            # 提取每行的第一个字符并加入到列表中
            first_char = line.strip()  # strip() 方法用于删除字符串开头和末尾的空白字符
            # print(first_char)
            first_chars.append(first_char)
    # print(i)
    new_list = []

    # 使用循环迭代first_chars列表
    for i in range(length):
        # 将每16个字符合并成一个字符串
        substring = ''.join(first_chars[i])
        substring = substring[:32] + "  |  " + substring[32:]
        # 将合并后的字符串添加到新列表中
        new_list.append(substring)

    for i in new_list:
        print(i)


if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=UserWarning)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    inference()