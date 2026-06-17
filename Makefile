.PHONY: backend frontend dev test

backend:
	cd backend && uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

dev:
	@echo "Run backend and frontend in separate terminals:"
	@echo "  make backend"
	@echo "  make frontend"

test:
	pytest backend/tests
