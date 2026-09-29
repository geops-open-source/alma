# Demo files

The `keywind.jar` and `initial.json` files are included in this folder for the
initial setup of the demo instance.

## Keywind

The `keywind.jar` contained in this folder is the result of running the build steps at

    https://github.com/lukin/keywind/tree/bdf966fdae0071ccd46dab4efdc38458a643b409

Note that `keywind` is distributed under the Apache License 2.0 license. See the
link above for more information.

## initial.json

This sets up keycloak for local user accounts with a preset demo user `test@alma-os.ch`
with password `demo2024`. Mount a different initialization file to `/opt/keycloak/data/import/initial.json`
before starting the keycloak container to use a different initial setup.

An empty file can be used to start from stratch.

To reproduce the file:

  0. `cd` to the root of the repository
  1. rebuild all containers from scratch: `make stop-services && make start-services`
  2. make changes using the keycloak admin interface
  3. `docker compose run --rm -it --entrypoint="" keycloak /bin/bash`
     1. `cd /opt/keycloak/bin`
     2. `./kc.sh export --realm alma --file /tmp/initial.json`
     3. LEAVE THE CONTAINER OPEN, `docker ps` to get the container id
  4. `docker cp <container-id>:/tmp/initial.json docker/keycloak/initial.json`


## password_blocklist.txt

This file contains a list of passwords that are not allowed to be used.

It is based on a list from [SecLists](https://github.com/danielmiessler/SecLists/)
filterd to only include passwords that would otherwise pass our password policy.

The file is under MIT license. See the link above for more information.

To reproduce the file:

    pws = []
    with open("/path/to/list.txt") as f:
        for line in f:
            pw = line[:-1].lower()
            if len(line) >= 12 and not pw.isalnum():
                if re.match(r'[a-z]+[0-9]+|[0-9]+[a-z]+', pw):
                    pws.append(f"{pw}\n")
    with open("docker/keycloak/password_blocklist.txt", "w") as f:
        f.writelines(pws)
