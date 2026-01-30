# Cloud Run Dağıtım Rehberi

Bu rehber, dahil edilen GitHub Actions iş akışını kullanarak bu uygulamayı Google Cloud Run'a nasıl dağıtacağınızı (deploy edeceğinizi) açıklar.

## Ön Gereksinimler

1.  Bir Google Cloud Platform (GCP) Hesabı.
2.  Bu GitHub Deposuna (Repository) erişim.

## 1. Adım: Google Cloud Kurulumu

1.  **Proje Oluşturun**:
    *   [Google Cloud Console](https://console.cloud.google.com/) adresine gidin.
    *   Yeni bir proje oluşturun (örneğin: `agentic-rag-prod`).
    *   **Project ID** (Proje Kimliği) değerini bir kenara not edin (örneğin: `agentic-rag-prod-12345`).

2.  **API'leri Etkinleştirin**:
    *   Menüden "APIs & Services" > "Enabled APIs & services" kısmına gidin.
    *   "+ ENABLE APIS AND SERVICES" butonuna tıklayın.
    *   Aşağıdaki servisleri aratıp etkinleştirin (Enable):
        *   **Cloud Run Admin API**
        *   **Container Registry API** (veya Artifact Registry API)
        *   **Cloud Build API** (isteğe bağlı, ama önerilir)

3.  **Servis Hesabı (Service Account) Oluşturun**:
    *   "IAM & Admin" > "Service Accounts" kısmına gidin.
    *   "+ CREATE SERVICE ACCOUNT" butonuna tıklayın.
    *   İsim: `github-deploy` (veya istediğiniz bir isim).
    *   **Roller (Roles)**: Aşağıdaki yetkileri verin:
        *   `Cloud Run Admin`
        *   `Service Account User`
        *   `Storage Admin` (Container Registry için)
    *   "Done" diyerek bitirin.

4.  **Anahtar (Key) Oluşturun**:
    *   Yeni oluşturduğunuz servis hesabına tıklayın (örn: `github-deploy@...`).
    *   "Keys" sekmesine gelin.
    *   "Add Key" > "Create new key" seçeneğini tıklayın ve **JSON** formatını seçin.
    *   Dosya bilgisayarınıza inecek. **Bu dosyayı kaybetmeyin ve kimseyle paylaşmayın!**

## 2. Adım: GitHub Depo Ayarları

1.  GitHub projenize gidin.
2.  **Settings** > **Secrets and variables** > **Actions** menüsüne tıklayın.
3.  "New repository secret" butonuna tıklayarak aşağıdaki 3 bilgiyi ekleyin:

| İsim (Name) | Değer (Value) |
| :--- | :--- |
| `GCP_PROJECT_ID` | Proje Kimliğiniz (1.1. adımda not ettiğiniz) |
| `GCP_SA_KEY` | İndirdiğiniz JSON dosyasının *tüm içeriğini* kopyalayıp buraya yapıştırın. |
| `GOOGLE_API_KEY` | Gemini API Anahtarınız (`AIza...` ile başlayan) |

## 3. Adım: Dağıtımı Başlatın

1.  `main` (ana) dalına (branch) herhangi bir değişiklik gönderin (push).
2.  İşlemi canlı izlemek için GitHub'da "Actions" sekmesine gidin.
3.  İşlem bittiğinde, "Deploy to Cloud Run" adımına tıklayarak uygulamanızın **Service URL**'ini (Web Sitesi Linki) görebilirsiniz.

## Maliyet Hakkında Not
*   **Cloud Run**: Sadece kod çalıştığında (siteye istek geldiğinde) ücret ödersiniz.
*   **Container Registry**: Docker imajlarınızın saklanması için çok küçük bir depolama ücreti çıkabilir.
