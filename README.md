# kubecrate-tennant-1

Minimal public Flux consumer root for Bedrock tenant `tennant-1`.

This repository intentionally contains only the minimum consumer contract needed for Bedrock to bootstrap Flux against the public Kubecrate Vanilla composition pinned to immutable release `v0.4.0`.

Repository root:

- `clusters/tennant-1/entrypoint`

Consumer source coordinates for Bedrock:

- repository: `https://github.com/42aei/kubecrate-tennant-1.git`
- branch: `main`
- path: `./clusters/tennant-1/entrypoint`

Kubecrate source coordinates consumed by this repository:

- repository: `https://github.com/42aei/kubecrate.git`
- source name: `flux-system-sync`
- tag: `v0.4.0`
- path: `./compositions/vanilla/entrypoint`

Static validation:

```sh
python3 scripts/validate-consumer.py .
kubectl kustomize clusters/tennant-1/entrypoint
```

This repository excludes workloads, External Secrets configuration, Doppler, OpenBao, NetBird credentials, and other tenant-specific secrets or private services.
