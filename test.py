import torch
import time
import os
# 设置使用的GPU编号
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

# 创建随机张量
size = 1000000000  # 大小可根据需要进行调整
a = torch.randn(size).cuda()

# 定义一个简单的模型
class SimpleModel(torch.nn.Module):
    def __init__(self):
        super(SimpleModel, self).__init__()

    def forward(self, x):
        return torch.sqrt(x)

# 创建模型并将其移至GPU
model = SimpleModel().cuda()

# 测试GPU负荷
iterations = 1000
start_time = time.time()

for _ in range(iterations):
    output = model(a)

end_time = time.time()
elapsed_time = end_time - start_time
print(f"Average time per iteration: {elapsed_time / iterations:.5f} seconds")
