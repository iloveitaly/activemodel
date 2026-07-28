from datetime import datetime

# 1. Basic Project Info
project = "activemodel"
copyright = f"{datetime.now().year}, Michael Bianco"
author = "Michael Bianco"

# 2. Extensions
# AutoAPI is the sole API generator (AST-based; avoids importing patched modules).
# autodoc/napoleon/autodoc-typehints/paramlinks are intentionally omitted.
extensions = [
    "myst_parser",  # Enable Markdown
    "sphinx_design",  # UI Components (Grids/Cards)
    "sphinx_copybutton",  # Code copy button
    "sphinx.ext.viewcode",  # View source code
    "sphinx.ext.intersphinx",  # Link to external docs
    "autoapi.extension",  # Auto-generate API reference
    "sphinx_llm.txt",  # LLM-friendly documentation (llms.txt / llms-full.txt)
]

# Configure AutoAPI
autoapi_dirs = ["../activemodel"]
autoapi_type = "python"
autoapi_ignore = [
    "*/logger.py",
    "*/patches/*",
]
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
]
autoapi_keep_files = False

# Intersphinx configuration
# sqlmodel.tiangolo.com currently serves an empty objects.inv (breaks the build)
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pydantic": (
        "https://docs.pydantic.dev/latest/",
        "https://pydantic.dev/docs/validation/latest/objects.inv",
    ),
    "sqlalchemy": ("https://docs.sqlalchemy.org/en/20/", None),
}
intersphinx_timeout = 10

# sphinx-llm runs a nested markdown build; keep it sequential for clearer errors
llms_txt_build_parallel = False

# 3. Markdown Support Configuration
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

myst_enable_extensions = [
    "colon_fence",  # Use ::: for directives (much cleaner MD)
    "deflist",  # Support for definition lists
    "substitution",  # Use {{ variables }} in Markdown
    "tasklist",  # Enable GitHub-style checkboxes
    "attrs_block",  # CSS classes directly in markdown
    "attrs_inline",  # CSS classes inline
    "smartquotes",  # Typographic curly quotes
]

# Support heading anchors in MyST for README includes
myst_heading_anchors = 3

# 4. Theme & Appearance (Shibuya)
html_theme = "shibuya"
html_baseurl = "https://iloveitaly.github.io/activemodel/"
html_static_path = ["_static"]
html_extra_path = [".nojekyll"]
html_css_files = ["custom.css"]

html_theme_options = {
    "accent_color": "blue",
    "github_url": "https://github.com/iloveitaly/activemodel",
    "light_logo": "_static/logo-nav.png",
    "dark_logo": "_static/logo-nav.png",
    "nav_links": [
        {"title": "Getting Started", "url": "getting-started"},
        {"title": "API Reference", "url": "autoapi/index"},
        {"title": "Changelog", "url": "changelog"},
    ],
}

# 5. sphinx-llm: publish machine-readable docs alongside HTML
llms_txt_enabled = True
llms_txt_full_build = True
llms_txt_description = (
    "ActiveModel: SQLModel with ActiveRecord-style developer ergonomics. "
    "ORM helpers, TypeID/whenever integrations, pytest fixtures, and JSONB mutation tracking."
)
