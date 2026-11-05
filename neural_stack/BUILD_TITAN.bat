@echo off
TITLE TITAN NEURAL STACK - VERTEX AI DEPLOYMENT
COLOR 0A

:: ==========================================
:: CONFIGURATION (EDIT PROJECT_ID BELOW)
:: ==========================================
SET PROJECT_ID=your-gcp-project-id
SET REGION=us-central1
SET REPO_NAME=titan-audio-repo
SET BUCKET_NAME=titan-audio-staging-%PROJECT_ID%
SET IMAGE_NAME=titan-engine
SET TAG=v1
SET IMAGE_URI=%REGION%-docker.pkg.dev/%PROJECT_ID%/%REPO_NAME%/%IMAGE_NAME%:%TAG%

echo.
echo =======================================================
echo   INITIATING TITAN NEURAL STACK CLOUD DEPLOYMENT
echo   Target: %PROJECT_ID%
echo =======================================================
echo.

:: 1. VERIFY GOOGLE CLOUD SDK IS INSTALLED
gcloud --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Google Cloud SDK is not installed or not in PATH.
    pause
    exit /b
)

:: 2. AUTHENTICATE WITH GOOGLE CLOUD
echo [1/7] Authenticating with Google Cloud...
gcloud auth login --update-adc

:: 3. SET THE ACTIVE PROJECT
echo [2/7] Setting active project to %PROJECT_ID%...
gcloud config set project %PROJECT_ID%

:: 4. ENABLE REQUIRED APIs
echo [3/7] Enabling Vertex AI, Cloud Storage, and Artifact Registry APIs...
gcloud services enable aiplatform.googleapis.com storage.googleapis.com artifactregistry.googleapis.com

:: 5. CREATE GCS BUCKET (For Audio Staging)
echo [4/7] Creating Google Cloud Storage Bucket: %BUCKET_NAME%...
gcloud storage buckets create gs://%BUCKET_NAME% --location=%REGION% >nul 2>&1
echo       (If bucket already exists, proceeding to next step...)

:: 6. CREATE ARTIFACT REGISTRY REPOSITORY
echo [5/7] Creating Artifact Registry Repository...
gcloud artifacts repositories create %REPO_NAME% --repository-format=docker --location=%REGION% --description="Titan Neural Audio Engine" >nul 2>&1
echo       (If repository already exists, proceeding to next step...)

:: 7. CONFIGURE DOCKER & BUILD/PUSH IMAGE
echo [6/7] Configuring Docker authentication for Google Cloud...
gcloud auth configure-docker %REGION%-docker.pkg.dev --quiet

echo [7/7] Building and Pushing Docker Image to Vertex AI (This may take a few minutes)...
docker build -t %IMAGE_URI% .
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker build failed. Make sure Docker Desktop is running.
    pause
    exit /b
)

docker push %IMAGE_URI%

echo.
echo =======================================================
echo   DEPLOYMENT SUCCESSFUL. THE TITAN ENGINE IS ONLINE.
echo =======================================================
echo.
echo   [Bucket]: gs://%BUCKET_NAME%
echo   [Image]:  %IMAGE_URI%
echo.
echo   You can now run the Python trigger script inside Reaper.
echo =======================================================
pause