# this python program was written using python 3.8.6
from abc import ABC, abstractmethod
import os
import snyk
import glob

# prefix for error messages:
ERROR_PREFIX = "ERROR:"


class AbstractDependencyTester(ABC):
    @abstractmethod
    def __init__(self, snyk_org: snyk.client.Organization) -> None:
        self.snyk_org = snyk_org

    @abstractmethod
    def test(self, artifact_location: str) -> (str, list):
        pass


class PythonDenpendencyTester(AbstractDependencyTester):
    def __init__(self, snyk_org: snyk.client.Organization) -> None:
        self.snyk_org = snyk_org

    def test(self, artifact_location: str) -> (str, list):
        # tests python dependency files, returns a list of vulnerabilities
        # returns an empty list if no vulnerabilities are found
        error = None
        vulns = []

        # check if artifact contains a pip requirements file
        # requirements.txt should be in the root, but if it is in a sub directory
        # we search for it recursively..
        pip_file = (
            None
            if not glob.glob(pathname=f"{artifact_location}/**/requirements.txt", recursive=True)
            else glob.glob(pathname=f"{artifact_location}/**/requirements.txt", recursive=True)[0]
        )

        if pip_file:
            with open(pip_file, "r") as pf:
                try:
                    api_response = self.snyk_org.test_pipfile(pf)
                    if api_response.issues.vulnerabilities:
                        vulns = api_response.issues.vulnerabilities
                except Exception:
                    error = f"{ERROR_PREFIX} There was an error getting the vulnerabilities for the artifact."

        else:
            error = f"{ERROR_PREFIX} No requirements.txt file could be found, please include it in the root of the function archive."

        return error, vulns


class NodeJSDenpendencyTester(AbstractDependencyTester):
    # TODO implement
    def __init__(self, snyk_org: snyk.client.Organization) -> None:
        self.snyk_org = snyk_org

    def test(self, artifact_location: str) -> (str, list):
        raise NotImplementedError()
