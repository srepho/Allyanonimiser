# Allyanonimiser Documentation

This directory contains the MkDocs-based documentation for the Allyanonimiser project.

## Setup

To work with the documentation, install the required dependencies:

```bash
pip install -r docs/requirements.txt
```

## Building the Documentation

To build and serve the documentation locally:

```bash
mkdocs serve
```

This will start a local server at http://127.0.0.1:8000/ where you can preview the documentation.

To build the static site without serving:

```bash
mkdocs build
```

The built documentation will be in the `site/` directory.

## Deploying to GitHub Pages

To deploy the documentation to GitHub Pages:

```bash
mkdocs gh-deploy
```

This command builds the documentation and pushes it to the `gh-pages` branch of your repository.

## Documentation Structure

- `docs/index.md`: Main landing page
- `docs/getting-started/`: Installation and quick start guides
- `docs/usage/`: Detailed usage guides
- `docs/patterns/`: Pattern reference documentation
- `docs/advanced/`: Advanced features documentation
- `docs/api/`: API reference documentation
- `docs/examples/`: Example code and tutorials
- `docs/css/`: Custom CSS styles
- `docs/assets/`: Images and other assets

## Adding New Pages

1. Create a new Markdown file in the appropriate subdirectory
2. Add the page to the navigation menu in `mkdocs.yml`
3. Link to the page from related pages

## Styling

Custom CSS styles are in `docs/css/extra.css`. The documentation uses the Material for MkDocs theme.

## API Documentation

API documentation is generated automatically using mkdocstrings. To document a new class or function:

1. Make sure it has a proper docstring in the Python code
2. Create a reference to it in the appropriate API documentation page

Example:

```python
::: allyanonimiser.Allyanonimiser
    options:
      show_root_heading: true
      show_source: true
```