.PHONY: up seed test check
up:
	docker compose up --build
seed:
	cd backend && python -m app.seed
test:
	cd backend && pytest && cd ../frontend && npm test
check:
	cd frontend && npm run lint && npm run typecheck && npm run build
