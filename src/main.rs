use anyhow::{Context, Result};
use clap::{Parser, Subcommand};
use git2::{Repository, Oid};
use crossterm::{
    event::{self, Event, KeyCode},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{
    backend::CrosstermBackend,
    layout::{Constraint, Direction, Layout},
    widgets::{Block, Borders, List, ListItem, Paragraph},
    Terminal,
};
use std::{io, path::PathBuf};

#[derive(Parser)]
#[command(
    name = "git-panic",
    author = "DudeSquad999",
    version = "0.1.0",
    about = "Visual Git Reflog Time Machine & Disaster Recovery CLI",
    long_about = "Scrub back in time, inspect visual diffs, and safely recover lost work from reflogs."
)]
struct Cli {
    /// Optional natural language search query against git reflog
    query: Option<String>,

    #[command(subcommand)]
    command: Option<Commands>,
}

#[derive(Subcommand)]
enum Commands {
    /// Launch the interactive TUI time machine
    Tui,
    /// Quick lookup for snapshots by relative time
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

    let repo_path = PathBuf::from(".");
    let repo = Repository::discover(&repo_path)
        .context("Failed to locate git repository. Are you in a valid git directory?")?;

    let reflogs = extract_reflogs(&repo)?;

    if let Some(query) = cli.query {
        println!("🔍 Scanning reflog for query: \"{}\"...", query);
        let matches = filter_reflog(&reflogs, &query);
        if matches.is_empty() {
            println!("❌ No matching reflog entries found.");
        } else {
            println!("\nFound {} relevant reflog state(s):", matches.len());
            for m in matches {
                println!("  [{}] {} - {}", m.index, &m.oid.to_string()[..7], m.message);
            }
            println!("\nRun `git panic` to open the interactive TUI time machine.");
        }
        return Ok(());
    }

    match cli.command {
        Some(Commands::Tui) | None => run_tui(&repo, reflogs)?,
        Some(Commands::Snapshot { before }) => {
            println!("🕒 Searching for snapshots before: {}", before);
        }
    }

    Ok(())
}

fn extract_reflogs(repo: &Repository) -> Result<Vec<ReflogItem>> {
    let mut items = Vec::new();
    let reflog = repo.reflog("HEAD")?;

    for (i, entry) in reflog.iter().enumerate() {
        let oid = entry.id_new();
        let msg = entry.message().unwrap_or("No commit message").to_string();
        items.push(ReflogItem {
            oid,
            message: msg,
            index: i,
        });
    }

    Ok(items)
}

fn filter_reflog(reflogs: &[ReflogItem], query: &str) -> Vec<ReflogItem> {
    let q = query.to_lowercase();
    reflogs
        .iter()
        .filter(|item| item.message.to_lowercase().contains(&q))
        .cloned()
        .collect()
}

fn run_tui(_repo: &Repository, reflogs: Vec<ReflogItem>) -> Result<()> {
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    let mut selected_idx = 0;

    loop {
        terminal.draw(|f| {
            let chunks = Layout::default()
                .direction(Direction::Horizontal)
                .constraints([Constraint::Percentage(40), Constraint::Percentage(60)].as_ref())
                .split(f.size());

            let list_items: Vec<ListItem> = reflogs
                .iter()
                .enumerate()
                .map(|(i, item)| {
                    let style = if i == selected_idx {
                        ratatui::style::Style::default()
                            .fg(ratatui::style::Color::Yellow)
                            .add_modifier(ratatui::style::Modifier::BOLD)
                    } else {
                        ratatui::style::Style::default()
                    };
                    ListItem::new(format!("HEAD@{{{}}} [{}] {}", item.index, &item.oid.to_string()[..7], item.message))
                        .style(style)
                })
                .collect();

            let list = List::new(list_items)
                .block(Block::default().title(" 🚨 Git-Panic Timeline ").borders(Borders::ALL));

            f.render_widget(list, chunks[0]);

            let active_item = &reflogs[selected_idx];
            let detail_text = format!(
                "Commit SHA: {}\nReflog Index: HEAD@{{{}}}\nAction: {}\n\nPress 'R' to restore this state into a safety branch.\nPress 'q' to quit.",
                active_item.oid, active_item.index, active_item.message
            );

            let details = Paragraph::new(detail_text)
                .block(Block::default().title(" 🔍 State Inspector ").borders(Borders::ALL));

            f.render_widget(details, chunks[1]);
        })?;

        if let Event::Key(key) = event::read()? {
            match key.code {
                KeyCode::Char('q') => break,
                KeyCode::Down => {
                    if selected_idx + 1 < reflogs.len() {
                        selected_idx += 1;
                    }
                }
                KeyCode::Up => {
                    if selected_idx > 0 {
                        selected_idx -= 1;
                    }
                }
                _ => {}
            }
        }
    }

    disable_raw_mode()?;
    execute!(terminal.backend_mut(), LeaveAlternateScreen)?;
    terminal.show_cursor()?;

    println!("👋 Exited git-panic.");
    Ok(())
}
