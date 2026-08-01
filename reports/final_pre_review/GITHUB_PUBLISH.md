# GitHub Publish

Direct-to-`main` publication is required by the governing prompt. The report
generation baseline is `7656a94539720fb4afe841c7b8738c62d0ebadcd`. No branch, pull request, or force
push is used. After final validation, the implementation/report commits are
pushed to `origin/main`, the local and remote SHA are compared, and bounded CI
is observed. A Pages deployment setting failure is recorded separately and
does not override passing scientific documentation checks.
