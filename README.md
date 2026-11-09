[# 🚨 git-panic

> **The CLI emergency room for your terminal.**  
> *Scrub back in time, inspect visual diffs, and restore wiped code from dirty reflogs, stashes, and detached HEADs—100% offline, zero data sent to the cloud.*

```
       _____ _ _       _____ Panic Mode Activated
      / ____(_) |     |  __ \ 
     | |  __ _| |_    | |__) |_ _ _ __  |_ _| ___
     | | |_ | | __|   |  ___/ _` | '_ \  | | / __|
     | |__| | | |_    | |  | (_| | | | | | | \__ \
      \____|_|\__|    |_|   \__,_|_| |_|___|_|___/
```

[![Crates.io](https://img.shields.io/crates/v/git-panic.svg)](https://crates.io/crates/git-panic)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Rust](https://img.shields.io/badge/built_with-Rust-orange.svg)](https://www.rust-lang.org/)

---

### 💥 The Problem
You ran `git reset --hard HEAD~3`, ran a buggy AI coding agent script that wiped your worktree, or lost uncommitted code during a botched rebase. Standard `git reflog` gives you an opaque wall of hex hashes like `HEAD@{14}` with zero context.

### 🛡️ The Solution
`git-panic` scans your local `.git/logs/reflog`, index snapshots, and orphaned commits to build a visual, scrubbable timeline. It lets you visually inspect lost file state before performing safe, deterministic rollbacks.

```bash
$ git panic "where did my uncommitted edits from 30 mins ago go?"
```

---

## ✨ Features

* 🕒 **Interactive Visual TUI:** Scrub backward and forward through your repo's time history using arrow keys.
* 🔍 **Side-by-Side Diff Inspector:** View exact syntax-highlighted code changes before applying any restore operation.
* 🤖 **Local-First Natural Language Filter:** Parse your intention using lightweight local fuzzy matching or Ollama without sending code off your machine.
* 🔒 **Deterministic Safety Net:** Creates an automatic safety backup branch (`panic/pre-restore-TIMESTAMP`) before touching your working directory.
* ⚡ **Blazing Fast Rust Binary:** Instant boot time with zero runtime dependencies.

---

## ⚡ Quickstart

### Installation

#### Via Cargo (Rust toolchain)
```bash
cargo install git-panic
```

#### Local Development
```bash
git clone https://github.com/your-org/git-panic.git
cd git-panic
cargo run
```
](https://github.com/DudeSquad999/Prism-Ai/tree/Main)
