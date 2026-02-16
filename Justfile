set unstable := true

# Set up the Python environment, done automatically for you when using direnv
setup:
    uv venv && uv sync
    @echo "activate: source ./.venv/bin/activate"

# Start docker services
up:
    docker compose up -d --wait

[macos]
db_play:
    uv tool run pgcli $DATABASE_URL

# Run tests
test:
    uv run pytest -v

# python linting checks
[script]
lint FILES=".":
    set +e
    exit_code=0

    if [ -n "${CI:-}" ]; then
        # CI mode: GitHub-friendly output
        uv run ruff check --output-format=github {{FILES}} || exit_code=$?
        uv run ruff format --check {{FILES}} || exit_code=$?

        uv run pyright {{FILES}} --outputjson > pyright_report.json || exit_code=$?
        jq -r \
            --arg root "$GITHUB_WORKSPACE/" \
            '
                .generalDiagnostics[] |
                .file as $file |
                ($file | sub("^\\Q\($root)\\E"; "")) as $rel_file |
                "::\(.severity) file=\($rel_file),line=\(.range.start.line),endLine=\(.range.end.line),col=\(.range.start.character),endColumn=\(.range.end.character)::\($rel_file):\(.range.start.line): \(.message)"
            ' < pyright_report.json
        rm pyright_report.json
    else
        # Local mode: regular output
        uv run ruff check {{FILES}} || exit_code=$?
        uv run ruff format --check {{FILES}} || exit_code=$?
        uv run pyright {{FILES}} || exit_code=$?
    fi

    if [ $exit_code -ne 0 ]; then
        echo "One or more linting checks failed"
        exit 1
    fi

# Automatically fix linting errors
lint-fix:
    uv run ruff check . --fix
    uv run ruff format .

# Clean build artifacts and cache
clean:
    rm -rf *.egg-info .venv || true
    find . -type f -name "*.pyc" -delete
    find . -type d -name "__pycache__" -delete || true

# Update copier template
update_from_upstream_template:
    uv tool run --with jinja2_shell_extension \
        copier@latest update --vcs-ref=HEAD --trust --skip-tasks --skip-answered

GITHUB_PROTECT_MASTER_RULESET := """
{
	"name": "Protect master from force pushes",
	"target": "branch",
	"enforcement": "active",
	"conditions": {
		"ref_name": {
			"include": ["refs/heads/master"],
			"exclude": []
		}
	},
	"rules": [
		{
			"type": "non_fast_forward"
		}
	]
}
"""

_github_repo:
	gh repo view --json nameWithOwner -q .nameWithOwner

# TODO this only supports deleting the single ruleset specified above
github_ruleset_protect_master_delete:
	repo=$(just _github_repo) && \
	  ruleset_name=$(echo '{{GITHUB_PROTECT_MASTER_RULESET}}' | jq -r .name) && \
		ruleset_id=$(gh api repos/$repo/rulesets --jq ".[] | select(.name == \"$ruleset_name\") | .id") && \
		(([ -n "${ruleset_id}" ] || (echo "No ruleset found" && exit 0)) || gh api --method DELETE repos/$repo/rulesets/$ruleset_id)

# adds github ruleset to prevent --force and other destructive actions on the github main branch
github_ruleset_protect_master_create: github_ruleset_protect_master_delete
	gh api --method POST repos/$(just _github_repo)/rulesets --input - <<< '{{GITHUB_PROTECT_MASTER_RULESET}}'

INVESTIGATE_PATCHES_PROMPT := '''
Take a look at this patched function from an external package. The assertion that is in place is breaking because the upstream package was mutated.

I want you to investigate the changes in that function between The current version of that package that is used in this project and the most recent version. Take a look our patch and:

1. Check the latest version of the package in pypi and update the version reference in pyproject.toml and `uv sync`
2. Update the patch if necessary to be compatible with the latest logic in the upstream package.
3. Provide a summary of the changes made in the latest version of that function.
'''

# Output the investigate patches prompt
investigate-patches-prompt:
	@echo '{{INVESTIGATE_PATCHES_PROMPT}}'

# Output logs of the last failed 'build' workflow for the current branch
[script]
github_last_build_failure:
    BRANCH=$(git branch --show-current)

    # 1. Fetch last 20 runs (to skip over 'Metadata Sync', 'Dependabot', etc.)
    JSON=$(gh run list -b "$BRANCH" -L 20 --json databaseId,conclusion,workflowName)

    # 2. Filter: Find the latest run where name contains "build" (case-insensitive)
    TARGET=$(echo "$JSON" | jq 'map(select(.workflowName | test("build"; "i"))) | .[0]')

    # 3. Handle case where no build run is found
    if [[ "$TARGET" == "null" ]]; then
        echo "No 'build' workflows found in the last 20 runs for $BRANCH."
        exit 0
    fi

    # 4. Extract Status and ID
    CONCLUSION=$(echo "$TARGET" | jq -r .conclusion)
    ID=$(echo "$TARGET" | jq -r .databaseId)

    # 5. Check Success vs Failure
    if [[ "$CONCLUSION" == "success" ]]; then
        echo "latest build succeeded"
    else
        # Force cat pager to output logs directly to terminal
        GH_PAGER=cat gh run view "$ID" --log-failed
    fi

# Set GitHub Actions permissions for the repository to allow workflows to write and approve PR reviews
# This enables release-please to run without a personal access token
github_repo_permissions_create:
  repo_path=$(gh repo view --json nameWithOwner --jq '.nameWithOwner') && \
    gh api --method PUT "/repos/${repo_path}/actions/permissions/workflow" \
      -f default_workflow_permissions=write \
      -F can_approve_pull_request_reviews=true && \
    gh api "/repos/${repo_path}/actions/permissions/workflow"

github_repo_set_metadata:
	gh repo edit \
		--description "$(yq  '.project.description' pyproject.toml)" \
		--homepage "$(yq '.project.urls.Repository' pyproject.toml)" \
		--add-topic "$(yq '.project.keywords | join(",")' pyproject.toml)"
