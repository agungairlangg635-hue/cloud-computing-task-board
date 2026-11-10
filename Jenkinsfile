pipeline {
    agent any
    options { timestamps(); disableConcurrentBuilds() }
    environment { COMPOSE_PROJECT_NAME = 'taskflow-cloud'; APP_URL = 'http://localhost:8081' }
    stages {
        stage('Checkout') { steps { checkout scm } }
        stage('Syntax Check') { steps { script { if (isUnix()) { sh 'python3 -m py_compile backend/app.py'; sh 'docker compose config -q' } else { bat 'python -m py_compile backend\\app.py'; bat 'docker compose config -q' } } } }
        stage('Build Image') { steps { script { if (isUnix()) { sh 'docker compose build --no-cache backend' } else { bat 'docker compose build --no-cache backend' } } } }
        stage('Automated Deployment') { steps { script { if (isUnix()) { sh 'docker compose up -d --remove-orphans' } else { bat 'docker compose up -d --remove-orphans' } } } }
        stage('Health Check') { steps { script { retry(10) { sleep time: 5, unit: 'SECONDS'; if (isUnix()) { sh "curl --fail ${APP_URL}/api/health" } else { bat "curl.exe --fail ${APP_URL}/api/health" } } } } }
    }
    post { success { echo 'Deployment berhasil dan aplikasi sehat.' }; failure { echo 'Pipeline gagal. Periksa stage yang berwarna merah.' } }
}
