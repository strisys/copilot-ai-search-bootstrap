import argparse, sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from shared.search import run

def get_args():
   parser = argparse.ArgumentParser(description="")
   args = parser.parse_args()
   return args

if __name__ == "__main__":
   args = get_args()
   run("inflation")

