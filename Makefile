#!/bin/bash
# Makefile-like tasks for development

.PHONY: help setup dev logs stop build deploy

help:
	@echo "DateGen Development Tasks"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  setup       - Set up local environment with Docker"
	@echo "  dev         - Start development environment"
	@echo "  logs        - View Docker logs"
	@echo "  stop        - Stop all services"
	@echo "  build       - Build Docker images"
	@echo "  deploy      - Deploy to Railway"
	@echo "  clean       - Remove containers and volumes"

setup:
	@bash setup.sh

dev:
	@docker-compose up -d
	@echo "✅ Services started"
	@echo "Frontend: http://localhost:5173"
	@echo "Backend:  http://localhost:8000"

logs:
	@docker-compose logs -f

stop:
	@docker-compose stop
	@echo "✅ Services stopped"

build:
	@docker-compose build
	@echo "✅ Images built"

deploy:
	@echo "Deploying to Railway..."
	@railway deploy
	@echo "✅ Deployed"

clean:
	@docker-compose down -v
	@echo "✅ Cleaned up"
