import importlib
import inspect
import os
from functools import wraps
from logging import Logger
from typing import Any, Callable, TypeVar

import oci

ClientT = TypeVar("ClientT")

logger = Logger(__name__, level="INFO")


def _create_oci_client(
    client_class: type[ClientT], project: str, version: str, tool_name: str
) -> ClientT:
    """
    Creates a client from the given OCI SDK class

    :param client_class: The OCI SDK Class
    :type client_class: type[ClientT]
    :param project: Project Name
    :type project: str
    :param version: Project Version
    :type version: str
    :return: Returns the configured client class
    :rtype: ClientT
    """
    logger.info("entering _create_oci_client")
    config = oci.config.from_file(
        file_location=os.getenv("OCI_CONFIG_FILE", oci.config.DEFAULT_LOCATION),
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE),
    )
    user_agent_name = project.split("oracle.", 1)[1].split("-server", 1)[0]
    config["additional_user_agent"] = f"{user_agent_name}/{version} ({tool_name})"

    private_key = oci.signer.load_private_key_from_file(config["key_file"])
    token_file = os.path.expanduser(config["security_token_file"])
    token = None
    with open(token_file, "r") as f:
        token = f.read()
    signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
    return client_class(config, signer=signer)


def _resolve_project_metadata(func: Callable[..., Any]) -> tuple[str, str]:
    """
    This function automatically finds the package name and version of a calling function

    :param func: The given function that is being called
    :type func: Callable[..., Any]
    :return: Returns a project and version of the package
    :rtype: tuple[str, str]
    """
    module = inspect.getmodule(func)
    if module is None:
        raise RuntimeError(
            "Unable to determine module for function decorated with with_oci_client"
        )

    project = getattr(module, "__project__", None)
    version = getattr(module, "__version__", None)

    package_name = module.__package__ or module.__name__.rpartition(".")[0]

    while (project is None or version is None) and package_name:
        package = importlib.import_module(package_name)
        project = project or getattr(package, "__project__", None)
        version = version or getattr(package, "__version__", None)
        if "." in package_name:
            package_name = package_name.rsplit(".", 1)[0]
        else:
            package_name = ""

    if project is None or version is None:
        raise RuntimeError(
            "Unable to resolve __project__ and __version__ for with_oci_client decorated function"
        )

    return project, version


def with_oci_client(
    client_class: type[ClientT],
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    A decorator which configures the OCI client with metadata

    :param client_class: The client class from the OCI SDK
    :type client_class: type[ClientT]
    :return: Configured client
    :rtype: Callable[[Callable[..., Any]], Callable[..., Any]]
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        signature = inspect.signature(func)

        if "client" not in signature.parameters:
            raise ValueError(
                "with_oci_client decorator requires a 'client' parameter in the function signature"
            )

        project, version = _resolve_project_metadata(func)

        def _ensure_client(kwargs: dict[str, Any]) -> dict[str, Any]:
            if kwargs.get("client") is None:
                kwargs = dict(kwargs)
                kwargs["client"] = _create_oci_client(
                    client_class, project, version, func.__qualname__
                )
            return kwargs

        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                kwargs = _ensure_client(kwargs)
                return await func(*args, **kwargs)

            wrapper: Callable[..., Any] = async_wrapper
        else:

            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                kwargs = _ensure_client(kwargs)
                return func(*args, **kwargs)

        parameters_without_client = [
            parameter
            for name, parameter in signature.parameters.items()
            if name != "client"
        ]
        wrapper.__signature__ = signature.replace(
            parameters=tuple(parameters_without_client)
        )
        return wrapper

    return decorator
