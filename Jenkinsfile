pipeline {
    agent {
        label 'docker-agent'  // atau label node yang punya docker
    }
    
    environment {
        DOCKER_HUB = credentials('docker-hub-credentials')
        GITHUB = credentials('github-credentials')
        ARGOCD_PASSWORD = credentials('argocd-password')
        GIT_REPO = 'bobieaditya31/myapp'
        DOCKER_IMAGE = 'bobieaditya03/myapp'
    }
    
    stages {
        stage('Checkout') {
            steps {
                cleanWs()
                checkout scm
                script {
                    env.GIT_COMMIT_SHORT = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    env.BUILD_TAG = "${env.BUILD_NUMBER}-${env.GIT_COMMIT_SHORT}"
                }
            }
        }
        
        stage('Build Docker Image') {
            steps {
                sh '''
                    cd src
                    docker build -t ${DOCKER_IMAGE}:${BUILD_TAG} .
                    docker tag ${DOCKER_IMAGE}:${BUILD_TAG} ${DOCKER_IMAGE}:latest
                '''
            }
        }
        
        stage('Test') {
            steps {
                script {
                    sh '''
                        docker run --rm ${DOCKER_IMAGE}:${BUILD_TAG} python -c "import app; print('Import OK')"
                        
                        docker run --rm ${DOCKER_IMAGE}:${BUILD_TAG} sh -c "
                            gunicorn --bind 0.0.0.0:5000 app:app --daemon
                            sleep 3
                            wget -qO- http://localhost:5000/health || exit 1
                            echo ' - Health check passed'
                            wget -qO- http://localhost:5000/ || exit 1
                            echo ' - Main endpoint passed'
                        "
                    '''
                }
            }
        }
        
        stage('Push to Docker Hub') {
            steps {
                sh '''
                    echo ${DOCKER_HUB_PSW} | docker login -u ${DOCKER_HUB} --password-stdin
                    docker push ${DOCKER_IMAGE}:${BUILD_TAG}
                    docker push ${DOCKER_IMAGE}:latest
                    docker logout
                '''
            }
        }
        
        stage('Update Manifests') {
            steps {
                sh '''
                    git config --global user.email "jenkins@homelab.local"
                    git config --global user.name "Jenkins CI"
                    
                    cd k8s/overlays/dev
                    kustomize edit set image myapp=${DOCKER_IMAGE}:${BUILD_TAG}
                    cd ../../..
                    
                    git add k8s/overlays/dev/kustomization.yaml
                    git commit -m "Update image to ${BUILD_TAG} [ci skip]"
                    git push https://${GITHUB}@github.com/${GIT_REPO}.git HEAD:main
                '''
            }
        }
        
        stage('Sync ArgoCD') {
            steps {
                sh '''
                    # Install argocd CLI jika belum ada
                    if ! command -v argocd &> /dev/null; then
                        curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
                        chmod +x /usr/local/bin/argocd
                    fi
                    
                    argocd login 172.18.0.2:30001 \
                        --username admin \
                        --password ${ARGOCD_PASSWORD} \
                        --insecure \
                        --grpc-web
                    
                    argocd app sync myapp-dev || true
                '''
            }
        }
    }
    
    post {
        always {
            sh '''
                docker rmi ${DOCKER_IMAGE}:${BUILD_TAG} || true
                docker rmi ${DOCKER_IMAGE}:latest || true
                docker ps -aq --filter name=test-${BUILD_NUMBER} | xargs -r docker rm -f || true
            '''
            cleanWs()
        }
        success {
            echo '✅ SUCCESS!'
        }
        failure {
            echo '❌ FAILED!'
        }
    }
}