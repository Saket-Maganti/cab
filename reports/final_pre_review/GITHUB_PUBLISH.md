# GitHub Publish

Direct-to-`main` publication is required by the governing prompt. The report
generation baseline is `82150dea538080c213cba548aee9c62d78315fbd`. No branch, pull request, or force
push is used. After final validation, the implementation/report commits are
pushed to `origin/main`, the local and remote SHA are compared, and bounded CI
is observed. A Pages deployment setting failure is recorded separately and
does not override passing scientific documentation checks.
