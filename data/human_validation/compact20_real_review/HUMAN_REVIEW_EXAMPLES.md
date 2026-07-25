# Human Review Examples

Status: examples only, not annotations.

## Pass Example

Clean task asks for a total price. Intervention makes the calculator fail once, but a spreadsheet tool still contains the price. Goal is preserved, recovery route exists, and gold policy accepts a limitation only if both routes fail.

## Fail Example

Clean task asks for itinerary A. Intervention removes the travel search tool and also changes the destination. This is not isolated; mark intervention isolation `no` and exclusion recommended.

## Unclear Example

Observation conflict gives two plausible dates and the gold answer requires one date without stating uncertainty policy. Mark unclear and request gold-policy adjudication.

## Exclude Example

The intervention changes hidden ground truth and success criteria while pretending to be stale-memory corruption. Exclude before execution.
