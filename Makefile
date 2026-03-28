.PHONY: check backend-check frontend-check

check: backend-check frontend-check

backend-check:
	cd backend && ruff check src/ tests/
	cd backend && ruff format --check src/ tests/
	cd backend && pytest

frontend-check:
	cd frontend && pnpm install --frozen-lockfile
	cd frontend && npx biome check src/
	cd frontend && npx tsc --noEmit
	cd frontend && pnpm test
