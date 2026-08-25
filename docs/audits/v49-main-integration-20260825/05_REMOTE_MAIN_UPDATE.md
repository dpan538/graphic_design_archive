# Remote main update

Authorized command: `git push origin HEAD:refs/heads/main` after a fresh fetch proves `origin/main == 592c765d0af5bf15b1666784dce784ac8e22624d`, merge base `592c765d0af5bf15b1666784dce784ac8e22624d`, and `HEAD..origin/main == 0`.

The update must be a non-force fast-forward. `--force` and `--force-with-lease` are prohibited. The exact containing integration SHA and remote equality are recorded by `refs/heads/main`, the post-integration annotated tag, and the final external receipt; a commit cannot contain its own object ID or a receipt of its later push.
