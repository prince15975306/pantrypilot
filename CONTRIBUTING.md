# Contributing to PantryPilot

Thanks for your interest! This is an open-source project (MIT) and small, focused contributions are welcome.

## Quick start

```bash
git clone https://github.com/YOUR-USERNAME/YOUR-REPO.git
cd YOUR-REPO
python -m unittest discover -s tests -v
python -m pantrypilot
```

No dependencies to install: the project uses only the Python standard library.

## Ways to help

- Add recipes in `pantrypilot/recipes.py` (ingredients are `(name, quantity, unit)`).
- Improve the ranking in `pantrypilot/planner.py`.
- Add an MCP tool in `pantrypilot/tools.py` (add the handler and an entry in `TOOLS`).
- Improve the dashboard in `web/`.
- Report bugs or confusing docs by opening an issue.

## Pull request checklist

1. Fork the repository and create a branch (`git checkout -b feature/my-change`).
2. Keep the change small and focused.
3. Add or update tests in `tests/` and make sure `python -m unittest discover -s tests` passes.
4. If you change the dashboard, also run `python tests/e2e_dashboard.py` (needs Playwright).
5. Update the README if behaviour or setup changes.
6. Open a pull request describing what changed and why.

## Style

Follow the existing code style, keep functions short, and avoid adding third-party dependencies unless
there is a strong reason.

By contributing you agree that your contribution is licensed under the MIT License.
