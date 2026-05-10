# Error Analysis Guide

## Recommended Review Fields

- Did the agent call the required tools?
- Were arguments valid and task-specific?
- Did the agent rely on corrupted memory or corrupted observations?
- Did the agent notice conflicts?
- Did it recover after tool errors?
- Did it stop too early?
- Was the final answer supported by the trajectory?

## Annotation Notes

Use trajectory JSONL as the primary evidence. Do not infer agent intent from final answer alone.

## TODO

Create a human annotation form and inter-annotator agreement protocol.
