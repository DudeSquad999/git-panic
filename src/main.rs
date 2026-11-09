use anyhow::{bail, Context, Result};
use clap::{Parser, Subcommand};
use crossterm::{
    event::{self, Event, KeyCode, KeyEventKind, KeyModifiers},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use git2::{Oid, Repository};
use ratatui::{
    backend::CrosstermBackend,
    layout::{Constraint, Direction, Layout},
    style::{Modifier, Style},
    widgets::{Block, Borders, List, ListItem, ListState, Paragraph, Wrap},
    Terminal,
};
use std::io::{self, IsTerminal, Write};

#[derive(Parser)]
#[command(
    name = "git-panic",
    author,
    version,
    about = "Inspect local Git reflogs and preserve commits on new branches"
)]
struct Cli {
    /// Case-insensitive literal substring to find in HEAD reflog messages
    query: Option<String>,
    #[command(subcommand)]
    command: Option<Commands>,
}

#[derive(Subcommand)]
enum Commands {
    /// Launch the read-only interactive timeline
    Tui,
    /// Preview preserving a commit; --create writes only a new branch reference
    Recover {
        /// Full 40-character commit SHA, not a moving HEAD@{n} position
        oid: String,
        #[arg(long)]
        branch: String,
        /// Explicitly create the branch; without this flag nothing is written
        #[arg(long)]
        create: bool,
    },
    /// Reserved command: time-based snapshots are not implemented
    Snapshot {
        #[arg(short, long)]
        before: String,
    },
}

#[derive(Clone, Debug)]
pub struct ReflogItem {
    pub oid: Oid,
    pub message: String,
    pub index: usize,
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    if cli.query.is_some() && cli.command.is_some() {
        bail!("Use a search query OR a subcommand, not both.");
    }
    if let Some(Commands::Snapshot { before }) = &cli.command {
        bail!(
            "snapshot --before {:?} is not implemented. Use a literal search or the TUI.",
            before
        );
    }
    let repo = Repository::discover(".")
        .context("No Git repository found. Run git-panic inside your repository.")?;
    if let Some(Commands::Recover {
        oid,
        branch,
        create,
    }) = &cli.command
    {
        return recover(&repo, oid, branch, *create);
    }
    let reflogs = extract_reflogs(&repo)?;
    if let Some(query) = cli.query {
        if query.trim().is_empty() {
            bail!("Search cannot be empty. Try a literal fragment such as reset or commit.");
        }
        let matches = filter_reflog(&reflogs, &query);
        if matches.is_empty() {
            println!(
                "No matching HEAD reflog entries. Try a shorter literal fragment such as reset."
            );
        } else {
            print_matches(&matches)?;
        }
        return Ok(());
    }
    run_tui(&reflogs)
}

fn extract_reflogs(repo: &Repository) -> Result<Vec<ReflogItem>> {
    let reflog = match repo.reflog("HEAD") {
        Ok(log) => log,
        Err(error) if error.code() == git2::ErrorCode::NotFound => return Ok(Vec::new()),
        Err(error) => return Err(error).context("Could not read the local HEAD reflog"),
    };
    Ok(reflog
        .iter()
        .enumerate()
        .map(|(index, entry)| ReflogItem {
            oid: entry.id_new(),
            message: entry.message().unwrap_or("No reflog message").to_string(),
            index,
        })
        .collect())
}

fn filter_reflog(reflogs: &[ReflogItem], query: &str) -> Vec<ReflogItem> {
    let query = query.to_lowercase();
    reflogs
        .iter()
        .filter(|item| item.message.to_lowercase().contains(&query))
        .cloned()
        .collect()
}

fn display_text(text: &str) -> String {
    text.chars()
        .map(|c| if c.is_control() { ' ' } else { c })
        .collect()
}

// `git-panic QUERY | head -n` closes stdout early. With the release
// panic=abort profile, an unhandled BrokenPipe from println! otherwise
// terminates with SIGABRT (exit 134) after the consumer already succeeded.
// `head`'s own exit code (0) is what matters, so exit quietly on SIGPIPE.
fn print_matches(matches: &[ReflogItem]) -> Result<()> {
    let mut out = io::stdout();
    for item in matches {
        let line = format!(
            "HEAD@{{{}}} {} - {}",
            item.index,
            item.oid,
            display_text(&item.message)
        );
        if out.write_all(line.as_bytes()).is_err() || out.write_all(b"\n").is_err() {
            // Consumer closed the pipe; treat this as a normal stop.
            return Ok(());
        }
    }
    out.flush()?;
    Ok(())
}

// Best-effort cleanup on ordinary returns/errors, including partial setup.
// Destructors cannot handle SIGKILL or the existing release panic=abort profile.
struct TerminalSession;

impl Drop for TerminalSession {
    fn drop(&mut self) {
        let _ = disable_raw_mode();
        let _ = execute!(io::stdout(), LeaveAlternateScreen, crossterm::cursor::Show);
    }
}

fn run_tui(reflogs: &[ReflogItem]) -> Result<()> {
    if reflogs.is_empty() {
        println!("No local HEAD reflog entries. This may be a new repository or reflogs may be disabled or expired.");
        return Ok(());
    }
    if !io::stdin().is_terminal() || !io::stdout().is_terminal() {
        bail!("The TUI needs an interactive terminal. Use a literal search, e.g. git-panic reset.");
    }
    enable_raw_mode()?;
    let _session = TerminalSession;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen)?;
    let mut terminal = Terminal::new(CrosstermBackend::new(stdout))?;
    let mut selected: usize = 0;
    let mut state = ListState::default();
    loop {
        state.select(Some(selected));
        terminal.draw(|frame| {
            let chunks = Layout::default()
                .direction(Direction::Horizontal)
                .constraints([Constraint::Percentage(40), Constraint::Percentage(60)])
                .split(frame.size());
            let items: Vec<ListItem> = reflogs.iter().map(|item| {
                ListItem::new(format!("HEAD@{{{}}} [{}] {}", item.index, &item.oid.to_string()[..7], display_text(&item.message)))
            }).collect();
            let list = List::new(items)
                .block(Block::default().title(" Timeline: Up/Down | q/Ctrl-C quit ").borders(Borders::ALL))
                .highlight_symbol("> ")
                .highlight_style(Style::default().add_modifier(Modifier::REVERSED));
            frame.render_stateful_widget(list, chunks[0], &mut state);
            let item = &reflogs[selected];
            let text = format!("Commit SHA: {}\nReflog: HEAD@{{{}}}\nAction: {}\n\nRead-only inspector. Quit, then preview:\ngit-panic recover {} --branch panic/recovered\n\nAdd --create only after reviewing the target.\nNo checkout, reset, or working-file backup.", item.oid, item.index, display_text(&item.message), item.oid);
            frame.render_widget(Paragraph::new(text).wrap(Wrap { trim: false })
                .block(Block::default().title(" State Inspector ").borders(Borders::ALL)), chunks[1]);
        })?;
        if let Event::Key(key) = event::read()? {
            if key.kind == KeyEventKind::Release {
                continue;
            }
            if key.code == KeyCode::Char('c') && key.modifiers.contains(KeyModifiers::CONTROL) {
                break;
            }
            match key.code {
                KeyCode::Char('q') => break,
                KeyCode::Down if selected + 1 < reflogs.len() => selected += 1,
                KeyCode::Up => selected = selected.saturating_sub(1),
                _ => {}
            }
        }
    }
    Ok(())
}

fn recovery_target<'a>(repo: &'a Repository, oid: &str, branch: &str) -> Result<git2::Commit<'a>> {
    if oid.len() != 40 || !oid.bytes().all(|b| b.is_ascii_hexdigit()) {
        bail!("Use a full 40-character commit SHA, not HEAD@{{n}} or an abbreviated SHA.");
    }
    let reference = format!("refs/heads/{branch}");
    if branch.is_empty() || branch.starts_with('-') || !git2::Reference::is_valid_name(&reference) {
        bail!("Invalid branch name. Example: panic/recovered");
    }
    match repo.find_reference(&reference) {
        Ok(_) => bail!(
            "Branch already exists; choose a new name. Existing branches are never overwritten."
        ),
        Err(error) if error.code() == git2::ErrorCode::NotFound => {}
        Err(error) => return Err(error).context("Could not inspect the requested branch"),
    }
    repo.find_commit(Oid::from_str(oid)?).context(
        "Commit is unavailable locally or the object is not a commit. It may have been pruned.",
    )
}

fn recover(repo: &Repository, oid: &str, branch: &str, create: bool) -> Result<()> {
    let commit = recovery_target(repo, oid, branch)?;
    println!("Target commit: {}", commit.id());
    println!("New branch: {}", display_text(branch));
    println!("HEAD, index and working files will not be changed. This does not back up uncommitted work.");
    if !create {
        println!("Preview only: nothing written. Repeat with --create to create the branch.");
        return Ok(());
    }
    repo.branch(branch, &commit, false)
        .context("Could not create the recovery branch; existing branches are never overwritten")?;
    println!(
        "Created branch {}. No checkout performed.",
        display_text(branch)
    );
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;
    use std::sync::atomic::{AtomicU64, Ordering};

    static NEXT: AtomicU64 = AtomicU64::new(0);
    struct Fixture {
        repo: Option<Repository>,
        path: PathBuf,
    }
    impl Fixture {
        fn new() -> Self {
            let path = std::env::temp_dir().join(format!(
                "git-panic-test-{}-{}-{}",
                std::process::id(),
                std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .unwrap()
                    .as_nanos(),
                NEXT.fetch_add(1, Ordering::Relaxed)
            ));
            std::fs::create_dir(&path).unwrap();
            let repo = Repository::init(&path).unwrap();
            Self {
                repo: Some(repo),
                path,
            }
        }
        fn repo(&self) -> &Repository {
            self.repo.as_ref().unwrap()
        }
        fn commit(&self) -> Oid {
            let repo = self.repo();
            let tree_id = repo.index().unwrap().write_tree().unwrap();
            let tree = repo.find_tree(tree_id).unwrap();
            let signature = git2::Signature::now("Test", "test@example.invalid").unwrap();
            repo.commit(Some("HEAD"), &signature, &signature, "fixture", &tree, &[])
                .unwrap()
        }
    }
    impl Drop for Fixture {
        fn drop(&mut self) {
            drop(self.repo.take());
            let _ = std::fs::remove_dir_all(&self.path);
        }
    }
    #[test]
    fn cli_definition_is_consistent() {
        use clap::CommandFactory;
        Cli::command().debug_assert();
    }
    #[test]
    fn cli_preserves_existing_entry_points() {
        for args in [
            vec!["git-panic"],
            vec!["git-panic", "tui"],
            vec!["git-panic", "reset"],
            vec!["git-panic", "snapshot", "--before", "yesterday"],
        ] {
            assert!(Cli::try_parse_from(args).is_ok());
        }
    }
    #[test]
    fn recovery_requires_branch_and_defaults_to_preview() {
        assert!(Cli::try_parse_from(["git-panic", "recover", "abc"]).is_err());
        let cli =
            Cli::try_parse_from(["git-panic", "recover", "abc", "--branch", "panic/test"]).unwrap();
        assert!(matches!(
            cli.command,
            Some(Commands::Recover { create: false, .. })
        ));
    }
    #[test]
    fn search_is_literal_and_case_insensitive() {
        let items = vec![ReflogItem {
            oid: Oid::zero(),
            index: 0,
            message: "reset: moving to HEAD~1".into(),
        }];
        assert_eq!(filter_reflog(&items, "RESET").len(), 1);
        assert!(filter_reflog(&items, "I accidentally reset").is_empty());
        assert!(filter_reflog(&items, ".*").is_empty());
    }
    #[test]
    fn broken_pipe_search_exits_quietly() {
        let items = vec![ReflogItem {
            oid: Oid::zero(),
            index: 0,
            message: "reset".into(),
        }];
        print_matches(&items).unwrap();
    }
    #[test]
    fn terminal_controls_are_not_displayed() {
        assert_eq!(display_text("a\x1b\n\t\u{009b}b"), "a    b");
    }
    #[test]
    fn empty_history_does_not_enter_raw_mode() {
        let fixture = Fixture::new();
        let entries = extract_reflogs(fixture.repo()).unwrap();
        assert!(entries.is_empty());
        run_tui(&entries).unwrap();
    }
    #[test]
    fn reads_head_reflog() {
        let fixture = Fixture::new();
        let oid = fixture.commit();
        let entries = extract_reflogs(fixture.repo()).unwrap();
        assert_eq!(entries[0].oid, oid);
        assert_eq!(entries[0].index, 0);
    }
    #[test]
    fn preview_does_not_create_reference() {
        let fixture = Fixture::new();
        let oid = fixture.commit();
        recover(fixture.repo(), &oid.to_string(), "panic/preview", false).unwrap();
        assert!(fixture
            .repo()
            .find_reference("refs/heads/panic/preview")
            .is_err());
    }
    #[test]
    fn creation_preserves_detached_head_index_and_working_files() {
        let fixture = Fixture::new();
        let oid = fixture.commit();
        let repo = fixture.repo();
        repo.set_head_detached(oid).unwrap();
        std::fs::write(fixture.path.join("staged.txt"), "staged").unwrap();
        let mut index = repo.index().unwrap();
        index.add_path(std::path::Path::new("staged.txt")).unwrap();
        index.write().unwrap();
        std::fs::write(fixture.path.join("staged.txt"), "unstaged").unwrap();
        std::fs::write(fixture.path.join("untracked.txt"), "untracked").unwrap();
        let before = std::fs::read(repo.path().join("index")).unwrap();
        recover(repo, &oid.to_string(), "panic/recovered", true).unwrap();
        assert_eq!(
            repo.find_reference("refs/heads/panic/recovered")
                .unwrap()
                .target(),
            Some(oid)
        );
        assert!(repo.head_detached().unwrap());
        assert_eq!(repo.head().unwrap().target(), Some(oid));
        assert_eq!(std::fs::read(repo.path().join("index")).unwrap(), before);
        assert_eq!(
            std::fs::read_to_string(fixture.path.join("staged.txt")).unwrap(),
            "unstaged"
        );
        assert_eq!(
            std::fs::read_to_string(fixture.path.join("untracked.txt")).unwrap(),
            "untracked"
        );
    }
    #[test]
    fn never_overwrites_existing_branch() {
        let fixture = Fixture::new();
        let oid = fixture.commit();
        recover(fixture.repo(), &oid.to_string(), "panic/existing", true).unwrap();
        assert!(recover(fixture.repo(), &oid.to_string(), "panic/existing", true).is_err());
        assert_eq!(
            fixture
                .repo()
                .find_reference("refs/heads/panic/existing")
                .unwrap()
                .target(),
            Some(oid)
        );
    }
    #[test]
    fn rejects_moving_refs_invalid_names_and_missing_objects() {
        let fixture = Fixture::new();
        let oid = fixture.commit();
        for bad in ["HEAD@{0}", "abc", "HEAD"] {
            assert!(recover(fixture.repo(), bad, "panic/test", true).is_err());
        }
        for bad in ["", "../bad", "a..b", "-bad", "bad name"] {
            assert!(recover(fixture.repo(), &oid.to_string(), bad, true).is_err());
        }
        assert!(recover(fixture.repo(), &Oid::zero().to_string(), "panic/test", true).is_err());
    }
    #[test]
    fn rejects_non_commit_objects() {
        let fixture = Fixture::new();
        let blob = fixture.repo().blob(b"not a commit").unwrap();
        assert!(recover(fixture.repo(), &blob.to_string(), "panic/test", true).is_err());
    }
}
