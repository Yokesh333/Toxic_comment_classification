pipeline {
    agent any

    environment {
        GITHUB_REPO = 'https://github.com/Yokesh333/Toxic_comment_classification.git'
    }

    stages {

        stage('Checkout Source') {
            steps {
                echo 'Cloning GitHub Repository...'

                git branch: 'main',
                    url: "${GITHUB_REPO}"
            }
        }

        stage('Verify Environment') {
            steps {
                echo 'Checking Docker installation...'
                sh 'docker --version'

                echo 'Checking Docker Compose installation...'
                sh '''
                if docker compose version >/dev/null 2>&1; then
                    echo "docker compose is available"
                elif docker-compose --version >/dev/null 2>&1; then
                    echo "docker-compose is available"
                else
                    echo "Docker Compose not found. Downloading standalone binary..."
                    if command -v curl >/dev/null 2>&1; then
                        curl -SL "https://github.com/docker/compose/releases/download/v2.29.1/docker-compose-linux-x86_64" -o ./docker-compose
                    elif command -v wget >/dev/null 2>&1; then
                        wget -q "https://github.com/docker/compose/releases/download/v2.29.1/docker-compose-linux-x86_64" -O ./docker-compose
                    else
                        echo "Error: Neither curl nor wget found to download docker-compose."
                        exit 1
                    fi
                    chmod +x ./docker-compose
                    ./docker-compose version
                fi
                '''

                echo 'Checking Model Weights...'
                sh '''
                mkdir -p ./best_model
                if [ ! -f ./best_model/model.safetensors ]; then
                    echo "Model weights (model.safetensors) missing from workspace."
                    if [ -n "${MODEL_URL}" ]; then
                        echo "Downloading model weights from ${MODEL_URL}..."
                        if command -v curl >/dev/null 2>&1; then
                            curl -SL "${MODEL_URL}" -o ./best_model/model.safetensors
                        elif command -v wget >/dev/null 2>&1; then
                            wget -q "${MODEL_URL}" -O ./best_model/model.safetensors
                        else
                            echo "Error: Neither curl nor wget found to download model weights."
                            exit 1
                        fi
                    else
                        echo "Error: model.safetensors is missing and the MODEL_URL environment variable is not set."
                        echo "Please copy the weights file manually to the Jenkins agent, or configure MODEL_URL."
                        exit 1
                    fi
                else
                    echo "Model weights (model.safetensors) found."
                fi
                '''
            }
        }

        stage('Build Backend Image') {
            steps {
                dir('backend') {
                    sh '''
                    docker build \
                    -t guardianai-backend:latest \
                    .
                    '''
                }
            }
        }

        stage('Build Frontend Image') {
            steps {
                dir('frontend') {
                    sh '''
                    docker build \
                    -t guardianai-frontend:latest \
                    .
                    '''
                }
            }
        }

        stage('Integration Test') {
            steps {
                echo 'Starting application using Docker Compose...'

                sh '''
                COMPOSE_CMD="docker compose"
                if ! docker compose version >/dev/null 2>&1; then
                    if docker-compose --version >/dev/null 2>&1; then
                        COMPOSE_CMD="docker-compose"
                    else
                        COMPOSE_CMD="./docker-compose"
                    fi
                fi

                $COMPOSE_CMD up --build -d

                echo "Waiting for backend to start and load model..."
                i=1
                while [ $i -le 20 ]; do
                    echo "Checking backend health (attempt $i)..."
                    if $COMPOSE_CMD exec -T backend python -c "import urllib.request, json, sys; res = urllib.request.urlopen('http://localhost:8000/api/health', timeout=5); data = json.loads(res.read().decode()); sys.exit(0 if data.get('status') == 'online' else 1)" >/dev/null 2>&1; then
                        echo "Backend is healthy!"
                        exit 0
                    fi
                    sleep 5
                    i=$((i+1))
                done
                echo "Error: Backend failed to respond to health check after 100 seconds."
                exit 1
                '''

                sh '''
                COMPOSE_CMD="docker compose"
                if ! docker compose version >/dev/null 2>&1; then
                    if docker-compose --version >/dev/null 2>&1; then
                        COMPOSE_CMD="docker-compose"
                    else
                        COMPOSE_CMD="./docker-compose"
                    fi
                fi
                echo "=== Files in Backend Model Directory ==="
                $COMPOSE_CMD exec -T backend ls -la /app/best_model || true
                echo "=== Backend Container Logs ==="
                $COMPOSE_CMD logs backend
                echo "=== End Backend Logs ==="
                '''

                echo 'Integration Test Passed'
            }
        }
    }

    post {

        success {
            echo 'Pipeline completed successfully.'
        }

        failure {
            echo 'Pipeline failed. Check the console logs. Cleaning up containers...'
            sh '''
            COMPOSE_CMD="docker compose"
            if ! docker compose version >/dev/null 2>&1; then
                if docker-compose --version >/dev/null 2>&1; then
                    COMPOSE_CMD="docker-compose"
                else
                    COMPOSE_CMD="./docker-compose"
                fi
            fi
            $COMPOSE_CMD down --remove-orphans || true
            '''
        }
    }
}
