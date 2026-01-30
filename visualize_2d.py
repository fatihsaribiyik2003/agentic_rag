import os
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.cluster import KMeans
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

# Renkler
GREEN = "\033[92m"
BLUE = "\033[94m"
RESET = "\033[0m"

def visualize_2d():
    load_dotenv()
    if "GOOGLE_API_KEY" not in os.environ:
        print("API Key eksik!")
        return

    print(f"{BLUE}1. VERİLER OKUNUYOR...{RESET}")
    pdf_files = [f for f in os.listdir("./database") if f.endswith(".pdf")]
    if not pdf_files:
        print("PDF dosyası bulunamadı.")
        return

    all_chunks = []
    
    # İlk 5 PDF'i alalım (Performans ve görsel netlik için)
    for pdf_file in pdf_files[:5]:
        path = os.path.join("./database", pdf_file)
        print(f" - {pdf_file}")
        try:
            loader = PyPDFLoader(path)
            docs = loader.load()
            splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            splits = splitter.split_documents(docs)
            all_chunks.extend(splits)
        except Exception as e:
            print(f"Hata ({pdf_file}): {e}")

    # Çok fazla nokta olmasın, grafik karışmasın (Max 150 nokta)
    if len(all_chunks) > 150:
        import random
        random.shuffle(all_chunks)
        all_chunks = all_chunks[:150]

    print(f"Toplam {len(all_chunks)} veri noktası görselleştirilecek.")

    print(f"{BLUE}2. VEKTÖRLER OLUŞTURULUYOR...{RESET}")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    chunk_texts = [d.page_content for d in all_chunks]
    vectors = embeddings.embed_documents(chunk_texts)
    X = np.array(vectors)

    print(f"{BLUE}3. BOYUT İNDİRGEME (3072D -> 2D) VE KÜMELEME...{RESET}")
    
    # Önce K-Means ile renkleri belirleyelim
    n_clusters = 4
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    labels = kmeans.fit_predict(X)

    # t-SNE ile 2 Boyuta İndir (Daha iyi görsel ayrıştırma sağlar)
    # Perplexity değerini veri sayısına göre ayarlayalım
    perp = min(30, len(all_chunks) - 1)
    tsne = TSNE(n_components=2, random_state=42, perplexity=perp, init='pca', learning_rate='auto')
    X_2d = tsne.fit_transform(X)

    print(f"{BLUE}4. GRAFİK ÇİZİLİYOR...{RESET}")
    plt.figure(figsize=(10, 8))
    
    # Her kümeyi farklı renkte ve şekilde çiz
    colors = ['#FF5733', '#33FF57', '#3357FF', '#F333FF', '#FFFF33']
    markers = ['o', 's', '^', 'D', 'v']
    
    for i in range(n_clusters):
        # Bu kümeye ait noktaları seç
        mask = labels == i
        plt.scatter(
            X_2d[mask, 0], 
            X_2d[mask, 1], 
            c=colors[i % len(colors)], 
            label=f'Konu Kümesi {i+1}',
            alpha=0.7,
            s=80,
            edgecolors='k',
            marker=markers[i % len(markers)]
        )

    plt.title('PDF Vektörlerinin 2D Uzayda Dağılımı (t-SNE)', fontsize=15)
    plt.xlabel('Boyut 1 (t-SNE)', fontsize=12)
    plt.ylabel('Boyut 2 (t-SNE)', fontsize=12)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.3)
    
    # Bazı noktalara örnek metin ekle (Annotate)
    for i in range(5): # Rastgele 5 noktaya etiket
        idx = np.random.randint(0, len(all_chunks))
        txt = all_chunks[idx].page_content[:20] + "..."
        plt.annotate(txt, (X_2d[idx, 0], X_2d[idx, 1]), fontsize=8, alpha=0.8)

    output_path = "vector_plot_2d.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\n{GREEN}2D Grafik kaydedildi: {output_path}{RESET}")
    print("Not: Noktaların birbirine yakın olması, içeriklerinin benzer olduğunu gösterir.")

if __name__ == "__main__":
    visualize_2d()
