
docker_stop_all() {
  docker stop $(docker ps -q)
}

docker_kill_all() {
  docker kill $(docker ps -q)
}

docker_cleanup() {
  # Prune images and containers that were created more than 5 days ago.
  docker system prune -a --filter "until=120h"
}
