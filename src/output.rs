//! Fallible line output with a narrowly scoped broken-pipe exception.
use std::io::{self, Write};

/// Write newline-terminated records and flush once.
///
/// A closed downstream pipe is a normal early stop. Every other write or flush
/// failure is returned to the caller. Records must not contain trailing newlines
/// unless an additional blank line is intended.
pub(crate) fn write_lines<W, I, S>(writer: &mut W, lines: I) -> io::Result<()>
where
    W: Write + ?Sized,
    I: IntoIterator<Item = S>,
    S: AsRef<str>,
{
    let result = (|| {
        for line in lines {
            writer.write_all(line.as_ref().as_bytes())?;
            writer.write_all(b"\n")?;
        }
        writer.flush()
    })();
    match result {
        Err(error) if error.kind() == io::ErrorKind::BrokenPipe => Ok(()),
        other => other,
    }
}

/// Lock standard output for the complete operation and report non-pipe errors.
pub(crate) fn stdout_lines<I, S>(lines: I) -> io::Result<()>
where
    I: IntoIterator<Item = S>,
    S: AsRef<str>,
{
    let stdout = io::stdout();
    let mut writer = stdout.lock();
    write_lines(&mut writer, lines)
}

#[cfg(test)]
mod tests {
    use super::*;

    struct FaultWriter {
        bytes: Vec<u8>,
        fail_after: Option<usize>,
        write_error: io::ErrorKind,
        flush_error: Option<io::ErrorKind>,
        max_chunk: usize,
    }

    impl Write for FaultWriter {
        fn write(&mut self, bytes: &[u8]) -> io::Result<usize> {
            if bytes.is_empty() {
                return Ok(0);
            }
            let available = match self.fail_after {
                Some(limit) => limit.saturating_sub(self.bytes.len()),
                None => usize::MAX,
            };
            if available == 0 {
                return Err(io::Error::new(self.write_error, "injected write failure"));
            }
            let count = bytes.len().min(available).min(self.max_chunk);
            self.bytes.extend_from_slice(&bytes[..count]);
            Ok(count)
        }

        fn flush(&mut self) -> io::Result<()> {
            match self.flush_error {
                Some(kind) => Err(io::Error::new(kind, "injected flush failure")),
                None => Ok(()),
            }
        }
    }

    fn writer() -> FaultWriter {
        FaultWriter {
            bytes: Vec::new(),
            fail_after: None,
            write_error: io::ErrorKind::PermissionDenied,
            flush_error: None,
            max_chunk: usize::MAX,
        }
    }

    #[test]
    fn writes_complete_lines_through_partial_writes() {
        let mut sink = writer();
        sink.max_chunk = 1;
        write_lines(&mut sink, ["alpha", "beta"]).unwrap();
        assert_eq!(sink.bytes, b"alpha\nbeta\n");
    }

    #[test]
    fn broken_pipe_is_success_at_each_write_boundary() {
        for limit in 0..8 {
            let mut sink = writer();
            sink.fail_after = Some(limit);
            sink.write_error = io::ErrorKind::BrokenPipe;
            write_lines(&mut sink, ["abc", "def"]).unwrap();
            assert_eq!(sink.bytes.len(), limit);
        }
    }

    #[test]
    fn non_pipe_write_errors_are_propagated() {
        for kind in [io::ErrorKind::PermissionDenied, io::ErrorKind::Other] {
            for limit in 0..8 {
                let mut sink = writer();
                sink.fail_after = Some(limit);
                sink.write_error = kind;
                let error = write_lines(&mut sink, ["abc", "def"]).unwrap_err();
                assert_eq!(error.kind(), kind);
            }
        }
    }

    #[test]
    fn broken_pipe_during_flush_is_success() {
        let mut sink = writer();
        sink.flush_error = Some(io::ErrorKind::BrokenPipe);
        write_lines(&mut sink, ["abc"]).unwrap();
    }

    #[test]
    fn non_pipe_flush_errors_are_propagated() {
        let mut sink = writer();
        sink.flush_error = Some(io::ErrorKind::Other);
        assert_eq!(
            write_lines(&mut sink, ["abc"]).unwrap_err().kind(),
            io::ErrorKind::Other
        );
    }

    #[test]
    fn zero_length_writes_are_not_silent_success() {
        let mut sink = writer();
        sink.max_chunk = 0;
        assert_eq!(
            write_lines(&mut sink, ["abc"]).unwrap_err().kind(),
            io::ErrorKind::WriteZero
        );
    }

    #[test]
    fn empty_input_still_reports_flush_failure() {
        let mut sink = writer();
        sink.flush_error = Some(io::ErrorKind::Other);
        assert_eq!(
            write_lines(&mut sink, std::iter::empty::<&str>())
                .unwrap_err()
                .kind(),
            io::ErrorKind::Other
        );
    }
}
