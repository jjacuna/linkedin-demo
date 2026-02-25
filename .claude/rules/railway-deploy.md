# Railway Deployment & DevOps

## Pre-Deploy Checklist
- [ ] Dockerfile or nixpacks config included and tested
- [ ] All env vars documented in `.env.example`
- [ ] Health check endpoint exists (`/health` or `/api/health`)
- [ ] Database migrations run on startup or via deploy hook
- [ ] Build and start commands defined
- [ ] Logs output to stdout (Railway captures automatically)
- [ ] No hardcoded `localhost` — use `process.env.RAILWAY_PUBLIC_DOMAIN`
- [ ] Static assets cached with proper headers

## Environment Management
- **Production**: `main` branch → auto-deploys to Railway production
- **Staging**: `staging` branch → deploys to Railway staging environment
- Never test on production. Always verify on staging first.
- Keep env vars synced between environments via `.env.example`

## Monitoring & Observability (Post-Deploy)
- Error monitoring: Sentry or LogRocket (recommend setup in every project)
- Uptime monitoring: UptimeRobot or Better Uptime for public-facing apps
- Log analysis: Railway logs dashboard for debugging
- Set up alerts for: 500 errors, high response times, service downtime

## Rollback Protocol
If a deploy breaks production:
1. **Immediate**: Use Railway's "Rollback" button to previous deploy
2. **Investigate**: Check Railway logs for the failure
3. **Fix**: Create `hotfix/` branch, fix, test on staging
4. **Redeploy**: Merge hotfix to main only after staging verification

## Database Management
- Use migrations (Prisma, Drizzle, Knex) — never raw schema edits
- Seed data scripts for local development
- Backup strategy: automated daily backups for production databases
- Schema versioning: every migration is tracked in version control
- Test migrations on staging before running on production

## API Documentation
- Auto-generate API docs with Swagger/OpenAPI for every backend
- Document all endpoints: method, path, params, request/response body
- Include auth requirements and error codes
- Keep docs updated with every API change

## Cost Awareness
- Flag when architecture choices increase Railway resource usage
- Prefer serverless/edge functions for low-traffic endpoints
- Optimize database queries to reduce compute time
- Use caching (Redis, CDN) to reduce repeated expensive operations
- Alert user if estimated monthly cost exceeds $50 for a single service

## Continuous Updates
When updating shipped code:
```
📝 CHANGELOG v[#]
- [Added/Changed/Fixed]: [description]
- Impact: [None/Low/Medium — what else is affected]
- Migration: [Steps needed to update]
- Rollback: [How to revert if needed]
```
