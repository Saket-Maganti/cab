# CAB final integrity closure — baseline repository state

Recorded at `2026-08-05T04:30:55.835544+00:00`.

This is the authoritative pre-repair snapshot.  Every scientific-kernel
surface listed below is compared again after the repair; drift is a
failure, not a result.

## Repository

| field | value |
| --- | --- |
| branch | `main` |
| HEAD | `131cd10abe519a7174171bb47e90347326862ca4` |
| starting commit | `131cd10abe519a7174171bb47e90347326862ca4` |
| starting commit is ancestor or HEAD | True |
| origin | `https://github.com/Saket-Maganti/cab.git` |
| origin/main | `131cd10abe519a7174171bb47e90347326862ca4` |
| ahead/behind (HEAD...origin/main) | `0	0` |
| dirty files | 0 |
| untracked files | 2 |
| Python | `3.11.9` |

## Active schema surface

| field | value |
| --- | --- |
| packet version | `compact20-review-ready-v2` |
| workflow schema | `cab_review_ready_v2_two_stage_workflow_v2` |
| qualification schema | `cab_qualification_v4` |
| review form schema | `cab_stage1_review_form_v2` |
| production receipt schema | `cab_review_ready_v2_production_receipt_v1` |
| fixture receipt schema | `cab_review_ready_v2_fixture_receipt_v1` |
| scientific freeze | `6a7b15b21d4a899e7cb95bf110625c5f72fc33899da20dfa93f9ce9c6b023fad` |
| public packet commitment | `03653ff304126cd460fc8ee51a371e6741f4b2fb294b44632145aa687f48745b` |

## Scientific kernel preservation baseline

| surface | digest |
| --- | --- |
| `packet_version` | `c1c971b49d3ddcb105eaf5e966961a65b91b16e3067b5963fa69381a24c8bb37` |
| `pair_count` | `f5ca38f748a1d6eaf726b8a42fb575c3c71f1864a8143301782de13da2d9202b` |
| `active_pair_content_digest` | `3b157dbcc14702c7df1a2c5e12ea5f7db6d5ccee69d1ff0bba1cd8f886f320ba` |
| `pair_content_hashes` | `01a2ed72c58d052cc36e64907b3ac5f2b19de5f314ad63915c4d975c51d6973d` |
| `stage1_package_hashes` | `98118cdd1b49ef878ecc6928c4b1eb73db0c449d18c594b8417a3c412a826dc9` |
| `stage1_reviewer_a_archive_sha256` | `c0edc9ea796938407dee2b478606405a2e9955c2fbd00f781f07d448ace051fe` |
| `stage1_reviewer_b_archive_sha256` | `578e4333d06f2147afc6b0ec8f98bcd3893f88a38059e0f3a63b06f649993623` |
| `qualification_version` | `68809b11608607a6273b187896b684383303d9dac0fb0866d432f66edc134bab` |
| `qualification_package_hashes` | `3b357fc263424c391000696eb9e564a762a2da1130f2bbe0bacf5f6c86148269` |
| `qualification_commitment_sha256` | `a304c98bb557113ab348c2d36d299d2bdbfe094bd7bf25c4722563c27f5c6fa3` |
| `qualification_commitment` | `351caa1d7529a2de124ab567553ddd3d2a09de3110933c47873537f959987f82` |
| `encrypted_qualification_vault_sha256` | `f51beb0f6190d5c887ec2dbea68f12a8bbd4b81a7e5549ea9ca224ee8d05b51c` |
| `stage2_encrypted_vault_sha256` | `359743c81755b016d186d96ffc3f4c724f0875fb80ce722103db2d501e3482f5` |
| `stage2_vault_file_sha256` | `359743c81755b016d186d96ffc3f4c724f0875fb80ce722103db2d501e3482f5` |
| `public_packet_commitment_sha256` | `81aebf785e8c28b55eba7de02758acfb0277fde9ef17a140394c6c7ba0661a51` |
| `seed_commitment` | `b318b03512da03ea8c26d8d8573a93e2c3438354ed67e9db3f77f3514a694fea` |
| `distinct_semantic_objectives` | `b17ef6d19c7a5b1ee83b907c595526dcb1eb06db8227d650d5dda0a9f4ce8cd9` |
| `family_counts` | `a09ad46ac2ea57e828a986c3a9247cef164ab02edf06b19fc5b6c0853398a109` |
| `domain_counts` | `fb6bf2a934700ce440062353c771b0cf85c658015a8359c5e098e7faad37d2b1` |
| `difficulty_counts` | `5bc204c97106fae57cd27f4735e89d008d82e31d0efb2328bee46f743191b684` |

## Private material

- private packet files present on disk: 20
- private files tracked in Git: 0 (expected: 0)

No private body, key, answer or reviewer identity appears in this report.
