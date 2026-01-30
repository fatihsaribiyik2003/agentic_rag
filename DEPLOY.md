# Cloud Run Deployment Guide

This guide explains how to deploy this application to Google Cloud Run using the included GitHub Actions workflow.

## Prerequisites

1.  A Google Cloud Platform (GCP) Account.
2.  Access to this GitHub Repository.

## Step 1: Google Cloud Setup

1.  **Create a Project**:
    *   Go to [Google Cloud Console](https://console.cloud.google.com/).
    *   Create a new project (e.g., `agentic-rag-prod`).
    *   Note down the **Project ID** (e.g., `agentic-rag-prod-12345`).

2.  **Enable APIs**:
    *   Go to "APIs & Services" > "Enabled APIs & services".
    *   Click "+ ENABLE APIS AND SERVICES".
    *   Search for and enable the following:
        *   **Cloud Run Admin API**
        *   **Container Registry API** (or Artifact Registry API)
        *   **Cloud Build API** (optional, but good practice)

3.  **Create Service Account**:
    *   Go to "IAM & Admin" > "Service Accounts".
    *   Click "+ CREATE SERVICE ACCOUNT".
    *   Name: `github-deploy`.
    *   **Roles**: Grant the following roles:
        *   `Cloud Run Admin`
        *   `Service Account User`
        *   `Storage Admin` (for Container Registry)
    *   Click "Done".

4.  **Create Key**:
    *   Click on the newly created service account (e.g., `github-deploy@...`).
    *   Go to the "Keys" tab.
    *   "Add Key" > "Create new key" > **JSON**.
    *   The file will download automatically. **Keep this safe!**

## Step 2: GitHub Repository Setup

1.  Go to your GitHub repository.
2.  Click **Settings** > **Secrets and variables** > **Actions**.
3.  Click "New repository secret" and add the following:

| Name | Value |
| :--- | :--- |
| `GCP_PROJECT_ID` | Your Project ID (from Step 1.1) |
| `GCP_SA_KEY` | Paste the *entire content* of the JSON key file you downloaded. |
| `GOOGLE_API_KEY` | Your Gemini API Key (starts with `AIza...`) |

## Step 3: Trigger Deployment

1.  Push any change to the `main` branch.
2.  Go to the "Actions" tab in GitHub to watch the deployment.
3.  Once finished, click the "Deploy to Cloud Run" step to see the **Service URL**.

## Cost Note
*   **Cloud Run**: You pay only when the code runs (per request).
*   **Container Registry**: Small storage fee for the Docker images.
