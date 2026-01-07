test::
	docker compose --ansi never up --force-recreate --abort-on-container-exit --no-color
	docker compose logs test
down::
	docker compose down
ps::
	docker compose ps

bash sh::
	docker compose --file docker-compose.yml --file docker-compose.bash.yml up --force-recreate --detach
	docker compose exec test bash
