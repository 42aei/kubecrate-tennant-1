#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import yaml

SEMVER_RE = re.compile(r"^v\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
ROOT = "clusters/tennant-1/entrypoint"
EXPECTED_SOURCE_NAME = "flux-system-sync"
EXPECTED_SOURCE_URL = "https://github.com/42aei/kubecrate.git"
EXPECTED_TAG = "v0.4.0"
EXPECTED_VANILLA_PATH = "./compositions/vanilla/entrypoint"
FORBIDDEN_PATH_TOKENS = (
    "doppler",
    "openbao",
    "clusterproxy",
    "netbird",
    "secret",
    "token",
)
FORBIDDEN_KINDS = {
    "externalsecret",
    "clustersecretstore",
    "secretstore",
}
FORBIDDEN_API_GROUP_SNIPPETS = (
    "external-secrets.io/",
    "secrets.hashicorp.com/",
)


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def validate_entrypoint(root: Path, errors: list[str]) -> None:
    entrypoint = root / ROOT
    require(entrypoint.is_dir(), errors, f"missing entrypoint directory: {ROOT}")

    namespace = load_yaml(entrypoint / "namespace.yaml")
    require(namespace.get("kind") == "Namespace", errors, "namespace.yaml must define a Namespace")
    require(namespace.get("metadata", {}).get("name") == "kubecrate-system", errors, "namespace name must be kubecrate-system")

    source = load_yaml(entrypoint / "kubecrate-source.yaml")
    require(source.get("apiVersion") == "source.toolkit.fluxcd.io/v1", errors, "kubecrate-source apiVersion must be source.toolkit.fluxcd.io/v1")
    require(source.get("kind") == "GitRepository", errors, "kubecrate-source.yaml must define a GitRepository")
    require(source.get("metadata", {}).get("name") == EXPECTED_SOURCE_NAME, errors, f"GitRepository name must be {EXPECTED_SOURCE_NAME}")
    require(source.get("metadata", {}).get("namespace") == "flux-system", errors, "GitRepository namespace must be flux-system")
    require(source.get("spec", {}).get("url") == EXPECTED_SOURCE_URL, errors, f"GitRepository url must be {EXPECTED_SOURCE_URL}")
    ref = source.get("spec", {}).get("ref", {})
    require(set(ref.keys()) == {"tag"}, errors, "GitRepository ref must use only spec.ref.tag")
    tag = ref.get("tag")
    require(bool(SEMVER_RE.match(str(tag))), errors, f"GitRepository tag must be exact SemVer, got: {tag!r}")
    require(tag == EXPECTED_TAG, errors, f"GitRepository tag must be {EXPECTED_TAG}")

    vanilla = load_yaml(entrypoint / "vanilla-kustomization.yaml")
    require(vanilla.get("apiVersion") == "kustomize.toolkit.fluxcd.io/v1", errors, "vanilla-kustomization apiVersion must be kustomize.toolkit.fluxcd.io/v1")
    require(vanilla.get("kind") == "Kustomization", errors, "vanilla-kustomization.yaml must define a Kustomization")
    require(vanilla.get("metadata", {}).get("name") == "kubecrate-vanilla", errors, "Kustomization name must be kubecrate-vanilla")
    require(vanilla.get("metadata", {}).get("namespace") == "flux-system", errors, "Kustomization namespace must be flux-system")
    spec = vanilla.get("spec", {})
    require(spec.get("path") == EXPECTED_VANILLA_PATH, errors, f"Kustomization path must be {EXPECTED_VANILLA_PATH}")
    require(spec.get("sourceRef", {}).get("kind") == "GitRepository", errors, "Kustomization sourceRef.kind must be GitRepository")
    require(spec.get("sourceRef", {}).get("name") == EXPECTED_SOURCE_NAME, errors, f"Kustomization sourceRef.name must be {EXPECTED_SOURCE_NAME}")

    root_kustomization = load_yaml(entrypoint / "kustomization.yaml")
    require(root_kustomization.get("kind") == "Kustomization", errors, "root kustomization.yaml must define a Kustomization")
    resources = root_kustomization.get("resources", [])
    require(resources == ["namespace.yaml", "kubecrate-source.yaml", "vanilla-kustomization.yaml"], errors, "root kustomization resources must stay minimal and ordered")


def validate_forbidden_content(root: Path, errors: list[str]) -> None:
    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        rel_path = path.relative_to(root).as_posix().lower()
        for token in FORBIDDEN_PATH_TOKENS:
            require(token not in rel_path, errors, f"forbidden path token {token!r} found in {path.relative_to(root).as_posix()}")
        if path.suffix not in {".yaml", ".yml"}:
            continue
        doc = load_yaml(path)
        if not isinstance(doc, dict):
            continue
        kind = str(doc.get("kind", "")).lower()
        api_version = str(doc.get("apiVersion", "")).lower()
        require(kind not in FORBIDDEN_KINDS, errors, f"forbidden kind {doc.get('kind')!r} found in {path.relative_to(root).as_posix()}")
        for snippet in FORBIDDEN_API_GROUP_SNIPPETS:
            require(snippet not in api_version, errors, f"forbidden apiVersion {doc.get('apiVersion')!r} found in {path.relative_to(root).as_posix()}")


def run_kustomize(root: Path, errors: list[str]) -> None:
    cmd = ["kubectl", "kustomize", str(root / ROOT)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        errors.append(f"kubectl kustomize failed: {result.stderr.strip() or result.stdout.strip()}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    errors: list[str] = []
    validate_entrypoint(root, errors)
    validate_forbidden_content(root, errors)
    run_kustomize(root, errors)
    if errors:
        print("consumer validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("consumer validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
