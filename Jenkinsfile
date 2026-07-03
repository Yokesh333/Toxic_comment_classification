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

                sleep(time: 15, unit: 'SECONDS')

                sh '''
                curl -f http://localhost:8000/api/health
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
