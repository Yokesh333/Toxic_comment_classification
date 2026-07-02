pipeline {
    agent any

    environment {
        // Change these variables to match your Docker Registry configuration
        DOCKER_REGISTRY_USER = 'your_dockerhub_username'
        BACKEND_IMAGE_NAME   = 'guardianai-backend'
        FRONTEND_IMAGE_NAME  = 'guardianai-frontend'
        IMAGE_TAG            = "${BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out source code...'
                checkout scm
            }
        }

        stage('Verify Environments') {
            steps {
                echo 'Verifying docker and docker-compose tools...'
                sh 'docker --version'
                sh 'docker-compose --version'
            }
        }

        stage('Build Backend') {
            steps {
                echo 'Building Backend Docker Image...'
                dir('backend') {
                    sh "docker build -t ${DOCKER_REGISTRY_USER}/${BACKEND_IMAGE_NAME}:${IMAGE_TAG} -t ${DOCKER_REGISTRY_USER}/${BACKEND_IMAGE_NAME}:latest ."
                }
            }
        }

        stage('Build Frontend') {
            steps {
                echo 'Building Frontend Docker Image...'
                dir('frontend') {
                    sh "docker build -t ${DOCKER_REGISTRY_USER}/${FRONTEND_IMAGE_NAME}:${IMAGE_TAG} -t ${DOCKER_REGISTRY_USER}/${FRONTEND_IMAGE_NAME}:latest ."
                }
            }
        }

        stage('Integration Testing') {
            steps {
                echo 'Starting containers to run API Integration tests...'
                // Spin up the backend and frontend using docker-compose
                sh 'docker-compose up --build -d'
                
                // Allow some time for model initialization
                sleep time: 10, unit: 'SECONDS'
                
                // Check if backend API answers health check successfully
                sh 'curl -f http://localhost:8000/api/health'
                
                // Tear down integration test environment
                sh 'docker-compose down'
            }
        }

        stage('Push Images') {
            /* 
               Uncomment this stage after configuring Jenkins Credentials 
               with ID 'dockerhub-credentials' for pushing to Docker Hub.
            */
            /*
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-credentials', usernameVariable: 'USER', passwordVariable: 'PASSWORD')]) {
                    sh "echo ${PASSWORD} | docker login -u ${USER} --password-stdin"
                    
                    echo 'Pushing Backend Image...'
                    sh "docker push ${DOCKER_REGISTRY_USER}/${BACKEND_IMAGE_NAME}:${IMAGE_TAG}"
                    sh "docker push ${DOCKER_REGISTRY_USER}/${BACKEND_IMAGE_NAME}:latest"
                    
                    echo 'Pushing Frontend Image...'
                    sh "docker push ${DOCKER_REGISTRY_USER}/${FRONTEND_IMAGE_NAME}:${IMAGE_TAG}"
                    sh "docker push ${DOCKER_REGISTRY_USER}/${FRONTEND_IMAGE_NAME}:latest"
                }
            }
            */
            steps {
                echo 'Skipping image push stage (configure credentials to enable).'
            }
        }
    }

    post {
        always {
            echo 'Pipeline execution complete. Cleaning up unused Docker networks and containers...'
            sh 'docker-compose down --remove-orphans || true'
        }
        success {
            echo 'CI/CD pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed. Please check build logs for errors.'
        }
    }
}
