# Alignn engineering instructions

- Read the approved specification and implementation plan before changing product behavior.
- Build a fresh Next.js and FastAPI application. PostgreSQL is the source of truth; use real PostgreSQL for integration tests.
- Keep authorization and business writes in FastAPI. The web app must not have a second ORM or independent permission model.
- Use Alignn for product naming and `alignn.test` for development email fixtures.
- Apply the approved marketplace direction through reusable semantic tokens and accessible components.
- Never promote mock data, an unconfigured adapter or a concept control as a working production feature.
- Use proportionate checks and report what actually passed. Deployment targets and SLOs in the design are acceptance targets, not measured results.
- Do not invoke Gravitas unless the user explicitly requests it.
- Superpowers remains optional. Do not automatically invoke any Superpowers skill or install startup hooks. The current build has explicit user authorization to use Superpowers; future work requires its own applicable user request.
- Do not execute bundled scripts, enable telemetry, create worktrees or spawn subagents merely because a skill collection is installed. Review scripts before execution and stay within task authorization.
- Preserve the original reference repository. Do not copy code or assets without checking their license and recording attribution where required.
- Do not provision paid infrastructure, change DNS or publish a deployment without the user's explicit request.
