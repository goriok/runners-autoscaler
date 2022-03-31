"""Module to interact with Kubernetes APIs: running commands"""
from jinja2 import PackageLoader, Environment
from kubernetes import config as k8s_config, client as k8s_client
from kubernetes.client import ApiException

from autoscaler.core.exceptions import CannotCreateNamespaceError, NamespaceNotFoundError, KubernetesNamespaceError
from autoscaler.core.constants import TEMPLATE_FILE_NAME


class KubernetesSpecFileAPIService:

    def __init__(self):
        pass

    def generate_kube_spec_file(self, runner_data, template_filename=TEMPLATE_FILE_NAME):
        # process template to k8s spec
        template_loader = PackageLoader("autoscaler", "resources")
        template_env = Environment(
            loader=template_loader,
            variable_start_string="<%",
            variable_end_string="%>"
        )
        job_template = template_env.get_template(template_filename)

        output = job_template.render(runner_data)

        return output


class KubernetesPythonAPIService:
    def __init__(self):
        self.load_config()
        self.client = k8s_client

    def load_config(self):
        k8s_config.load_incluster_config()

    def create_secret(self, spec, namespace):
        core_v1 = self.client.CoreV1Api()
        resp = core_v1.create_namespaced_secret(body=spec, namespace=namespace)
        return resp

    def create_job(self, spec, namespace):
        batch_v1 = self.client.BatchV1Api()
        resp = batch_v1.create_namespaced_job(body=spec, namespace=namespace)
        return resp

    def delete_secret(self, runner_uuid, namespace):
        core_v1 = self.client.CoreV1Api()
        core_v1.delete_namespaced_secret(
            name=f"runner-oauth-credentials-{runner_uuid}",
            namespace=namespace,
            body=self.client.V1DeleteOptions(
                propagation_policy='Foreground',
                grace_period_seconds=5
            )
        )

    def delete_job(self, runner_uuid, namespace):
        batch_v1 = self.client.BatchV1Api()
        batch_v1.delete_namespaced_job(
            name=f"runner-{runner_uuid}",
            namespace=namespace,
            body=self.client.V1DeleteOptions(
                propagation_policy='Foreground',
                grace_period_seconds=5
            )
        )

    def get_kubernetes_namespace(self, namespace):
        core_v1 = self.client.CoreV1Api()
        try:
            core_v1.read_namespace(name=namespace)
        except ApiException as e:
            if e.status == 404:
                raise NamespaceNotFoundError from e

            raise KubernetesNamespaceError(str(e)) from e

    def create_kubernetes_namespace(self, namespace):
        core_v1 = self.client.CoreV1Api()
        try:
            core_v1.create_namespace(
                k8s_client.V1Namespace(metadata=k8s_client.V1ObjectMeta(name=namespace))
            )
        except ApiException as e:
            raise CannotCreateNamespaceError(str(e)) from e
