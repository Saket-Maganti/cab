# GitHub publication model

Work is published directly to `main` without force push. An exact-HEAD receipt cannot truthfully
include itself in the commit it attests, so reproducible artifact hashes and final source SHA are
stored in an external receipt after the immutable final commit. Local/remote SHA equality and CI
must be verified before completion is claimed.
