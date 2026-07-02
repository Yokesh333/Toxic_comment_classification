# GuardianAI - BERT Toxicity Classification Engine

GuardianAI is a deep learning multi-label classification framework powered by a fine-tuned **BERT-base-uncased** model. It predicts and flags toxicity across 6 distinct sub-classes: `toxic`, `severe_toxic`, `obscene`, `threat`, `insult`, and `identity_hate`.

This project is decoupled into a high-performance **FastAPI backend** and a premium, responsive **Vanilla HTML/CSS/JS frontend** using glassmorphic UI elements and micro-animations.

---

## Folder Structure

```
├── backend/
│   ├── app.py              # FastAPI server serving prediction endpoint
│   ├── model.py            # Custom BERT model class definition & loader
│   └── requirements.txt    # Python backend package dependencies
│
├── frontend/
│   ├── index.html          # Semantic dashboard structure
│   ├── style.css           # Custom dark glassmorphism stylesheet
│   └── app.js              # Fetch client and dynamic visualization controller
│
├── .gitignore              # Files to ignore (e.g., model weights, datasets)
├── model.py                # Legacy single-app classification script (backup)
├── app_gradio.py           # Legacy Gradio dashboard (backup)
├── colab_instructions.md   # Script to train/download the model in Google Colab
├── nlp_toxic_comment_fixed.ipynb  # Local Jupyter Notebook workbook
└── README.md               # Project documentation (this file)
```

---

## 🚀 Pushing the Project to GitHub

Because the BERT model weights (`model.safetensors`) are **438MB** and the training set (`train.csv`) is **68MB**, they exceed GitHub's strict **100MB** single file limit and are ignored automatically by `.gitignore`.

Follow these commands to push the codebase to your GitHub repository:

1. **Initialize Git and Stage Files:**
   ```bash
   git init
   git add .
   ```
2. **Commit Changes:**
   ```bash
   git commit -m "feat: restructure to decoupled frontend/backend application"
   ```
3. **Configure Branch and Remote Origin:**
   *Create a new repository on your GitHub account, copy its URL, and paste it below:*
   ```bash
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
   ```
4. **Push code:**
   ```bash
   git push -u origin main
   ```

---

## 🛠️ Local Development Setup

To run the application locally, you will need to start both the Python backend and load the frontend.

### 1. Setup the Model Weights
If you do not have the model weights inside a `best_model` folder:
1. Open a Google Colab GPU session and copy-paste the contents of `colab_instructions.md` to train the model.
2. Download the resulting `best_model.zip` file.
3. Extract the contents of `best_model.zip` into a directory named `best_model` in the root of this project (or inside `backend/best_model`).
4. Ensure the directory contains `config.json`, `model.safetensors`, and tokenizer files.

### 2. Start the Backend API Server
You can run the backend server using one of these options:

#### Option A: Local Python Environment
1. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```
2. (Optional but recommended) Create and activate a python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```
3. Install package requirements:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the server using Uvicorn:
   ```bash
   python app.py
   ```
   *The backend will run on [http://127.0.0.1:8000](http://127.0.0.1:8000).*

#### Option B: Docker Container (Volume Mounted Weights)
We have included a Dockerfile in the `backend/` folder. Since the model weights are very large, they are excluded from the image build. You should bind-mount them from your host computer during container startup:

1. Build the backend image (optimized for CPU to keep the size small):
   ```bash
   cd backend
   docker build -t guardianai-backend .
   ```
2. Run the container and mount your local `best_model` folder (replace `C:/absolute/path/to/best_model` with the absolute path on your host):
   ```bash
   # On Windows (PowerShell):
   docker run -d -p 8000:8000 -v "C:/absolute/path/to/best_model:/app/best_model" guardianai-backend

   # On Mac/Linux:
   docker run -d -p 8000:8000 -v "$(pwd)/best_model:/app/best_model" guardianai-backend
   ```


### 3. Load the Frontend UI
Since the frontend is built using standard Vanilla HTML, CSS, and JS:
- **Option A (Direct File)**: Simply double-click the [index.html](file:///c:/Users/Yokesh/Downloads/Toxic%20comment/frontend/index.html) file to open it in your web browser.
- **Option B (Local CLI Server)**: Serve it locally from the `frontend/` directory:
  ```bash
  cd frontend
  # Using Python:
  python -m http.server 3000
  # Using Node:
  npx serve
  ```
- **Option C (Docker Container)**: Build and run the lightweight Nginx image:
  ```bash
  cd frontend
  docker build -t guardianai-frontend .
  docker run -d -p 3000:80 guardianai-frontend
  ```
  Open the browser to **http://localhost:3000**.

### 4. Run Both Services using Docker Compose (Recommended)
You can build and start both the frontend and backend services with a single command:

1. Ensure your model weights folder `best_model/` is located in the project root directory.
2. Build and start the services in background mode:
   ```bash
   docker-compose up --build -d
   ```
3. Open your browser to **http://localhost:3000** to use the application. The backend API is automatically exposed on **http://localhost:8000**.
4. To stop the containers:
   ```bash
   docker-compose down
   ```

---

## 🛡️ API Endpoints

- **`GET /api/health`**: Checks if the model weights are loaded and shows CPU/GPU device details.
- **`POST /api/analyze`**: Receives raw text comments and classification confidence threshold. Returns multi-label predictions:
  ```json
  {
    "toxic": { "probability": 0.003, "flagged": false },
    "severe_toxic": { "probability": 0.0001, "flagged": false },
    "obscene": { "probability": 0.001, "flagged": false },
    "threat": { "probability": 0.0005, "flagged": false },
    "insult": { "probability": 0.001, "flagged": false },
    "identity_hate": { "probability": 0.0004, "flagged": false }
  }
  ```
