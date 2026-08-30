pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'swapnilsupe01/ai-resume-ats'
        IMAGE_TAG    = "${env.BUILD_NUMBER ?: 'latest'}"
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
                script {
                    if (isUnix()) {
                        sh '''
                            python3 -m pip install --upgrade pip || pip install --upgrade pip
                            python3 -m pip install flake8 || pip install flake8
                            flake8 backend/app/ --count --select=E9,F63,F7,F82 --show-source --statistics || true
                        '''
                    } else {
                        bat '''
                            python -m pip install --upgrade pip
                            python -m pip install flake8
                            flake8 backend/app/ --count --select=E9,F63,F7,F82 --show-source --statistics || exit 0
                        '''
                    }
                }
            }
        }

        stage('DevSecOps Security Audit') {
            steps {
                echo 'Running Bandit Static Application Security Testing (SAST)...'
                script {
                    if (isUnix()) {
                        sh '''
                            python3 -m pip install bandit || pip install bandit
                            bandit -r backend/app/ -ll -i || true
                        '''
                    } else {
                        bat '''
                            python -m pip install bandit
                            bandit -r backend/app/ -ll -i || exit 0
                        '''
                    }
                }
            }
        }

        stage('Unit & ML Pipeline Testing') {
            steps {
                echo 'Running test suite with Python test runner...'
                script {
                    if (isUnix()) {
                        sh '''
                            python3 -m pip install -r backend/requirements.txt || pip install -r backend/requirements.txt
                            export PYTHONPATH="${WORKSPACE}/backend:${WORKSPACE}/backend/app:${PYTHONPATH}"
                            python3 backend/test.py || python backend/test.py
                        '''
                    } else {
                        bat '''
                            python -m pip install -r backend/requirements.txt
                            set PYTHONPATH=%WORKSPACE%\\backend;%WORKSPACE%\\backend\\app;%PYTHONPATH%
                            python backend/test.py
                        '''
                    }
                }
            }
        }

        stage('Docker Image Build') {
            steps {
                echo "Building Docker container image: ${DOCKER_IMAGE}:${IMAGE_TAG}..."
                script {
                    if (isUnix()) {
                        sh "docker build -t ${DOCKER_IMAGE}:${IMAGE_TAG} -t ${DOCKER_IMAGE}:latest ."
                    } else {
                        bat "docker build -t ${DOCKER_IMAGE}:${IMAGE_TAG} -t ${DOCKER_IMAGE}:latest ."
                    }
                }
            }
        }

        stage('Container Smoke & Health Test') {
            steps {
                echo 'Deploying test container for smoke test...'
                script {
                    if (isUnix()) {
                        sh """
                            docker run -d --name test-ats-container -p 8000:8000 ${DOCKER_IMAGE}:${IMAGE_TAG}
                            sleep 10
                            curl --fail --retry 5 --retry-delay 2 http://localhost:8000/api/health || (docker logs test-ats-container && exit 1)
                            docker stop test-ats-container
                            docker rm test-ats-container
                        """
                    } else {
                        bat """
                            docker run -d --name test-ats-container -p 8000:8000 ${DOCKER_IMAGE}:${IMAGE_TAG}
                            powershell -Command "Start-Sleep -Seconds 10; try { Invoke-RestMethod -Uri http://localhost:8000/api/health } catch { docker logs test-ats-container; exit 1 }"
                            docker stop test-ats-container
                            docker rm test-ats-container
                        """
                    }
                }
            }
        }
    }

    post {
        always {
            echo 'Cleaning up workspace and stopped containers...'
            script {
                if (isUnix()) {
                    sh 'docker rm -f test-ats-container 2>/dev/null || true'
                } else {
                    bat 'docker rm -f test-ats-container 2>nul || ver >nul'
                }
            }
        }
        success {
            echo '✅ Jenkins CI/CD Pipeline Completed Successfully! Image is ready for deployment.'
        }
        failure {
            echo '❌ Jenkins CI/CD Pipeline Failed. Check stage logs for details.'
        }
    }
}


