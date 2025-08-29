import argparse
from search import upload_directory
    
def get_args():
   parser = argparse.ArgumentParser(description="Ingest files into Azure AI Search.")
   parser.add_argument("directory", help="Path to the directory of files")
   parser.add_argument("max_chars", type=int, nargs="?", default=1200, help="Max characters per chunk")
   parser.add_argument("overlap", type=int, nargs="?", default=200, help="Number of overlapping chars")

   args = parser.parse_args()
   print(args)

   return args

if __name__ == "__main__":
    args = get_args()

    max_chars = int(args.max_chars) if (args.max_chars) else 1200
    overlap = int(args.overlap) if (args.overlap) else 200

    upload_directory(args.directory, max_chars=max_chars, overlap=overlap)