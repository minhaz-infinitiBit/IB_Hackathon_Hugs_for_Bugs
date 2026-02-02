build:
	clear
	docker compose build

start:
	clear
	docker compose up --scale celery=2 --remove-orphans

run: build start;

clear:
	docker compose down --remove-orphans
	clear
