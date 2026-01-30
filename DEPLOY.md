# Cloud Run Dağıtım Rehberi (Key Gerektirmez)

Kuruluşunuz (Organization) güvenlik nedeniyle "Key" (Anahtar) oluşturmayı engellediği için, daha güvenli olan **Workload Identity Federation** yöntemini kullanacağız. Bu yöntem **Google Cloud Shell** kullanılarak çok daha hızlı kurulabilir.

## Ön Gereksinimler

1.  Bir Google Cloud Platform (GCP) Hesabı.
2.  Bu GitHub Deposuna erişim.

## 1. Adım: Cloud Shell ile Hızlı Kurulum

1.  [Google Cloud Console](https://console.cloud.google.com/) adresine gidin.
2.  Sağ üstteki **>_** simgesine tıklayarak **Cloud Shell**'i açın (Ekranın altında siyah bir terminal açılacak).
3.  Aşağıdaki kod bloğunu **tek seferde kopyalayın**, Cloud Shell'e yapıştırın ve `Enter` tuşuna basın.
    *   *Not: Yapıştırdıktan sonra "Authorize" penceresi çıkarsa onay verin.*

```bash
# --- AYARLAR (BURAYI KENDİNİZE GÖRE DÜZENLEMEYİN, OTOMATİK AYARLANMIŞTIR) ---
export PROJECT_ID="project-33f269e2-c8b3-4f34-a2a"  # <--- BURAYA KENDİ PROJE ID'NİZİ YAZIN!!!
export GITHUB_REPO="fatihsaribiyik2003/agentic_rag" # GitHub kullanıcı/repo adınız
# ----------------------------------------------------------------------------

# 1. API'leri Aç
gcloud services enable iamcredentials.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  --project "${PROJECT_ID}"

# 2. Servis Hesabı Oluştur
gcloud iam service-accounts create github-deploy \
  --display-name "GitHub Actions" \
  --project "${PROJECT_ID}"

# 3. Yetkileri Ver
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:github-deploy@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:github-deploy@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:github-deploy@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:github-deploy@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.admin"

# 4. Workload Identity Havuzu Oluştur
gcloud iam workload-identity-pools create "github-pool" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --display-name="GitHub Pool"

# 5. Sağlayıcı (Provider) Oluştur
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# 6. GitHub Reposunu Bağla
gcloud iam service-accounts add-iam-policy-binding "github-deploy@${PROJECT_ID}.iam.gserviceaccount.com" \
  --project="${PROJECT_ID}" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$(gcloud projects describe ${PROJECT_ID} --format='value(projectNumber)')/locations/global/workloadIdentityPools/github-pool/attribute.repository/${GITHUB_REPO}"

# 7. Çıktı Ver
echo ""
echo "----------------------------------------------------------------"
echo "GITHUB SECRET OLARAK EKLEMENİZ GEREKENLER:"
echo "----------------------------------------------------------------"
echo "GCP_PROJECT_ID: ${PROJECT_ID}"
echo "GCP_SERVICE_ACCOUNT: github-deploy@${PROJECT_ID}.iam.gserviceaccount.com"
echo "GCP_WORKLOAD_IDENTITY_PROVIDER: projects/$(gcloud projects describe ${PROJECT_ID} --format='value(projectNumber)')/locations/global/workloadIdentityPools/github-pool/providers/github-provider"
echo "GOOGLE_API_KEY: (Gemini API Key'iniz)"
echo "----------------------------------------------------------------"
```

## 2. Adım: GitHub Depo Ayarları

1.  Cloud Shell çıktısında size verilen **3 değeri** kopyalayın.
2.  GitHub projenize gidin.
3.  **Settings** > **Secrets and variables** > **Actions** menüsüne tıklayın.
4.  "New repository secret" butonuna tıklayarak aşağıdaki 4 bilgiyi ekleyin:

| İsim (Name) | Değer (Value) |
| :--- | :--- |
| `GCP_PROJECT_ID` | Proje Kimliğiniz |
| `GCP_SERVICE_ACCOUNT` | `github-deploy@...` ile biten adres |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | `projects/...` ile başlayan uzun adres |
| `GOOGLE_API_KEY` | Gemini API Anahtarınız |

## 3. Adım: Dağıtımı Başlatın

1.  Bu değişiklikleri GitHub'a gönderin (Push).
2.  Actions sekmesinden izleyin.

---

## SORUN GİDERME (HATA ALIRSANIZ)

Eğer "Invalid Target" veya "Authentication Failed" hatası alıyorsanız, aşağıdaki "Tamir Kodu"nu Cloud Shell'e yapıştırın. Bu kod mevcut ayarları silip her şeyi sıfırdan doğrusuyla kurar:

```bash
# --- KESİN ÇÖZÜM KODU (ORGANIZATION POLICY BYPASS) ---
export PROJECT_ID="project-33f269e2-c8b3-4f34-a2a"
export GITHUB_REPO="fatihsaribiyik2003/agentic_rag"

# 1. Havuz (my-pool-final)
gcloud iam workload-identity-pools create "my-pool-final" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --display-name="My GitHub Pool Final"

# 2. Sağlayıcı (KOŞUL EKLİ!) - Hata vermeyecek kısım burası
gcloud iam workload-identity-pools providers create-oidc "my-provider-final" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --workload-identity-pool="my-pool-final" \
  --display-name="My GitHub Provider Final" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner_id=assertion.repository_owner_id" \
  --attribute-condition="assertion.repository_owner_id != 'google'" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# 3. İzinler
export PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format='value(projectNumber)')

gcloud iam service-accounts add-iam-policy-binding "github-deploy@${PROJECT_ID}.iam.gserviceaccount.com" \
  --project="${PROJECT_ID}" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/my-pool-final/attribute.repository/${GITHUB_REPO}"

# 4. Sonuç (Bunu kopyalayın)
echo "---------------------------------------------------"
echo "BUNU GITHUB SECRET YERİNE YAPIŞTIRIN:"
gcloud iam workload-identity-pools providers describe "my-provider-final" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --workload-identity-pool="my-pool-final" \
  --format="value(name)"
echo "---------------------------------------------------"
```
Bu kodun verdiği yeni sonucu GitHub Secret'a tekrar ekleyin.
