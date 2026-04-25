# Security Policy

## Supported Versions

OmniGlyph is currently pre-1.0. Security fixes target the latest beta branch.

## Reporting a Vulnerability

Open a private security advisory if hosted on GitHub, or contact the maintainers privately before public disclosure.

## Data Safety Rules

- Do not commit real customer inquiries.
- Do not commit private domain packs unless they are explicitly approved for publication.
- Do not commit upstream full datasets under `data/`.
- Do not publish logs containing customer terms, supplier names, or query patterns.

## MCP Boundary

The MCP server exposes local lookup and normalization tools. It does not implement authentication or access control in the current beta. Run it only in trusted local environments.

## Private Namespace Warning

`private_*` namespaces are data separation markers, not a security boundary. Production deployments must add authentication, authorization, and audit logging before serving private packs to multiple users or agents.
