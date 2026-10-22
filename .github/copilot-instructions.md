# Copilot instructions

## Project overview

This repository contains a Python discrete-event simulation for neuropsychological patient appointments, plus the thesis and presentation in LaTeX. The current simulation models patient arrivals, a shared pool of professionals, appointments, and professional-level utilization metrics; triage and the multiple-appointment diagnosis flow are project goals, not yet implemented behavior. The latest thesis article is in `articles/tcc2`.

## Thesis materials

Do not edit thesis or presentation materials under `articles/`, including LaTeX sources, bibliographies, figures, and generated documents. You may read them to understand project context and suggest changes, but make no direct modifications to them, even when asked to edit or build the thesis.

The runtime starts in `src/main.py`: it creates a SimPy environment and an `Equipe`, then runs and summarizes a `Simulador`. `Simulador` generates patients and starts a SimPy process per arrival. `Equipe` coordinates its professionals through a `simpy.Store`, so patients wait for the first available professional; each `Profissional` also owns its own SimPy resource and records completed appointment durations and utilization samples. `Paciente` holds patient state, and `Suspeita` defines the available suspicion values. Team and professional summaries feed the simulator's console report and CSV export (`output/data.csv`).

## Build, test, and lint

Install dependencies with `poetry install`, then use Poetry to run project tasks:

```bash
poetry run task run
poetry run task test
poetry run task lint:black:check
poetry run task lint:black:fix
poetry run task build:article
```

`task build:article` compiles `articles/tcc2/tcc.tex` with `latexmk`; it requires the LaTeX tools to be installed. Tests use pytest with `src` on the import path. To run one test, pass its node ID directly to pytest:

```bash
poetry run pytest tests/unit/classes/test_equipe.py::test_when_requesting_and_releasing_a_professional
```

## Repository conventions

- Python identifiers, domain concepts, and user-facing messages generally use Portuguese (`Paciente`, `Equipe`, `Suspeita`, `triagem_feita`). Follow that vocabulary in related code.
- Import domain classes from `classes` and enum classes from `enums`. `classes/__init__.py` explicitly re-exports its classes; `enums/__init__.py` discovers and re-exports classes in the enum package.
- Simulation timing and concurrency are expressed with SimPy processes, events, and timeouts on the shared environment. Return a professional to `Equipe` after an appointment so the shared waiting line continues to make progress.
- Tests live under `tests/unit/classes/` and use pytest functions named `test_when_...`; parameterize related input cases with pytest when appropriate.
- Treat the article directories as separate thesis versions/materials. The README's build task targets `articles/tcc2`, not the other article folders.

## Commit messages

Use Conventional Commit-style prefixes followed by a concise description, for example `feat: add patient triage`, `test: cover team release`, `fix: correct class imports`, or `ci: configure package mode`. Keep the subject focused on the change.

## CI and Commitizen

The pull-request workflow uses Python 3.14 and runs the test and Black checks; its Commitizen Conventional Commit check is advisory (`continue-on-error: true`). `poetry run task commit` starts the interactive Commitizen commit flow.

The README defines `poetry run task build:article` to compile `articles/tcc2/tcc.tex`. Do not run this task: it can modify generated thesis materials under `articles/`.

## Pull requests and commit language

Write pull request titles and descriptions in Portuguese. Write commit messages in English, following the Conventional Commit format described above.
