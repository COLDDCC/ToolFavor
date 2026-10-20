# ToolFavor accounts — deployment checklist

This is an API scaffold, **not a finished login experience**. No users can sign up until a compatible identity provider is configured and a frontend authentication flow is built.

## Cloudflare D1
1. Create a D1 database named `toolfavor-db`.
2. Replace `REPLACE_WITH_YOUR_D1_DATABASE_ID` in wrangler.toml with the real database UUID.
3. Apply `schema.sql` to D1 using Wrangler's remote execution or the Cloudflare dashboard.
4. Deploy through Cloudflare Pages with the Functions directory.

## Identity provider
Configure a trusted OpenID Connect provider that issues RS256 JWT access tokens.
Set server-side environment variables:
- `AUTH_ISSUER`: exact JWT issuer.
- `AUTH_AUDIENCE`: expected API audience.
- `AUTH_JWKS_URL`: trusted HTTPS JWKS endpoint.

The API verifies JWT signatures and checks issuer, audience and expiry. Do not place credentials or private signing keys in client-side code. Before enabling public signup, additionally configure and verify provider login/logout, token acquisition, CSRF and abuse protections, token renewal, email verification, and account recovery.

## API contracts
- GET /api/profile — bearer auth, returns current profile
- POST /api/profile — creates or edits current profile; username is immutable
- GET /api/projects — returns own projects
- POST /api/projects — creates own project
- DELETE /api/projects — deletes own project by JSON id
- GET /api/creators/:username — public profile and public projects

Numeric IDs are assigned by D1's AUTOINCREMENT primary key; usernames are unique case-insensitively. Deleting an account must never result in reusing an old numeric ID. Account deletion, moderation, editing projects, and creator ownership verification are not implemented yet.

## Current limitations
- `/creators/colddcc.html` is a static portfolio example, not a registered account.
- Authentication frontend and signup are not yet implemented.
- Do not claim this is production-ready or publicly available until the provider, database, security testing, and deployment are complete.
