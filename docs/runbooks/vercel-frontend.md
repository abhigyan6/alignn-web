# Vercel frontend configuration

Deploy the Next.js app from the monorepo with the project root set to `apps/web` and access to workspace packages outside that directory. The coming-soon homepage remains available without a backend.

For application pages, set `API_ORIGIN` to the reachable FastAPI HTTPS origin without a path, credentials or trailing query. Set it for the build and runtime environments and redeploy after changing it. Both browser rewrites and server profile checks use this origin. A stopped EC2 backend cannot answer Vercel requests. Missing `API_ORIGIN` on Vercel disables the rewrite and account profile requests fail with a recoverable page error.

Configure the production Clerk instance for the public frontend hostname. Set its publishable and secret keys through Vercel environment settings. Set `PUBLIC_ORIGIN` to the exact frontend HTTPS origin in both the frontend and FastAPI. The backend checks that origin for mutations and Clerk token authorized parties. Avoid routing `API_ORIGIN` back to the frontend itself.

The backend, worker and scheduler still require PostgreSQL and their configured services. Frontend deployment does not deploy them. Defaults allow three pooled connections and two overflow connections per backend process. Include all processes and migrations when budgeting database connections.

Before publishing application routes, verify a new account completes onboarding, a returning account opens its workspace, profile editing works, and private resume uploads finish scanning. Signed-out route tests cannot establish those outcomes.
