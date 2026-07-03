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
                sh 'docker compose version || docker-compose --version'
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
                docker compose up --build -d || docker-compose up --build -d
                '''

                sh '''
                COMPOSE_CMD="docker compose"
                if ! docker compose version >/dev/null 2>&1; then
                    COMPOSE_CMD="docker-compose"
                fi

                echo "Waiting for backend to start and load model..."
                for i in {1..20}; do
                    echo "Checking backend health (attempt $i)..."
                    if $COMPOSE_CMD exec -T backend python -c "import urllib.request, json, sys; res = urllib.request.urlopen('http://localhost:8000/api/health', timeout=5); data = json.loads(res.read().decode()); sys.exit(0 if data.get('status') == 'online' else 1)" >/dev/null 2>&1; then
                        echo "Backend is healthy!"
                        exit 0
                    fi
                    sleep 5
                done
                echo "Error: Backend failed to respond to health check after 100 seconds."
                exit 1
                '''

                echo 'Integration Test Passed'
            }
        }
    }

    post {

        always {
            echo 'Cleaning up containers...'

            sh '''
            docker compose down --remove-orphans || docker-compose down --remove-orphans || true
            '''
        }

        success {
            echo 'Pipeline completed successfully.'
        }

        failure {
            echo 'Pipeline failed. Check the console logs.'
        }
    }
}
