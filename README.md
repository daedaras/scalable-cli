# scalable-cli

## How to Build and Run with Podman

1. Build the container image & login:

    ```Bash
    podman build -t scalable-cli:latest .
    podman volume create scalable-config
    podman run --rm -it -e DISPLAY= -e DBUS_SESSION_BUS_ADDRESS= -v scalable-config:/root/.config/scalable-cli scalable-cli:latest login
    ```

1. Verification: To check if the build and wrapper are working correctly, run the following to see the installed version of `sc`:

    ```Bash
    podman run --rm scalable-cli:latest --version
    ```

## Python script usage (get overview with distributions)

```Bash
python .\scalable_report.py
```

## scalable-cli usage example

```Bash
# 1. Export all holdings with a larger page size
podman run --rm -v scalable-config:/root/.config/scalable-cli scalable-cli:latest broker holdings --json > positions.json

# 2. Export all transactions with a larger page size so history isn't cut off
podman run --rm -v scalable-config:/root/.config/scalable-cli scalable-cli:latest broker transactions --page-size 100 --json > transactions.json

# 3. Export broker overview (contains performance by timeframe like YTD, ONE_YEAR, MAX)
podman run --rm -v scalable-config:/root/.config/scalable-cli scalable-cli:latest broker overview --json > overview.json
```
