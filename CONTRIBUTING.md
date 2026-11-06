# Contributing to KeyLayoutFixer

Thank you for your interest in contributing!

## How to Contribute

### Reporting Bugs

1. Check if the bug is already reported in [Issues](../../issues)
2. Create a new issue with:
   - Clear title
   - Steps to reproduce
   - Expected vs actual behavior
   - Your OS and Python version (`python --version`, `klf --version`)

### Suggesting Features

1. Open an issue with the `enhancement` label
2. Describe the feature clearly
3. Explain why it would be useful

### Code Contributions

1. Fork the repository
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run the tests (`python -m pytest -q`)
5. Commit with clear messages
6. Push to your fork
7. Open a Pull Request

## Code Style

- Use clear variable names
- Add comments for complex logic
- Keep functions small and focused
- No emojis in code, comments or commit messages

## The mapping table

`keylayoutfixer/mapping.py` is the core of this project. Any change to
it must:

- Cite ISIRI 9147 (the Iranian national standard for the Persian
  keyboard layout) for the new value
- Keep `tests/test_mapping.py` green, especially the round-trip test
  for every mappable character (`convert(convert(x)) == x`)

## Testing

Before submitting:

- Run the full suite: `python -m pytest -q`
- Test the CLI by hand: `klf --text sghl`, `echo sghl | klf`, `klf`
- Test with both Persian and English text, including digits and
  shifted punctuation (`?`, `«»`, `()`, `{}`)
- If you touched tray mode, test it on a real desktop (hotkey +
  tray icon cannot be tested in CI)

## Questions?

Feel free to open an issue for any questions!
