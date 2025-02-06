#!/bin/bash

set -e

last_workflow_name() {
  last_wf_info="$(command osmo workflow list --count=1 --format-type=json)"
  last_wf_name="$(echo "${last_wf_info}" | jq -r '.workflows[0].name')"
  echo "${last_wf_name}"
}

select_workflow_name() {
  set -e
  wf_infos=$(command osmo workflow list --format-type=json)
  IFS=$'\n' options=($(echo "${wf_infos}" | jq -r '.workflows[] | [.status, .user, .name, .submit_time] | @tsv' | tac | column -t))
  selected_option=$(interactive_select.sh ${options[@]})
  selected_wf_name=$(echo ${selected_option} | awk '{print $3}')
  echo "${selected_wf_name}"
}


args=()
for arg in "$@"; do
  if [[ "$arg" == "wf" ]]; then
    args+=("workflow")
  elif [[ "$arg" == "ds" ]]; then
    args+=("dataset")
  elif [[ "$arg" == "pf" ]]; then
    args+=("port-forward")
  elif [[ "$arg" == "ls" ]]; then
    args+=("list")
  elif [[ "$arg" == "q" ]]; then
    args+=("query")
  elif [[ "$arg" == "json" ]]; then
    args+=("--format-type=json")
  elif [[ "$arg" == "last" ]]; then
    args+=("$(last_workflow_name)")
  elif [[ "$arg" == "select" ]]; then
    args+=("$(select_workflow_name)")
  else
    args+=("${arg}")
  fi
done

echo "Running command 'osmo ${args[@]}'."
command osmo "${args[@]}"
