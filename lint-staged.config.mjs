export default {
  "*.{js,cjs,mjs,jsx,ts,tsx}": ["eslint --fix", "prettier --write"],
  "*.{json,css,scss,md,mdx,yaml,yml}": "prettier --write",
  "*.py": [
    "uv run --project apps/api --locked ruff check --config apps/api/pyproject.toml --fix",
    "uv run --project apps/api --locked ruff format --config apps/api/pyproject.toml",
  ],
};
