"""Read-only container-runtime prerequisites; never install or start a daemon.

This is an environment check, not a substitute for Docker build/Compose tests.
It does not read application .env files, connect to a DB, or call model APIs.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess

import yaml

ROOT = Path(__file__).resolve().parents[2]


def namespace_probe(arguments):
    if not shutil.which("unshare"):
        return {"status": "unavailable"}
    try:
        result = subprocess.run(["unshare", "--user", "--map-root-user", *arguments, "true"],
                                capture_output=True, text=True, timeout=5)
        return {"status": "available" if result.returncode == 0 else "blocked",
                "exitCode": result.returncode, "reason": result.stderr.strip()[:300] or None}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "blocked", "reason": type(exc).__name__}


def inspect():
    names = ("docker", "dockerd", "podman", "containerd", "nerdctl", "runc", "rootlesskit",
             "newuidmap", "newgidmap", "slirp4netns", "fuse-overlayfs", "unshare")
    tools = {name: shutil.which(name) is not None for name in names}
    sockets = {}
    for location in ("/var/run/docker.sock", "/run/docker.sock", "/run/podman/podman.sock", "/run/containerd/containerd.sock"):
        try:
            sockets[location] = stat.S_ISSOCK(Path(location).stat().st_mode)
        except OSError:
            sockets[location] = False
    ranges = {}
    for name in ("/etc/subuid", "/etc/subgid"):
        try:
            rows = [row.split(":") for row in Path(name).read_text().splitlines() if row and not row.startswith("#")]
            ranges[name] = {"readable": True,
                "hasConfigured65536Range": any(len(row) == 3 and row[2].isdigit() and int(row[2]) >= 65536 for row in rows)}
        except OSError:
            ranges[name] = {"readable": False}
    capabilities = {}
    try:
        status = dict(line.split(":", 1) for line in Path("/proc/self/status").read_text().splitlines() if ":" in line)
        effective = int(status["CapEff"].strip(), 16)
        capabilities = {name: bool(effective & (1 << bit)) for name, bit in
                        (("CAP_SYS_ADMIN", 21), ("CAP_NET_ADMIN", 12), ("CAP_SETUID", 7), ("CAP_SETGID", 6))}
    except (OSError, KeyError, ValueError):
        pass
    compose = yaml.safe_load((ROOT / "compose.dev.yml").read_text())
    services = compose.get("services", {})
    build_files = {}
    for name, value in services.items():
        build = value.get("build")
        if isinstance(build, dict) and build.get("dockerfile"):
            build_files[name] = (ROOT / build["dockerfile"]).is_file()
    missing = [name for name in ("docker", "dockerd", "rootlesskit", "newuidmap", "newgidmap", "slirp4netns") if not tools[name]]
    return {"operation": "container_runtime_prerequisites", "checkedAt": datetime.now(timezone.utc).isoformat(),
        "uid": os.getuid(), "tools": tools, "knownSockets": sockets, "capabilities": capabilities,
        "subordinateIds": ranges, "namespaces": {"user": namespace_probe([]),
            "mount": namespace_probe(["--mount"]), "network": namespace_probe(["--net"]),
            "pid": namespace_probe(["--pid", "--fork"])},
        "compose": {"yamlParsed": True, "services": sorted(services), "buildFilesPresent": build_files,
            "dockerComposeConfigExecuted": False, "imageBuildExecuted": False, "containerStartupExecuted": False},
        "status": "blocked_missing_runtime" if not tools["docker"] and not tools["podman"] else "requires_explicit_runtime_test",
        "missingRootlessTools": missing,
        "note": "Namespace support does not prove a rootless Docker daemon is installed or Compose works. No daemon installation or system configuration change was attempted.",
        "officialPrerequisites": "https://docs.docker.com/engine/security/rootless/",
        "systemConfigurationChanged": False, "databaseConnections": 0, "modelCalls": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output")
    args = parser.parse_args()
    result = inspect()
    if args.output:
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["status"] == "requires_explicit_runtime_test" else 1)
