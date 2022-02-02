import yaml
from autoscaler.clients.kubernetes.base import (
    KubernetesPythonAPIService,
    KubernetesSpecFileAPIService)
from autoscaler.core.logger import logger


class KubernetesInMemoryService:
    def check_kubernetes_namespace(self, namespace):
        return True

    def setup_job(self, runner_data):
        pass

    def delete_job(self, runner_uuid, namespace):
        pass


class KubernetesService:

    def check_kubernetes_namespace(self, namespace):
        logger.info(f"Checking for the {namespace} namespace...")
        kube_python_api = KubernetesPythonAPIService()
        created = kube_python_api.get_or_create_kubernetes_namespace(
            namespace=namespace)
        return created

    def setup_job(self, runner_data):
        logger.info("Starting to setup the Kubernetes job ...")

        # TODO refactor it
        kube_spec_file_api = KubernetesSpecFileAPIService()
        runner_job_spec = kube_spec_file_api.generate_kube_spec_file(
            runner_data)

        # TODO improve workflow with k8s spec template for runner job
        # runner-config.yaml.template
        runner_spec = yaml.safe_load(runner_job_spec)
        job_secret_spec = runner_spec['items'][0]
        job_spec = runner_spec['items'][1]

        kube_python_api = KubernetesPythonAPIService()
        kube_python_api.create_secret(
            job_secret_spec, runner_data['runnerNamespace'])
        kube_python_api.create_job(job_spec, runner_data['runnerNamespace'])

        logger.info("Job created.")

    def delete_job(self, runner_uuid, namespace):
        # TODO refactor it
        kube_python_api = KubernetesPythonAPIService()
        kube_python_api.delete_job(runner_uuid, namespace)
        # TODO delete secrets

        logger.info("Job deleted.")
