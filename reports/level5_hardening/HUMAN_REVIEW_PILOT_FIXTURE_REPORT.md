# Human-review pilot fixture report

Status: passed at fixture scope. Scientific state: `HUMAN_VALIDATION_REQUIRED`.

The durable application service created an administrator, two reviewers and an
adjudicator. Both reviewers and the adjudicator completed consent, direct-human
attestation and no-proxy/no-AI qualification. The administrator assigned one
fixture item independently to both reviewers. Two immutable judgments created
a deliberate disagreement; the adjudicator resolved it; the administrator
requested an amendment; and the first reviewer appended a superseding
judgment.

The public export contains two current fixture judgments, zero genuine
judgments and no identity fields. Dashboard coverage is two assigned/two
submitted. Backup/restore reproduced the same public count. Concurrent
idempotency, conflicts, draft autosave, session expiry, token hashing, CSRF,
RBAC and logout revocation were tested.

The actual HTTP service was started on loopback and exercised for health,
security headers, local identity login, session-cookie rotation, qualification,
CSRF enforcement, unauthorised export and 404 behavior. Domain workflow
provisioning and amendment administration used the same durable application
service directly; no production identity provider was asserted.

Canonical C10 status remains `HUMAN_VALIDATION_REQUIRED`; fixture rows cannot
satisfy it.
