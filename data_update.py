from unitls import load_bais
from pathlib import Path

if __name__ == "__main__":
    print("Updating IC/IM data...")
    IC_data = load_bais("IC")
    IC_data.to_csv(Path("data/IC_data.csv"), index=False, encoding="utf-8-sig")
    IM_data = load_bais("IM")
    IM_data.to_csv(Path("data/IM_data.csv"), index=False, encoding="utf-8-sig")
