SHELL := /bin/bash

container := back

restarthard: restartdocker stopall updb up

ps:
	sudo docker ps

up:
	sudo docker compose up backend -d

restart:
	sudo docker compose restart backend

down:
	sudo docker compose down backend

stop:
	sudo docker compose stop backend

updb:
	sudo docker compose up db pgadmin redis redis-commander -d

stopdb:
	sudo docker compose stop db pgadmin redis redis-commander

stopall:
	sudo docker stop $$(sudo docker ps -q)

restartdocker:
	sudo systemctl restart docker

exec:
	sudo docker exec -it $(container) bash

logs:
	sudo docker logs --tail 100 -f $(container)

migrate:
	sudo docker exec $(container) alembic upgrade head
