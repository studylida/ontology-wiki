"""Resource-bounded Python workers; this is not a filesystem/network sandbox."""
from __future__ import annotations

import asyncio
import math
import os
import signal
import subprocess
from collections.abc import Mapping, Sequence


class BoundedProcessError(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


# -S keeps site hooks and parser imports behind the parent's limit-assignment gate.
_BOOTSTRAP = """
import sys
if sys.stdin.buffer.read(1) != b'\\0':
    raise SystemExit(125)
cpu, memory, module = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
if sys.platform != 'win32':
    import resource
    resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))
    resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
sys.argv = sys.argv[3:]
import site
site.main()
import runpy
runpy.run_module(module, run_name='__main__', alter_sys=True)
"""


class _WindowsJob:
    def __init__(self, cpu_seconds: int, memory_bytes: int):
        import ctypes
        from ctypes import wintypes

        class BasicLimits(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_int64),
                ("PerJobUserTimeLimit", ctypes.c_int64),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD),
            ]

        class IoCounters(ctypes.Structure):
            _fields_ = [(name, ctypes.c_uint64) for name in (
                "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

        class ExtendedLimits(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", BasicLimits), ("IoInfo", IoCounters),
                ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]

        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        self.api.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        self.api.CreateJobObjectW.restype = wintypes.HANDLE
        self.api.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        self.api.SetInformationJobObject.restype = wintypes.BOOL
        self.api.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.api.OpenProcess.restype = wintypes.HANDLE
        self.api.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        self.api.AssignProcessToJobObject.restype = wintypes.BOOL
        self.api.CloseHandle.argtypes = [wintypes.HANDLE]
        self.api.CloseHandle.restype = wintypes.BOOL
        self.handle = self.api.CreateJobObjectW(None, None)
        if not self.handle:
            raise BoundedProcessError("setup_failed")
        limits = ExtendedLimits()
        # No breakaway flag: descendants stay in the same job and share its limits.
        limits.BasicLimitInformation.LimitFlags = 0x2000 | 0x100 | 0x200 | 0x2 | 0x4
        limits.BasicLimitInformation.PerProcessUserTimeLimit = cpu_seconds * 10_000_000
        limits.BasicLimitInformation.PerJobUserTimeLimit = cpu_seconds * 10_000_000
        limits.ProcessMemoryLimit = limits.JobMemoryLimit = memory_bytes
        if not self.api.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            self.close()
            raise BoundedProcessError("setup_failed")

    def assign(self, pid: int):
        # PROCESS_SET_QUOTA | PROCESS_TERMINATE are required for job assignment.
        process = self.api.OpenProcess(0x0100 | 0x0001, False, pid)
        if not process:
            raise BoundedProcessError("setup_failed")
        try:
            if not self.api.AssignProcessToJobObject(self.handle, process):
                raise BoundedProcessError("setup_failed")
        finally:
            self.api.CloseHandle(process)

    def close(self):
        if self.handle:
            self.api.CloseHandle(self.handle)
            self.handle = None


async def run_bounded_python(
    python_executable: str,
    module: str,
    args: Sequence[str] = (),
    *,
    input_bytes: bytes,
    env: Mapping[str, str],
    timeout_seconds: float,
    cpu_seconds: int,
    memory_bytes: int,
    max_output_bytes: int,
) -> bytes:
    """Run a module with only caller-supplied env and bound its resource/output use.

    TimeoutError and CancelledError propagate after terminating the worker tree.
    Child stderr is deliberately discarded; failures never disclose source content.
    Windows limits committed memory/user CPU for the job; POSIX limits virtual
    address space/process CPU. Neither grants filesystem or network isolation.
    """
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be finite and positive")
    if any(not isinstance(value, int) or isinstance(value, bool) or value <= 0
           for value in (cpu_seconds, memory_bytes, max_output_bytes)):
        raise ValueError("Resource bounds must be positive integers")
    proc = job = None
    tasks = []
    spawn = None
    try:
        async with asyncio.timeout(timeout_seconds):
            if os.name == "nt":
                job = _WindowsJob(cpu_seconds, memory_bytes)
            options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {"start_new_session": True}
            spawn = asyncio.create_task(asyncio.create_subprocess_exec(
                python_executable, "-S", "-c", _BOOTSTRAP, str(cpu_seconds), str(memory_bytes), module, *args,
                stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL, env=dict(env), **options))
            # Retain the process handle even if cancellation arrives during spawn.
            try:
                proc = await asyncio.shield(spawn)
            except OSError as exc:
                raise BoundedProcessError("setup_failed") from exc
            if job:
                job.assign(proc.pid)

            async def feed():
                try:
                    proc.stdin.write(b"\0")
                    for offset in range(0, len(input_bytes), 65536):
                        proc.stdin.write(input_bytes[offset:offset + 65536])
                        await proc.stdin.drain()
                    await proc.stdin.drain()
                except (BrokenPipeError, ConnectionResetError):
                    pass
                finally:
                    proc.stdin.close()

            async def read():
                output = bytearray()
                while chunk := await proc.stdout.read(min(65536, max_output_bytes + 1 - len(output))):
                    output.extend(chunk)
                    if len(output) > max_output_bytes:
                        raise BoundedProcessError("output_limit")
                return bytes(output)

            tasks = [asyncio.create_task(feed()), asyncio.create_task(read())]
            _, output = await asyncio.gather(*tasks)
            if await proc.wait() != 0:
                raise BoundedProcessError("process_failed")
            return output
    finally:
        if proc is None and spawn is not None:
            try:
                proc = await asyncio.shield(spawn)
            except (OSError, asyncio.CancelledError):
                pass
        if job:
            job.close()
        if proc is not None:
            if os.name != "nt":
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            elif proc.returncode is None:
                try:
                    proc.kill()
                except ProcessLookupError:
                    pass
            if proc.stdin:
                proc.stdin.close()
            for task in tasks:
                task.cancel()
            await asyncio.shield(asyncio.gather(proc.wait(), *tasks, return_exceptions=True))
