import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
import pytorch_lightning as pl
class LargeDataset(Dataset):
    def __init__(self, size=1000000, input_size=100):
        self.data = torch.randn(size, input_size)
        self.labels = torch.randint(0, 2, (size,), dtype=torch.float32)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        return self.data[index], self.labels[index]

class LargeModel(nn.Module):
    def __init__(self, input_size=100, hidden_size=1000, output_size=1):
        super(LargeModel, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = self.fc2(x)
        return x

class LargeLightningModule(pl.LightningModule):
    def __init__(self, config):
        super(LargeLightningModule, self).__init__()
        self.save_hyperparameters(config)
        self.dataset = LargeDataset(size=config["data_size"])
        self.model = LargeModel()

    def forward(self, x):
        return self.model(x)

    def training_step(self, batch, batch_idx):
        x, y = batch
        output = self(x)
        y = y.unsqueeze(1)
        loss = F.binary_cross_entropy_with_logits(output, y)
        gpu_memory_allocated = torch.cuda.memory_allocated(device=0)  # 0 是 GPU 设备的索引
        gpu_memory_cached = torch.cuda.memory_cached(device=0)

        # 打印 GPU 内存占用
        print(f"GPU Memory Allocated: {gpu_memory_allocated / 1e9:.2f} GB")
        print(f"GPU Memory Cached: {gpu_memory_cached / 1e9:.2f} GB")
        return loss

    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=self.hparams.learning_rate)

if __name__ == "__main__":
    import pytorch_lightning as pl
    from torch.nn import functional as F

    config = {
        "data_size": 1000000,
        "learning_rate": 0.001,
    }

    model = LargeLightningModule(config)
    model.to('cuda')
    trainer = pl.Trainer(gpus=1)
    trainer.fit(model, DataLoader(model.dataset, batch_size=64, num_workers=4))
