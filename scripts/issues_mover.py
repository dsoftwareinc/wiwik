import os
from typing import Dict, Any, Optional

import click
from dotenv import load_dotenv
from github import Github

load_dotenv()  # take environment variables from .env.

THIS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))


class GithubData:
    def __init__(self, source_repo: str, filter_issues: Optional[Dict[str, Any]] = None, dry=True):
        self.labels = None
        self.issues = None
        token = os.getenv('GITHUB_TOKEN', None)
        self.gh_client = Github(token)
        self.filter_issues = filter_issues or dict()
        self.dry = dry or (token is None)
        click.echo(f'Connecting to source repository {source_repo}')
        self.source_repo = self.gh_client.get_repo(source_repo)

    def collect_data(self):
        labels = self.source_repo.get_labels()
        self.labels = [label for label in labels]
        click.echo(f'Got {len(self.labels)} labels in source repository')
        click.echo(f'Getting issues with filter {self.filter_issues}')
        issues = self.source_repo.get_issues(**self.filter_issues)
        self.issues = [issue for issue in issues]
        click.echo(f'Got {len(self.issues)} issues in source repository')


@click.command()
@click.option('--list-only', default=True, show_default=True, help='List issues, do not create')
@click.option('--issue-state', default=None, help='Only issues with state')
@click.argument('source_repo')
def main(list_only: bool, issue_state: str, source_repo: str, ):
    filter_issues = dict(state=issue_state) if issue_state is not None else None
    client = GithubData(source_repo, dry=list_only, filter_issues=filter_issues)
    client.collect_data()
    for label in client.labels:
        click.echo(label)
    for issue in client.issues:
        click.echo(issue)


if __name__ == '__main__':
    main()
