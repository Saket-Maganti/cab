# Power and inference calibration

Status: `CAB_POWER_PLAN_CALIBRATED`.

- Replicates: 4000 in 8 persisted deterministic shards
- Null Type-I error per model: `[0.05225, 0.0455, 0.04675, 0.048, 0.05025]`
- Null CI coverage per model: `[0.94775, 0.9545, 0.95325, 0.952, 0.94975]`
- Alternative power per model: `[0.934, 0.9255, 0.928, 0.9255, 0.9255]`
- Minimum/median per-model power: 0.9255 / 0.9255
- All-model familywise pass probability: 0.68175
- Family/interaction power: 0.989 / 0.6725
- Interaction null Type-I error: 0.052
- Bias: `[0.001208, -0.00074, -0.000618, 0.000465, 0.000573]`; RMSE: `[0.043863, 0.043624, 0.043728, 0.045255, 0.044342]`
- Type-I Monte Carlo SE: `[0.003519, 0.003295, 0.003338, 0.00338, 0.003454]`
- Actual paired Wald/ANOVA/confidence-bound estimators run in every replicate; heuristic SD detection is prohibited
