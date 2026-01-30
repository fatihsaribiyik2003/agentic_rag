import os
import shutil
from agentic_rag import setup_vectorstore

def build_db():
    print("--- Building Vector Database ---")
    
    # Optional: Clear existing DB to force rebuild
    if os.path.exists("./chroma_db"):
        print("Removing existing chroma_db...")
        shutil.rmtree("./chroma_db")
        
    setup_vectorstore(data_dir="./database", persist_dir="./chroma_db")
    print("--- Build Complete ---")

if __name__ == "__main__":
    build_db()
