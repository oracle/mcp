"""
Kubernetes MCP Server (Python, FastMCP)
- Pure Python MCP server for Kubernetes clusters via user-selected kubeconfig.
- Tools provided: list_namespaces, list_pods, list_nodes, ping.
- Each tool accepts kubeconfig (param or env) to support session/user profiles as in kubernetes-mcp-server.
"""
import os
from typing import Optional, List, Dict
from fastmcp import FastMCP
from kubernetes import client, config
from kubernetes.client import ApiException
import glob

mcp = FastMCP("kube-mcp-server")

def load_kube_config(kubeconfig_path: Optional[str] = None, context: Optional[str] = None):
    """Prompt for kubeconfig path if not provided, instead of loading default."""
    if not kubeconfig_path:
        raise RuntimeError(
            "Kubeconfig path not provided. Please specify the path to your kubeconfig file."
        )
    try:
        config.load_kube_config(config_file=kubeconfig_path, context=context)
    except Exception as e:
        raise RuntimeError(f"Failed to load kubeconfig: {e}")

@mcp.tool()
def ping() -> str:
    """Health check. Returns 'ok' if the server is responsive."""
    return "ok"

# @mcp.tool()
# def list_kubeconfigs(configs_dir: str = None) -> dict:
#     """
#     List available kubeconfig files in the provided directory.
#     - configs_dir: directory containing kubeconfig files (defaults to $KUBECONFIGS env variable)
#     """
#     # Determine directory to search
#     if not configs_dir:
#         configs_dir = os.environ.get("KUBECONFIGS", os.path.expanduser("~/.kube/"))
#     pattern = os.path.join(configs_dir, "*")
#     files = [f for f in glob.glob(pattern) if os.path.isfile(f)]
#     return {"kubeconfigs": files}

def _list_namespaces_inner(kubeconfig: str, context: Optional[str] = None) -> Dict:
    """
    List all namespaces in the cluster.
    :param kubeconfig: Path to kubeconfig file (required)
    :param context: Optional kubeconfig context name
    :return: {"namespaces": [ ... ]}
    """
    load_kube_config(kubeconfig, context)
    v1 = client.CoreV1Api()
    try:
        ns_list = v1.list_namespace()
        return {
            "namespaces": [item.metadata.name for item in ns_list.items]
        }
    except ApiException as e:
        return {"error": str(e)}

@mcp.tool()
def list_namespaces(kubeconfig: str, context: Optional[str] = None) -> Dict:
    """
    :param kubeconfig: Path to kubeconfig file (required)
    :param context: Kubernetes context (optional)
    """
    return _list_namespaces_inner(kubeconfig, context)

@mcp.tool()
def list_pods(
    kubeconfig: Optional[str] = None, 
    namespace: Optional[str] = None
) -> Dict:
    """
    List pods in the specified namespace (or all).
    :param kubeconfig: Path to kubeconfig file (optional)
    :param namespace: Namespace to filter pods (optional, all if not given)
    :return: {"pods": [{namespace, name, phase}, ...]}
    """
    load_kube_config(kubeconfig or os.environ.get("KUBECONFIG", None))
    v1 = client.CoreV1Api()
    try:
        if namespace:
            pods = v1.list_namespaced_pod(namespace=namespace)
        else:
            pods = v1.list_pod_for_all_namespaces()
        return {
            "pods": [
                {
                    "namespace": pod.metadata.namespace,
                    "name": pod.metadata.name,
                    "phase": pod.status.phase,
                }
                for pod in pods.items
            ]
        }
    except ApiException as e:
        return {"error": str(e)}

@mcp.tool()
def list_nodes(kubeconfig: Optional[str] = None) -> Dict:
    """
    List all nodes in the cluster.
    :param kubeconfig: Path to kubeconfig file (optional, uses env if not provided)
    :return: {"nodes": [{name, labels, status}...]}
    """
    load_kube_config(kubeconfig or os.environ.get("KUBECONFIG", None))
    v1 = client.CoreV1Api()
    try:
        nodes = v1.list_node()
        return {
            "nodes": [
                {
                    "name": node.metadata.name,
                    "labels": node.metadata.labels,
                    "status": node.status.conditions[-1].type if node.status and node.status.conditions else "Unknown",
                }
                for node in nodes.items
            ]
        }
    except ApiException as e:
        return {"error": str(e)}

def main():
    """Start the Python MCP server for Kubernetes."""
    import sys
    # Dynamic CLI selection for kubeconfig/context
    import argparse
    parser = argparse.ArgumentParser(description="Kubernetes MCP server/tools")
    parser.add_argument("--test-list-namespaces", action="store_true", help="Test list namespaces")
    parser.add_argument("--kubeconfig", type=str, default=None, help="Path to kubeconfig file")
    parser.add_argument("--context", type=str, default=None, help="Kubernetes context name")
    args = parser.parse_args()

    if args.test_list_namespaces:
        print(f"Testing direct list_namespaces() with KUBECONFIG={args.kubeconfig} context={args.context}")
        try:
            print(_list_namespaces_inner(args.kubeconfig, args.context))
        except Exception as e:
            print(f"Error: {e}")
        return
    mcp.run()

if __name__ == "__main__":
    main()
