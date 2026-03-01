pipeline {
    agent {
        label 'docker-agent'
    }
    
    environment {
        DOCKER_HUB = credentials('docker-hub-credentials')
        GITHUB = credentials('github-credentials')
        ARGOCD_PASSWORD = credentials('argocd-password')
        DOCKER_IMAGE = "bobiaditya03/myapp"
        KUBECONFIG = "/home/jenkins/.kube/config"
        ARGOCD_SERVER = "host.docker.internal:30001"
    }
    
    stages {
        stage('Checkout') {
            steps {
                cleanWs()
                checkout scm
                script {
                    env.GIT_COMMIT_SHORT = sh(
                        script: 'git rev-parse --short HEAD',
                        returnStdout: true
                    ).trim()
                    env.BUILD_TAG = "${BUILD_NUMBER}-${GIT_COMMIT_SHORT}"
                }
            }
        }
        
        stage('Build Docker Image') {
            steps {
                sh """
                    cd src
                    docker build -t ${DOCKER_IMAGE}:${BUILD_TAG} .
                    docker tag ${DOCKER_IMAGE}:${BUILD_TAG} ${DOCKER_IMAGE}:latest
                """
            }
        }
        
        stage('Test') {
            steps {
                sh """
                    docker run --rm ${DOCKER_IMAGE}:${BUILD_TAG} python -c "import app; print('Import OK')"
                    
                    docker run -d --name test-${BUILD_NUMBER} -p 5001:5000 ${DOCKER_IMAGE}:${BUILD_TAG}
                    sleep 5
                    curl -f http://localhost:5001/health || (docker logs test-${BUILD_NUMBER} && exit 1)
                    docker stop test-${BUILD_NUMBER} && docker rm test-${BUILD_NUMBER}
                """
            }
        }
        
        stage('Push to Docker Hub') {
            steps {
                sh """
                    echo \$DOCKER_HUB_PSW | docker login -u \$DOCKER_HUB_USR --password-stdin
                    docker push ${DOCKER_IMAGE}:${BUILD_TAG}
                    docker push ${DOCKER_IMAGE}:latest
                    docker logout
                """
            }
        }
        
        stage('Update Manifests') {
            steps {
                sh """
                    git config --global user.email "jenkins@homelab.local"
                    git config --global user.name "Jenkins CI"
                    
                    cd k8s/overlays/dev
                    kustomize edit set image myapp=${DOCKER_IMAGE}:${BUILD_TAG}
                    
                    cd ../../..
                    git add k8s/overlays/dev/kustomization.yaml
                    git commit -m "Update image to ${BUILD_TAG} [ci skip]" || echo "No changes"
                    
                    git push https://\$GITHUB_USR:\$GITHUB_PSW@github.com/YOUR_USERNAME/myapp.git HEAD:main
                """
            }
        }
        
        stage('Sync ArgoCD') {
            steps {
                sh """
                    argocd login ${ARGOCD_SERVER} \
                        --username admin \
                        --password \$ARGOCD_PASSWORD \
                        --insecure \
                        --grpc-web
                    
                    argocd app get myapp-dev || argocd app create -f argocd/application.yaml
                    argocd app sync myapp-dev --force
                    argocd app wait myapp-dev --health --timeout 300
                """
            }
        }
        
        stage('Verify') {
            steps {
                sh """
                    kubectl get pods -n dev
                    kubectl get svc -n dev
                """
            }
        }
    }
    
    post {
        always {
            sh """
                docker rmi ${DOCKER_IMAGE}:${BUILD_TAG} || true
                docker rmi ${DOCKER_IMAGE}:latest || true
                docker ps -aq --filter "name=test-${BUILD_NUMBER}" | xargs -r docker rm -f || true
            """
            cleanWs()
        }
        success {
            echo "✅ SUCCESS! App: http://localhost:30000"
        }
        failure {
            echo "❌ FAILED!"
        }
    }
}
