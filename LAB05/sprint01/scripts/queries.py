# REST endpoint builders — each returns a path fragment appended to REST_BASE_URL
REST_QUERY_URLS = {
    "repo_info": lambda owner, repo: f"/repos/{owner}/{repo}",
    "issues": lambda owner, repo: f"/repos/{owner}/{repo}/issues?per_page=20&state=open",
    "pull_requests": lambda owner, repo: f"/repos/{owner}/{repo}/pulls?per_page=20&state=open",
    "commits": lambda owner, repo: f"/repos/{owner}/{repo}/commits?per_page=20",
}

# GraphQL query strings — variables: {owner: str, name: str}
# Fields are chosen to be semantically equivalent to what a client would use
# from the REST responses, demonstrating over-fetching on the REST side.
GRAPHQL_QUERY_STRINGS = {
    "repo_info": """
query RepoInfo($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    name
    nameWithOwner
    description
    stargazerCount
    forkCount
    openIssues: issues(states: OPEN) { totalCount }
    primaryLanguage { name }
    updatedAt
    createdAt
    watchers { totalCount }
    defaultBranchRef { name }
    licenseInfo { name }
    diskUsage
  }
}
""",
    "issues": """
query RepoIssues($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    issues(first: 20, states: OPEN, orderBy: {field: CREATED_AT, direction: DESC}) {
      nodes {
        number
        title
        state
        createdAt
        updatedAt
        author { login }
        labels(first: 5) { nodes { name } }
        comments { totalCount }
      }
    }
  }
}
""",
    "pull_requests": """
query RepoPRs($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    pullRequests(first: 20, states: OPEN, orderBy: {field: CREATED_AT, direction: DESC}) {
      nodes {
        number
        title
        state
        createdAt
        updatedAt
        author { login }
        reviewRequests(first: 5) { totalCount }
        commits { totalCount }
      }
    }
  }
}
""",
    "commits": """
query RepoCommits($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    defaultBranchRef {
      target {
        ... on Commit {
          history(first: 20) {
            nodes {
              oid
              messageHeadline
              committedDate
              author { name email }
              additions
              deletions
            }
          }
        }
      }
    }
  }
}
""",
}
