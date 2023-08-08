
docker_stop_all() {
  docker stop $(docker ps -q)
}

docker_kill_all() {
  docker kill $(docker ps -q)
}
