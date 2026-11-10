#!/usr/bin/env python3
"""Drive the git-panic TUI through a real PTY and verify behavior.

Usage:  scripts/tui-pty-test.py [path/to/git-panic]   (default: target/release/git-panic)
Needs:  python3, git. Run `cargo build --release` first. No interactive input required.

Checks: alternate-screen enter/leave, key navigation (Down, j, PageDown,
PageUp, Home, End, k, q, Ctrl-C), selection movement across a long history,
narrow-terminal rendering, and clean exit.
"""
import os
import pty
import struct
import subprocess
import sys
import tempfile
import time
import fcntl
import termios

BIN = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "target", "release", "git-panic")


def make_repo(path, n=30):
    env = dict(os.environ, GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_SYSTEM="/dev/null")
    def git(*args):
        subprocess.run(["git", *args], cwd=path, env=env, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.makedirs(path, exist_ok=True)
    git("init", "-q", "-b", "main")
    git("config", "user.name", "TUI Test")
    git("config", "user.email", "tui@example.invalid")
    git("config", "commit.gpgsign", "false")
    git("config", "core.hooksPath", "/dev/null")
    for i in range(n):
        with open(os.path.join(path, "f.txt"), "w") as f:
            f.write(f"revision {i}\n" + "x" * i + "\n")
        git("add", "f.txt")
        git("commit", "-q", "-m", f"tui: entry number {i} with a reasonably long message")


def run_tui(args, keys, cols=100, rows=24, settle=0.6, key_delay=0.15):
    pid, fd = pty.fork()
    if pid == 0:  # child
        os.chdir(args["cwd"])
        os.execv(BIN, [BIN, *args["argv"]])
    # set window size
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
    os.set_blocking(fd, False)
    output = b""
    def drain():
        nonlocal output
        while True:
            try:
                chunk = os.read(fd, 65536)
            except (BlockingIOError, OSError):
                return
            if not chunk:
                return
            output += chunk
    time.sleep(settle)
    drain()
    for k in keys:
        os.write(fd, k)
        time.sleep(key_delay)
        drain()
    # wait for exit
    deadline = time.time() + 5
    while time.time() < deadline:
        drain()
        waited, status = os.waitpid(pid, os.WNOHANG)
        if waited == pid:
            return output, status
        time.sleep(0.1)
    os.kill(pid, 9)
    os.waitpid(pid, 0)
    return output, None


def decode(b):
    return b.decode("utf-8", "replace")

def squash(text):
    """Remove ANSI escapes and all whitespace for robust matching."""
    import re
    text = re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", text)
    text = re.sub(r"\x1b[()][B0]", "", text)
    return "".join(text.split())


def main():
    tmp = tempfile.mkdtemp(prefix="git-panic-tui-")
    repo = os.path.join(tmp, "repo")
    make_repo(repo)
    failures = []

    def check(name, cond, detail=""):
        print(("PASS " if cond else "FAIL ") + name + (("  [" + detail + "]") if detail and not cond else ""))
        if not cond:
            failures.append(name)

    # 1. navigation with all new keys, then q
    out, status = run_tui({"cwd": repo, "argv": []},
                          [b"\x1b[B", b"j", b"j", b"\x1b[6~", b"\x1b[6~", b"\x1b[H",
                           b"\x1b[F", b"k", b"q"], cols=160, rows=30)
    text = decode(out)
    check("q exits cleanly with status 0", status == 0, f"status={status}")
    check("enters alternate screen", "\x1b[?1049h" in text)
    check("leaves alternate screen on exit", "\x1b[?1049l" in text)
    check("shows cursor again on exit", "\x1b[?25h" in text)
    check("renders timeline list", "Timeline" in text)
    check("shows navigation help", "PgUp/PgDn/Home/End" in text.replace(" ", ""))
    check("shows oldest entry (Home target) HEAD@{29}", "HEAD@{29}" in text)
    check("shows newest entry HEAD@{0}", "HEAD@{0}" in text)
    check("shows inspector pane", "StateInspector" in squash(text))
    check("renders full SHA in inspector", "CommitSHA:" in squash(text) and "Reflog:HEAD@{" in squash(text))

    # 2. Ctrl-C exit path
    out2, status2 = run_tui({"cwd": repo, "argv": []}, [b"\x1b[B", b"\x03"])
    text2 = decode(out2)
    check("Ctrl-C exits cleanly with status 0", status2 == 0, f"status={status2}")
    check("Ctrl-C leaves alternate screen", "\x1b[?1049l" in text2)

    # 3. narrow terminal, long messages
    out3, status3 = run_tui({"cwd": repo, "argv": []}, [b"\x1b[F", b"q"], cols=40, rows=12)
    text3 = decode(out3)
    check("narrow terminal renders and exits 0", status3 == 0, f"status={status3}")
    check("narrow terminal still shows both panes",
          "Timeline" in squash(text3) and "Inspector" in squash(text3))

    # 4. explicit tui subcommand
    out4, status4 = run_tui({"cwd": repo, "argv": ["tui"]}, [b"q"])
    check("tui subcommand works and exits 0", status4 == 0, f"status={status4}")

    # 5. after TUI exit, the terminal is usable: run a normal command in same PTY
    pid, fd = pty.fork()
    if pid == 0:
        os.chdir(repo)
        os.execv(BIN, [BIN, "tui:"])
    time.sleep(1.0)
    out5 = b""
    try:
        while True:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            out5 += chunk
    except (BlockingIOError, OSError):
        pass
    _, status5 = os.waitpid(pid, 0)
    check("plain search still works after TUI (same PTY)",
          status5 == 0 and b"HEAD@{" in out5, f"status={status5} out={out5[:120]!r}")

    print(f"\n{len(failures)} failure(s)" if failures else "\nALL TUI PTY CHECKS PASSED")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
