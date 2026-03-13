import os
import ast
import inspect
from enum import Enum
from collections import defaultdict

class OpCategory(Enum):
    DESTRUCTIVE = "destructive"
    LIST = "list"
    OTHER = "other"

DESTRUCTIVE_KEYWORDS = set([
    # Fill with confirmed "definitely not safe" verbs (likely rare, opt-in only as knowledge increases)
    # Start empty or minimal (e.g., "delete", "terminate", "detach", "remove")
])

LIST_KEYWORDS = ("list",)
LIST_SIGNATURE_HINTS = ("page", "limit", "opc_next_page")
LIST_DOC_HINTS = ("paginated", "pagination", "returns a list", "lists all", "paged", "page token")
CATEGORIES = [cat.value for cat in OpCategory]

SAFE_KEYWORDS = set([
    "list", "get", "fetch", "search", "summarize", "query", "retrieve", "suggest", "filter",
    "batch", "analyze", "check", "scan", "find", "describe", "export"
])

def method_takes_payload(node):
    # AST mode: True if method has at least one non-self parameter other than **kwargs, *args, and 'self' (or 'cls')
    params = [arg.arg for arg in node.args.args]
    if params and params[0] in ("self", "cls"):
        params = params[1:]
    # Ignore *args, **kwargs, but if there's any remaining, consider this method as taking a payload.
    # Arguments like "self", "cls", "kwargs", "args", etc. with default/empty value are not considered payload.
    return bool(params)

def classify_method(method_name, docstring, params, debug=False):
    name = method_name.lower()
    docstring = (docstring or "").lower()
    tokens = name.split("_")
    for kw in LIST_KEYWORDS:
        if name.startswith(kw + "_"):
            if debug: print(f"[CLASSIFY] {method_name}: matched LIST by prefix '{kw}_'")
            return OpCategory.LIST.value
    if docstring:
        for hint in LIST_DOC_HINTS:
            if hint in docstring:
                if debug: print(f"[CLASSIFY] {method_name}: matched LIST by docstring hint '{hint}'")
                return OpCategory.LIST.value
    if name.startswith("get_") and docstring and ("multiple " in docstring or "list of" in docstring):
        if debug: print(f"[CLASSIFY] {method_name}: matched LIST by get_ bulk")
        return OpCategory.LIST.value
    first_kw = tokens[0]
    if first_kw in SAFE_KEYWORDS or (name.startswith("test_") and "connection" in name):
        if debug: print(f"[CLASSIFY] {method_name}: matched SAFE first keyword '{first_kw}', classified as OTHER")
        return OpCategory.OTHER.value
    if first_kw in DESTRUCTIVE_KEYWORDS or any(token in DESTRUCTIVE_KEYWORDS for token in tokens):
        if debug: print(f"[CLASSIFY] {method_name}: matched explicit DESTRUCTIVE_KEYWORDS, classified as DESTRUCTIVE")
        return OpCategory.DESTRUCTIVE.value
    if debug: print(f"[CLASSIFY] {method_name}: defaulted to DESTRUCTIVE (guilty until proven innocent)")
    return OpCategory.DESTRUCTIVE.value

def all_client_files(oci_base):
    for dirpath, _, files in os.walk(oci_base):
        for file in files:
            if file.endswith("_client.py"):
                yield os.path.join(dirpath, file)

def extract_classes_and_methods_and_payloads(file_path):
    classes = {}
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=file_path)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name.endswith("Client"):
            methods = {}
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and not item.name.startswith("_"):
                    args = [a.arg for a in item.args.args[1:]]  # skip self
                    doc = ast.get_docstring(item)
                    has_payload = method_takes_payload(item)
                    methods[item.name] = {"params": args, "doc": doc, "payload": has_payload}
            classes[node.name] = methods
    return classes

def main():
    oci_base = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        ".venv", "lib", "python3.13", "site-packages", "oci"
    )
    if not os.path.isdir(oci_base):
        print(f"ERROR: Can't find OCI SDK base at {oci_base}")
        return

    grouped = {cat: defaultdict(list) for cat in CATEGORIES}
    client_file_count = 0
    client_class_count = 0
    first_keywords = {cat: set() for cat in CATEGORIES}

    for fpath in all_client_files(oci_base):
        client_file_count += 1
        try:
            class_map = extract_classes_and_methods_and_payloads(fpath)
        except Exception as e:
            print(f"PARSE ERROR: {fpath}: {e}")
            continue
        for clsname, methods in class_map.items():
            client_class_count += 1
            for meth_name, info in methods.items():
                debug = False
                cat = classify_method(meth_name, info["doc"], info["params"], debug=debug)
                grouped[cat][clsname].append((meth_name, info.get("payload", False)))
                if cat in first_keywords:
                    first_kw = meth_name.lower().split("_")[0]
                    first_keywords[cat].add(first_kw)

    with open("oci_sdk_method_classification.txt", "w") as f:
        for cat in CATEGORIES:
            f.write(f"{cat}\n")
            for client in sorted(grouped[cat]):
                f.write(f"\t{client}\n")
                for method, has_payload in sorted(grouped[cat][client]):
                    emoji = "✅" if has_payload else "❌"
                    f.write(f"\t\t{method} {emoji}\n")
            f.write("\n")
        f.write("====== SUMMARY ======\n")
        f.write(f"Client files parsed: {client_file_count}\n")
        f.write(f"Clients (classes) found: {client_class_count}\n")
        f.write("\n====== KEYWORDS ======\n")
        for cat in CATEGORIES:
            f.write(f"First keywords in '{cat}':\n")
            for kw in sorted(first_keywords[cat]):
                f.write(f"\t{kw}\n")
    print(f"Classification written to oci_sdk_method_classification.txt - "
          f"Files parsed: {client_file_count}, Clients found: {client_class_count}")

if __name__ == "__main__":
    main()