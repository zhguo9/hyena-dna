import numpy as np
import hydra
from omegaconf import DictConfig
from src.processData.process import find_sequence_at_positions
@hydra.main(config_path="configs", config_name="config.yaml", version_base="1.1")
def inference(cfg: DictConfig) -> None:
    fna_path = cfg.fna_path
    print(fna_path)
    tsv_path = fna_path.replace(".fna", ".tsv")
    find_sequence_at_positions(fna_path, tsv_path, "C:\Guo\Git\hyena-dna\data\dna_segment\K12\test\dataset_test.tsv")

if __name__ == "__main__":
    pass
    # warnings.filterwarnings("ignore", category=UserWarning)
    # device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # inference()