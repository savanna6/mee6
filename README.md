# Mee6

The essence of mee6 with a lot of utility classes and functions. Plugins are
also defined here. Two sort of plugin exists: standalone and "not-standalone"
ones 🙃 .

You can launch the standalone ones with the cli `python3 mee6.cli Reddit` for
example.

## Configuration

The configuration is implicit and lives in your environment variables. You can
find a list of the configuration variables in `config.example`.

## Discord Ratelimiter

If a `RATELIMIT_REDIS_URL` config variable is found, the ratelimiter will
"live" in Redis. So launching multiple workers and standalone plugins will be
totally safe in terms of respecting the discord rate limits 👌 .

## Disclaimer

This is a **WIP**. We should add a worker that'll be connected to mee6's shards
through a broker (We use Redis for now). And complete the discord APIClient.
