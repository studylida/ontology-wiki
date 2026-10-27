import asyncio
import ctypes
import json
import os
import sys
from pathlib import Path

import pytest

from knowledge.integrations.bounded_process import BoundedProcessError, run_bounded_python


@pytest.fixture
def worker(tmp_path):
    (tmp_path / "bounded_test_worker.py").write_text("""
import json, os, subprocess, sys, time
from pathlib import Path
mode = sys.argv[1]
if mode == 'echo':
    print(json.dumps({'body': sys.stdin.buffer.read().decode(), 'secret': os.environ.get('BOUNDED_TEST_SECRET')}))
elif mode == 'overflow':
    sys.stdout.buffer.write(b'x' * 100_000)
elif mode == 'fail':
    print('private-input-on-stderr', file=sys.stderr)
    raise SystemExit(3)
elif mode in ('tree', 'orphan'):
    child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    Path(sys.argv[2]).write_text(str(child.pid))
    if mode == 'tree':
        time.sleep(60)
    print('done')
elif mode == 'memory':
    bytearray(400 * 1024 * 1024)
    print('unbounded')
elif mode == 'cpu':
    while True:
        pass
elif mode == 'marker':
    Path(sys.argv[2]).write_text('parser-ran')
""", encoding="utf-8")
    env = {key: value for key, value in os.environ.items()
           if key in ("SystemRoot", "SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP")}
    env["PYTHONPATH"] = str(tmp_path)

    async def run(mode, *args, **overrides):
        kwargs = dict(input_bytes=b"", env=env, timeout_seconds=10, cpu_seconds=5,
                      memory_bytes=256 * 1024 * 1024, max_output_bytes=4096)
        kwargs.update(overrides)
        return await run_bounded_python(sys.executable, "bounded_test_worker", (mode, *map(str, args)), **kwargs)
    return run


def process_alive(pid):
    if os.name == "nt":
        from ctypes import wintypes
        api = ctypes.WinDLL("kernel32", use_last_error=True)
        api.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        api.OpenProcess.restype = wintypes.HANDLE
        api.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        api.WaitForSingleObject.restype = wintypes.DWORD
        api.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = api.OpenProcess(0x00100000, False, pid)
        if not handle:
            return False
        try:
            return api.WaitForSingleObject(handle, 0) == 258
        finally:
            api.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


async def wait_for_file(path: Path):
    async with asyncio.timeout(5):
        while not path.exists():
            await asyncio.sleep(0.02)


async def assert_exited(pid):
    async with asyncio.timeout(5):
        while process_alive(pid):
            await asyncio.sleep(0.02)


@pytest.mark.asyncio
async def test_exact_input_and_only_supplied_environment(worker, monkeypatch):
    monkeypatch.setenv("BOUNDED_TEST_SECRET", "parent-only-test-value")
    raw = "조건 250°C\n".encode() * 10_000
    result = json.loads(await worker("echo", input_bytes=raw, max_output_bytes=1_000_000))
    assert result == {"body": raw.decode(), "secret": None}


@pytest.mark.asyncio
async def test_missing_interpreter_has_generic_setup_error(tmp_path):
    with pytest.raises(BoundedProcessError) as caught:
        await run_bounded_python(str(tmp_path / "missing-python.exe"), "anything", input_bytes=b"",
                                 env={}, timeout_seconds=5, cpu_seconds=1, memory_bytes=256 * 1024 * 1024,
                                 max_output_bytes=1024)
    assert caught.value.code == "setup_failed"


@pytest.mark.asyncio
@pytest.mark.parametrize(("mode", "code"), [("overflow", "output_limit"), ("fail", "process_failed")])
async def test_output_limit_and_generic_failure(worker, mode, code):
    with pytest.raises(BoundedProcessError) as caught:
        await worker(mode)
    assert caught.value.code == code
    assert "private-input" not in str(caught.value)


@pytest.mark.asyncio
async def test_timeout_kills_descendant(worker, tmp_path):
    pid_path = tmp_path / "timeout-child.pid"
    with pytest.raises(TimeoutError):
        await worker("tree", pid_path, timeout_seconds=1.5)
    assert pid_path.exists(), "Worker must have created its child before timeout"
    await assert_exited(int(pid_path.read_text()))


@pytest.mark.asyncio
async def test_cancellation_kills_descendant(worker, tmp_path):
    pid_path = tmp_path / "cancel-child.pid"
    task = asyncio.create_task(worker("tree", pid_path))
    await wait_for_file(pid_path)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    await assert_exited(int(pid_path.read_text()))


@pytest.mark.asyncio
async def test_success_also_closes_descendant_job(worker, tmp_path):
    pid_path = tmp_path / "success-child.pid"
    assert (await worker("orphan", pid_path)).strip() == b"done"
    await assert_exited(int(pid_path.read_text()))


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["memory", "cpu"])
async def test_os_enforces_memory_and_cpu_bounds(worker, mode):
    with pytest.raises(BoundedProcessError) as caught:
        await worker(mode, cpu_seconds=1, timeout_seconds=10)
    assert caught.value.code == "process_failed"


@pytest.mark.asyncio
@pytest.mark.skipif(os.name != "nt", reason="Windows job assignment contract")
async def test_job_assignment_failure_never_imports_parser(worker, tmp_path, monkeypatch):
    from knowledge.integrations import bounded_process
    def fail_assignment(self, pid):
        raise BoundedProcessError("setup_failed")
    monkeypatch.setattr(bounded_process._WindowsJob, "assign", fail_assignment)
    marker = tmp_path / "should-not-exist"
    with pytest.raises(BoundedProcessError) as caught:
        await worker("marker", marker)
    assert caught.value.code == "setup_failed"
    assert not marker.exists()
