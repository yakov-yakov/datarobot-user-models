node('release-dev && memory-intense'){
  checkout scm
  stage ('test_inference_model_templates') {
    checkout scm

    dir('jenkins_artifacts'){
        unstash 'drum_wheel'
    }

    checkoutDataRobot()
    withQuantum([
        bash: '''\
            set -exuo pipefail
            pushd DataRobot
            make update_env
            export LRS_POLL_DELAY_SECONDS=1
            export LRS_RETRIES=120
            export CUSTOM_MODEL_PREDICT_MEM_LIMIT=2147483648
            export CUSTOM_MODEL_PREDICT_MEM_REQUEST=2147483648
            export EXECUTION_ENVIRONMENT_LIMIT=20
            export RESTRICT_EXECUTION_ENVIRONMENT_CREATION=false
            export CLIENT_VERSION=\$(git rev-parse --short HEAD)
            ./start.sh --kubernetes-k3d --kubernetes-validate
            popd
        '''.stripIndent(),
        venvName: "datarobot-dev"
    ])
    withQuantum([
        bash: '''\
            set -exuo pipefail
            ls -la jenkins_artifacts
            ./jenkins/test3_inference_model_templates.sh
        '''.stripIndent(),
        pythonVersion: '3',
        venvName: "datarobot-user-models"
    ])
  }
}