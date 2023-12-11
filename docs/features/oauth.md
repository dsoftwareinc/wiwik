# Authentication & Authorization

## Authentication

### OAuth

wiwik can integrate with various external oauth parties such as Google,
facebook, okta, etc.

To do this, most third parties require some setup on their side to
identify wiwik as a new app authenticating using oauth and wiwik requires some
settings on the environment variables.

### Self-authentication management

wiwik can also allow maintaining its own authentication database. This is a
valid use-case when wiwik is being tried out by a small group as it enables
quick deployment without the need to configure any third party.

## Authorization

All active users are able to view posts that are not associated with any
specific space, i.e., posts that are public.

Users can be associated with spaces (become space members), and gain access to
posts available only on these spaces.

Users can be associated with one or more team.

User/Team access to create new posts can be managed via the admin views.

User/Team access to edit/delete exiting posts (moderation) can be managed via
the admin views, however, based on users' feedback, it is good to grant this
access based on the engagement of the users with the platform - i.e., if a user
visited daily for 30 days, or reached certain reputation.


## Technical details

All relevant data is under `userauth` app.
