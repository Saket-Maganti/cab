# Backend plugin contract

A backend declares its name, capabilities, resource limits and evidence class.
It must validate the immutable manifest in `prepare`, execute one identified
unit per attempt, support explicit cancellation and perform cleanup.

Backends must not substitute a model, revision, quantization, policy, scorer or
budget. Any mismatch creates an error or a new manifest identity. Network,
quota and checkpoint capabilities are discoverable rather than inferred.

Plugin metadata uses API version `1.0`; incompatible versions and duplicate
names fail before launch. Loading one broken plugin does not disable other
plugins.
