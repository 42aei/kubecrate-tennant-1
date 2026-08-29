# Bootstrap notes

This consumer repository is a public Flux root for Bedrock tenant `tennant-1`.

Use it as the Flux bootstrap path:

```text
clusters/tennant-1/entrypoint
```

The entrypoint defines exactly three hand-maintained resources:

- `Namespace/kubecrate-system`
- `GitRepository/flux-system-sync` for `https://github.com/42aei/kubecrate.git` pinned to `v0.4.0`
- `Kustomization/kubecrate-vanilla` for `./compositions/vanilla/entrypoint`

Why `flux-system-sync`:

- Kubecrate `v0.4.0` release notes and `docs/consumer-repositories.md` require the consumer's Kubecrate source to be named `flux-system-sync`.
- The nested Flux `Kustomization` objects inside `compositions/vanilla/entrypoint` also use `sourceRef.name: flux-system-sync`.

This repository intentionally does not carry private application services, deploy keys, generated Flux bootstrap secrets, or secret-manager integrations.

Validate before changing the pinned tag or path:

```sh
python3 scripts/validate-consumer.py .
kubectl kustomize clusters/tennant-1/entrypoint >/dev/null
```
