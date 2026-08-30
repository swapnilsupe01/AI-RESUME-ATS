pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'swapnilsupe01/ai-resume-ats'
        IMAGE_TAG    = "${env.BUILD_NUMBER}"
        PORT         = '8000'
    }

    options {
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
    }

    stages {
        stage('Checkout Source') {
            steps {
                echo 'Checking out source repository...'
                checkout scm
            }
        }

        stage('Code Quality & Linting') {
            steps {
                echo 'Running Python syntax and style checks...'
                sh '''
                    python3 -m pip install --upgrade pip
                    python3 -m pip install flake8
                    flake8 backend/app/ --count --select=E9,F63,F7,F82 --show-source --statistics
                '''
            }
        }

        stage('DevSecOps Security Audit') {
            steps {
                echo 'Running Bandit Static Application Security Testing (SAST)...'
                sh '''
                    python3 -m pip install bandit
                    bandit -r backend/app/ -ll -i || true
                '''
            }
        }

        stage('Unit & ML Pipeline Testing') {
            steps {
                echo 'Running test suite with pytest...'
                sh '''
                    python3 -m pip install -r backend/requirements.txt
                    export PYTHONPATH="${WORKSPACE}/backend:${WORKSPACE}/backend/app"
                    python3 backend/test.py
                '''
            }
        }

        stage('Docker Image Build') {
            steps {
                echo "Building Docker container image: ${DOCKER_IMAGE}:${IMAGE_TAG}..."
                sh """
                    docker build -t ${DOCKER_IMAGE}:${IMAGE_TAG} -t ${DOCKER_IMAGE}:latest .
                """
            }
        }

        stage('Container Smoke & Health Test') {
            steps {
                echo 'Deploying test container for smoke test...'
                sh """
                    docker run -d --name test-ats-container -p 8000:8000 ${DOCKER_IMAGE}:${IMAGE_TAG}
                    sleep 10
                    curl --fail --retry 5 --retry-delay 2 http://localhost:8000/api/health || (docker logs test-ats-container && exit 1)
                    docker stop test-ats-container
                    docker rm test-ats-container
                """
            }
        }
    }

    post {
        always {
            echo 'Cleaning up workspace and stopped containers...'
            sh 'docker rm -f test-ats-container 2>/dev/null || true'
        }
        success {
            echo '✅ CI/CD Pipeline Completed Successfully! Image is ready for deployment.'
        }
        failure {
            echo '❌ CI/CD Pipeline Failed. Check stage logs for details.'
        }
    }
}
