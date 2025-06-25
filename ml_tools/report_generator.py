import matplotlib.pyplot as plt
import pandas as pd

def generate_report(log_file_path):
    success = []
    with open(log_file_path, "r") as f:
        for line in f:
            if "成功" in line:
                success.append(1)
            elif "失敗" in line:
                success.append(0)

    if not success:
        return

    df = pd.Series(success)
    plt.figure(figsize=(8, 4))
    df.rolling(5).mean().plot(label="成功率移動平均")
    plt.title("攻擊成功率趨勢")
    plt.xlabel("封包數")
    plt.ylabel("成功率")
    plt.legend()
    plt.tight_layout()
    plt.savefig(log_file_path.replace(".log", ".png"))
