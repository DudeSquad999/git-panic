<p align="center">
  <img src="assets/banner.svg" alt="git-panic banner" width="100%">
</p>

<p align="center">
  <a href="https://crates.io/crates/git-panic"><img src="https://img.shields.io/crates/v/git-panic.svg?style=flat-square&color=f85149" alt="Crates.io"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square" alt="License: MIT"></a>
  <a href="https://www.rust-lang.org/"><img src="https://img.shields.io/badge/built_with-Rust-orange.svg?style=flat-square" alt="Built with Rust"></a>
  <a href="https://github.com/DudeSquad999/Prism-Ai"><img src="https://img.shields.io/badge/built_while_building-Prism_AI-blue.svg?style=flat-square" alt="Prism AI"></a>
</p>

<h3 align="center">The CLI emergency room for your terminal.</h3>
<p align="center"><b>Scrub back in time, inspect visual diffs, and restore wiped code from dirty reflogs, stashes, and detached HEADs—100% offline, zero cloud telemetry.</b></p>

```
       _____ _ _       _____ Panic Mode Activated
      / ____(_) |     |  __ \ 
     | |  __ _| |_    | |__) |_ _ _ __  |_ _| ___
     | | |_ | | __|   |  ___/ _` | '_ \  | | / __|
     | |__| | | |_    | |  | (_| | | | | | | \__ \
      \____|_|\__|    |_|   \__,_|_| |_|___|_|___/
```

---

## 💡 The Origin Story

While building **[Prism-AI](https://github.com/DudeSquad999/Prism-Ai/tree/Main)**—a lightweight private neurosymbolic AI engine—I ran into a nightmare scenario: a botched rebase combined with an aggressive AI agent script wiped out hours of custom transformer architecture work. 

Standard `git reflog` gave me an opaque wall of hex hashes like `HEAD@{14}` with zero context. I needed something faster, visual, and bulletproof so I didn't lose my mind (or my code) ever again. So, I built **`git-panic`**.

---

## ✨ Key Features

* 🕒 **Interactive Visual TUI:** Scrub backward and forward through your repository's history using a retro terminal interface.
* 🔍 **State Inspector:** View exact commit SHAs, reflog indices, and action descriptions before taking action.
* 🔒 **Deterministic Safety Net:** Automatically creates a backup safety branch (`panic/pre-restore-TIMESTAMP`) before modifying your working directory.
* ⚡ **Blazing Fast Rust Binary:** Written in zero-cost Rust using `git2` and `ratatui`, booting instantly with zero runtime overhead.
* 📴 **100% Offline Privacy:** Runs completely locally on your machine. Your code never leaves your computer.

---

## 📦 Installation

### Via Cargo (Recommended)
```bash
cargo install git-panic
```

### From Source (Local Development)
```bash
git clone https://github.com/DudeSquad999/git-panic.git
cd git-panic
cargo build --release
```

---

## 🚀 Usage Guide

### 1. Launch the Interactive TUI Time Machine
To open the visual timeline and scrub through your reflog history interactively:
```bash
git-panic
# or via subcommand:
git-panic tui
```

### 2. Natural Language Emergency Query
Search your reflog history instantly using plain English:
```bash
git-panic "I accidentally hard reset main branch"
```

---

## 🎮 TUI Keyboard Shortcuts

| Key | Action |
| :--- | :--- |
| `↑` / `↓` | Navigate up and down through reflog history entries |
| `R` | Restore the selected state into an automatic safety branch |
| `q` | Quit / exit `git-panic` cleanly |

---

## 🏗️ Tech Stack

* **[Clap](https://crates.io/crates/clap)** – Lightning-fast command-line argument parsing.
* **[Git2](https://crates.io/crates/git2)** – Direct Rust bindings to `libgit2` for high-performance low-level reflog inspection.
* **[Ratatui](https://crates.io/crates/ratatui)** & **[Crossterm](https://crates.io/crates/crossterm)** – Robust terminal UI rendering engine.

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.
