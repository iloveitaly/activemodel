[macos]
db_play:
	uv tool run pgcli $DATABASE_URL

up:
	docker compose up -d


gh_configure:
	repo_path=$(gh repo view --json nameWithOwner --jq '.nameWithOwner') && \
		gh api --method PUT "/repos/${repo_path}/actions/permissions/workflow" \
			-f default_workflow_permissions=write \
			-F can_approve_pull_request_reviews=true && \
		gh api "/repos/${repo_path}/actions/permissions/workflow"