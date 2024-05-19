### How to run

1. Populate the env.list

```shell
docker build -t washing-machine-alerter .
docker run -it \
  --name=washing-machine-alerter \
  --net=host \
  --env-file ./env.list \
  washing-machine-alerter
```