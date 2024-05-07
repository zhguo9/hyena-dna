import numpy as np
import csv
import torch
import torch.nn as nn
import tqdm
import os
import torch.nn.functional as F
from torch.optim.lr_scheduler import LambdaLR
import hydra
from torch.utils.data import Dataset, DataLoader
from omegaconf import DictConfig
from torchvision import datasets, transforms
import os
import sys
import datetime
import logging
import warnings
from src.processData.process import find_sequence_at_positions
# Get file name as an argument
import argparse
current_dir = os.path.dirname(os.path.abspath(__file__))
path_dna = os.path.join(current_dir, 'data\\processedData\\output.txt')
path_data_dir = os.path.join(current_dir, 'data\\sourceData\\')
checkpoint_dir = os.path.join(current_dir, 'checkoutpoints')

mapping = {0: 'A', 1: 'C', 2: 'G', 3: 'T'}

@hydra.main(config_path="configs", config_name="config.yaml", version_base="1.1")
def inference(cfg: DictConfig) -> None:
    fna_path = cfg.fna_path
    print(fna_path)
    tsv_path = fna_path.replace(".fna", ".tsv")
    find_sequence_at_positions(fna_path, tsv_path, )

    model = Se

    # 创建模型
    dna_encoder = DNAFeatureExtractor(cfg.dna_extractor.voca_size,
                                      cfg.dna_extractor.embedding_dim,
                                      cfg.dna_extractor.num_filter,
                                      cfg.dna_extractor.filter_size,
                                      )
    dna_encoder.to(device)
    model = BILSTMCRF(4, 2)
    model.to(device)

    # 加载模型参数
    encoder_file = "encoder_epoch_100.pt"
    checkpoint_path = os.path.join(checkpoint_dir, encoder_file)
    if os.path.exists(checkpoint_path):
        # 加载模型参数
        dna_encoder.load_state_dict(torch.load(checkpoint_path))
        print(f"Encoder parameters loaded from checkpoint file: {checkpoint_path}")

    checkpoint_file = "lstm_epoch_100.pt"
    checkpoint_path = os.path.join(checkpoint_dir, checkpoint_file)
    if os.path.exists(checkpoint_path):
        # 加载模型参数
        model.load_state_dict(torch.load(checkpoint_path))
        print(f"Model parameters loaded from checkpoint file: {checkpoint_path}")

    # 加载待推理的数据集
    inference_dataset = DNADataset(file_path=path_dna, seq_length=32)
    inference_loader = DataLoader(inference_dataset, batch_size=cfg.batch_size, shuffle=False)

    # 推理过程
    model.eval()  # 将模型设置为评估模式，关闭 dropout 和 batch normalization
    dna_encoder.eval()
    words = []
    predictions = []
    total = 30
    i = 0
    for data in inference_loader:
        # print(data)
        if i > total:
            break
        else:
            i = i + 1
        tmp = data.tolist()
        words.append(tmp)
        inputs = data.to(device)
        data = data.to(device)
        f, x = dna_encoder(data)
        outputs = model.predict(x)
        # print("intput:",inputs[0],
        #       "output:",outputs[0])
        predictions.append(outputs)
    words = np.array(words)
    words = words.flatten()
    predictions = np.array(predictions)
    predictions = predictions.flatten()
    # print(words.shape, predictions.shape)
    start = 0
    end = 0
    result = []
    for i in range(len(predictions)):
        if predictions[i] == 1:
            pass
        else:
            end = i
            fragment = "".join(mapping[n] for n in words[start:end])
            result.append(fragment)
            start = end
    # print(predictions[0:100],predictions.shape)
    begin_position = 16
    correct = 0
    whole = 0
    for i in range(200):
        if predictions[begin_position] == 1:
            correct += 1
        else:
            pass
        begin_position += 32
        whole += 1
        if begin_position > len(predictions):
            break
    # print(correct, whole, correct / whole)
    # 准确率
    print(correct / whole)
    # 词长
    # print(6144/len(result))
    correct = 0
    whole = 0
    for i in range(0, 32 * 10, 32):
        group = predictions[i: i + 32]
        if group[16] == 1:
            pass
        else:
            correct += 1
        whole
    # print(result)
    # for r in result:
    #     print(r)
    # file_path = "C:\\Guo\\Git\\transfer-dna\\result.csv"
    # try:
    #     with open(file_path, "w", newline="") as f:
    #         writer = csv.writer(f)
    #         for word in result:
    #             # print(word)
    #             writer.writerow([word])
    #     print("分词结果已保存到文件:", file_path)
    # except Exception as e:
    #     print("写入文件时出错:", e)



if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=UserWarning)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    inference()
