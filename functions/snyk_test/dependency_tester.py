# this python program was written using python 3.8.6
from abc import ABC, abstractmethod
import os
import snyk

# prefix for error messages:
ERROR_PREFIX = "ERROR:"


class AbstractDependencyTester(ABC):
    @abstractmethod
    def __init__(self, snyk_org: snyk.client.Organization) -> None:
        self.org = snyk_org

    @abstractmethod
    def test(self, artifact_location: str) -> (str, list):
        pass


class PythonDenpendencyTester(AbstractDependencyTester):
    def __init__(self, snyk_org: snyk.client.Organization) -> None:
        self.snyk_org = snyk_org

    def test(self, artifact_location: str) -> (str, list):
        error = None
        vulns = []

        artifact_files = os.listdir(artifact_location)

        if "requirements.txt" in artifact_files:
            pip_file = f"{artifact_location}/requirements.txt"
            with open(pip_file) as pf:
                try:
                    api_response = self.snyk_org.test_pipfile(pf.read())
                    vulns = api_response.issues.vulnerabilities
                except Exception:
                    error = f"{ERROR_PREFIX} There was an error getting the vulnerabilities for the artifact."
            return error, vulns

        # TODO case where using .dist-info folder names to get packages and versions
        # TODO case where there are no vulnerabilities

        return error, vulns


class NodeJSDenpendencyTester(AbstractDependencyTester):
    # TODO implement
    def __init__(self, snyk_org: snyk.client.Organization) -> None:
        self.org = snyk_org

    def test(self, artifact_location: str) -> (str, list):
        pass
