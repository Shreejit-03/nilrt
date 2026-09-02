#!/usr/bin/env python3
"""Read-only MCP server exposing NI Linux RT target diagnostics.

Runs either directly on an RT target (local mode) or against a remote target
over SSH (set RT_MCP_SSH="user@host"). Only read-only tools are exposed.
"""

import os
import shlex
import subprocess

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("nilrt-rt")

# When set (e.g. "root@10.0.0.42"), commands run on the remote target via SSH.
SSH_TARGET = os.environ.get("RT_MCP_SSH", "").strip()
CMD_TIMEOUT = int(os.environ.get("RT_MCP_TIMEOUT", "120"))


def _run(cmd: str, timeout: int = CMD_TIMEOUT) -> str:
    """Run a shell command locally or over SSH and return combined output."""
    if SSH_TARGET:
        full = ["ssh", "-o", "BatchMode=yes", "-o",
                "StrictHostKeyChecking=accept-new", SSH_TARGET, cmd]
    else:
        full = ["bash", "-lc", cmd]
    try:
        proc = subprocess.run(
            full, capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        return f"ERROR: command timed out after {timeout}s: {cmd}"
    if proc.returncode != 0:
        out = (proc.stdout or "") + (proc.stderr or "")
        return f"ERROR (exit {proc.returncode}):\n{out}".rstrip()
    # On success ignore stderr (NI login banner is emitted there).
    return (proc.stdout or "").strip() or "(no output)"


@mcp.tool()
def get_boot_mode() -> str:
    """Report whether the RT target is in safemode or runmode."""
    return _run(
        "if [ -f /etc/natinst/safemode ] || /sbin/runlevel | grep -Eq ' 4$'; "
        "then echo safemode; else echo runmode; fi"
    )


@mcp.tool()
def get_rt_kernel_info() -> str:
    """Report kernel version and PREEMPT_RT status of the target."""
    return _run(
        "echo '# uname'; uname -a; "
        "echo; echo '# realtime flag'; "
        "cat /sys/kernel/realtime 2>/dev/null || echo 'not present'; "
        "echo; echo '# PREEMPT in version'; "
        "cat /proc/version"
    )


@mcp.tool()
def get_rt_latency(duration_s: int = 10, interval_us: int = 1000) -> str:
    """Measure scheduling latency with cyclictest (read-only benchmark).

    duration_s: how long to run. interval_us: timer interval in microseconds.
    """
    duration_s = max(1, min(int(duration_s), 300))
    loops = max(1, int(duration_s * 1_000_000 / max(interval_us, 1)))
    cmd = (
        f"cyclictest --smp -p 80 -i {int(interval_us)} "
        f"-l {loops} -q -m 2>/dev/null || "
        f"echo 'cyclictest not available (install rt-tests)'"
    )
    return _run(cmd, timeout=duration_s + 30)


@mcp.tool()
def list_rt_threads() -> str:
    """List real-time scheduled threads with priority and CPU affinity."""
    return _run(
        "ps -eLo pid,tid,cls,rtprio,psr,comm --sort=-rtprio | "
        "awk 'NR==1 || $3==\"FF\" || $3==\"RR\"'"
    )


@mcp.tool()
def read_kernel_log(lines: int = 100, grep: str = "") -> str:
    """Read the tail of the kernel ring buffer, optionally filtered.

    lines: number of trailing lines. grep: optional case-insensitive filter.
    """
    lines = max(1, min(int(lines), 2000))
    base = "dmesg -T 2>/dev/null || dmesg"
    if grep:
        base = f"({base}) | grep -i -- {shlex.quote(grep)}"
    return _run(f"({base}) | tail -n {lines}")


if __name__ == "__main__":
    mcp.run()
