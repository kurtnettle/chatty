from invoke import task


@task
def clean(c, docs=False, bytecode=False, extra=""):
    c.run("pyclean .", pty=True)


@task
def lint(c) -> None:
    """
    Lint the codebase using ruff.
    """
    c.run("ruff check .", pty=True)


@task
def format(c) -> None:
    """
    Format the codebase using isort, black and ruff.
    """
    c.run("isort --profile black .", pty=True)
    c.run("black .", pty=True)
    c.run("ruff format .", pty=True)


@task
def run(c) -> None:
    """
    Start the app
    """
    c.run("streamlit run app.py --server.runOnSave true", pty=True)
