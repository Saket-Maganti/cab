# Paper TODO / placeholder inventory

Generated: 2026-05-20T08:27:04.501242+00:00

## Summary

- Total items: 72
- By severity: {'cleanup': 45, 'blocker_before_empirical_claims': 22, 'optional': 5}

## ablations

- [cleanup] **planned** @ `paper/latexpaper/sections/09_ablations.tex:3` — No ablation result is claimed in this draft. The repository defines a factorial ablation matrix (\texttt{ablation-matrix}, \texttt{configs/ablation\_matrix\_local\_stub.yaml}) and per-factor configs u
- [blocker_before_empirical_claims] **not yet run** @ `paper/latexpaper/sections/09_ablations.tex:5` — \paragraph{Planned ablations (not yet run).}
- [cleanup] **planned** @ `paper/latexpaper/sections/09_ablations.tex:5` — \paragraph{Planned ablations (not yet run).}
- [blocker_before_empirical_claims] **missing_ablations** @ `paper/latexpaper/sections/09_ablations.tex:5` — \paragraph{Planned ablations (not yet run).}

## benchmark design

- [cleanup] **planned** @ `paper/latexpaper/sections/03_benchmark_design.tex:6` — The planned benchmark spans travel planning, calendar/email workflow, file and spreadsheet question answering, shopping/comparison, research assistant tasks, policy/compliance tasks, coding/debugging 
- [optional] **table_figure_reference** @ `paper/latexpaper/sections/03_benchmark_design.tex:6` — The planned benchmark spans travel planning, calendar/email workflow, file and spreadsheet question answering, shopping/comparison, research assistant tasks, policy/compliance tasks, coding/debugging 
- [cleanup] **TODO** @ `paper/latexpaper/sections/03_benchmark_design.tex:15` — To probe transfer without abandoning control, we added a 40-task mini-study that compares template-generated synthetic tasks with naturalistic synthetic tasks built from mock emails, calendars, spread
- [optional] **table_figure_reference** @ `paper/latexpaper/sections/03_benchmark_design.tex:15` — To probe transfer without abandoning control, we added a 40-task mini-study that compares template-generated synthetic tasks with naturalistic synthetic tasks built from mock emails, calendars, spread
- [blocker_before_empirical_claims] **placeholder** @ `paper/latexpaper/sections/03_benchmark_design.tex:36` — \caption{Mini-study comparison of intervention-family degradation between template-generated and naturalistic synthetic tasks. Placeholder until paired validated runs are exported.}
- [cleanup] **TODO** @ `paper/latexpaper/sections/03_benchmark_design.tex:42` — \texttt{[todo]} & \texttt{[todo]} & \texttt{[todo]} & \texttt{[todo]} \\

## ethics/reproducibility

- [blocker_before_empirical_claims] **placeholder** @ `paper/latexpaper/sections/11_ethics_reproducibility.tex:12` — \paragraph{Compensation placeholder.}
- [cleanup] **planned** @ `paper/latexpaper/sections/11_ethics_reproducibility.tex:16` — Every reported result should include task version, run config, random seed, model/API version, timestamp, scorer version, and artifact path. Current reproducibility conventions are documented in \text

## experiments

- [cleanup] **TODO** @ `paper/latexpaper/main.tex:18` — \newcommand{\todo}[1]{\textcolor{red}{[TODO: #1]}}
- [cleanup] **planned** @ `paper/latexpaper/sections/06_experiments.tex:3` — The planned main experiments use generated benchmark directories, deterministic seeds, fixed agent lists, and saved run metadata. Every run directory records the config, config hash, Python version, p
- [blocker_before_empirical_claims] **placeholder** @ `paper/latexpaper/sections/06_experiments.tex:6` — Before execution, configs are validated (\texttt{validate-config}, \texttt{plan-run}, \texttt{dry-run}) and checked against evidence-level policy (\texttt{docs/EVIDENCE\_LEVEL\_POLICY.md}). During exe
- [cleanup] **planned** @ `paper/latexpaper/sections/06_experiments.tex:12` — The repository currently supports smoke, development, pilot, and planned main benchmark configurations. Pilot data generation is intended for pipeline validation and early failure analysis. A submissi

## generated files

- [cleanup] **planned** @ `paper/latexpaper/generated/00_abstract.tex:1` — Tool-using language agents are increasingly evaluated by final task success, but such scores conflate planning, tool selection, memory use, observation interpretation, recovery, and stopping behavior.
- [blocker_before_empirical_claims] **placeholder** @ `paper/latexpaper/generated/01_introduction_snippet.tex:2` — We reserve empirical findings for runs over configured non-oracle agents; the planned main finding remains [main finding placeholder].
- [cleanup] **planned** @ `paper/latexpaper/generated/01_introduction_snippet.tex:2` — We reserve empirical findings for runs over configured non-oracle agents; the planned main finding remains [main finding placeholder].
- [blocker_before_empirical_claims] **placeholder** @ `paper/latexpaper/generated/03_benchmark_stats_table.tex:3` — \caption{Benchmark statistics. Placeholder until \texttt{fill-paper-from-run} links a verified run.}
- [blocker_before_empirical_claims] **placeholder** @ `paper/latexpaper/generated/07_results.tex:3` — This section is a structured placeholder. \textbf{No final scientific results are claimed in this draft.} Results will be inserted only after completed non-oracle LLM runs, human validation where requ
- [cleanup] **planned** @ `paper/latexpaper/generated/07_results.tex:6` — \textbf{Planned test.} Compare clean success, intervention success, absolute degradation, relative degradation, and \acrs across agents. This tests \claimref{C1}.
- [cleanup] **TODO** @ `paper/latexpaper/generated/07_results.tex:8` — \textbf{TODO.} Run \texttt{fill-paper-from-run} after a verified non-stub pilot and link Table~\ref{tab:main-performance}.
- [optional] **table_figure_reference** @ `paper/latexpaper/generated/07_results.tex:8` — \textbf{TODO.} Run \texttt{fill-paper-from-run} after a verified non-stub pilot and link Table~\ref{tab:main-performance}.
- [cleanup] **TODO** @ `paper/latexpaper/generated/07_results.tex:11` — \textbf{TODO.} Insert Figure~\ref{fig:family-breakdown} from the final run.
- [optional] **table_figure_reference** @ `paper/latexpaper/generated/07_results.tex:11` — \textbf{TODO.} Insert Figure~\ref{fig:family-breakdown} from the final run.
- [cleanup] **TODO** @ `paper/latexpaper/generated/07_results.tex:14` — \textbf{TODO.} Insert Figure~\ref{fig:ranking-instability} after main experiments.
- [optional] **table_figure_reference** @ `paper/latexpaper/generated/07_results.tex:14` — \textbf{TODO.} Insert Figure~\ref{fig:ranking-instability} after main experiments.
- [cleanup] **TODO** @ `paper/latexpaper/generated/07_results.tex:17` — \textbf{TODO.} Insert trajectory disagreement figure and audited examples.
- [blocker_before_empirical_claims] **placeholder** @ `paper/latexpaper/generated/08_human_validation.tex:1` — Human validation is not yet complete for paper claims. Table~5 remains a placeholder until annotations and adjudication are finished (\claimref{C3}, \claimref{C10}).
- [blocker_before_empirical_claims] **missing_human_validation** @ `paper/latexpaper/generated/08_human_validation.tex:1` — Human validation is not yet complete for paper claims. Table~5 remains a placeholder until annotations and adjudication are finished (\claimref{C3}, \claimref{C10}).
- [cleanup] **planned** @ `paper/latexpaper/generated/claim_evidence_matrix.tex:3` — \item \textbf{C1}: status=planned; eligible artifacts=0.
- [cleanup] **planned** @ `paper/latexpaper/generated/claim_evidence_matrix.tex:4` — \item \textbf{C2}: status=planned; eligible artifacts=0.
- [cleanup] **planned** @ `paper/latexpaper/generated/claim_evidence_matrix.tex:5` — \item \textbf{C3}: status=planned; eligible artifacts=0.
- [cleanup] **planned** @ `paper/latexpaper/generated/claim_evidence_matrix.tex:6` — \item \textbf{C4}: status=planned; eligible artifacts=0.
- [cleanup] **planned** @ `paper/latexpaper/generated/claim_evidence_matrix.tex:7` — \item \textbf{C5}: status=planned; eligible artifacts=0.
- [cleanup] **planned** @ `paper/latexpaper/generated/claim_evidence_matrix.tex:8` — \item \textbf{C6}: status=planned; eligible artifacts=0.
- [cleanup] **planned** @ `paper/latexpaper/generated/claim_evidence_matrix.tex:9` — \item \textbf{C7}: status=planned; eligible artifacts=0.
- [cleanup] **planned** @ `paper/latexpaper/generated/claim_evidence_matrix.tex:10` — \item \textbf{C8}: status=planned; eligible artifacts=0.
- [cleanup] **planned** @ `paper/latexpaper/generated/claim_evidence_matrix.tex:12` — \item \textbf{C10}: status=planned; eligible artifacts=0.

## human validation

- [blocker_before_empirical_claims] **blocked** @ `paper/latexpaper/sections/08_human_validation.tex:6` — Human validation exports and protocols exist; completed annotations and agreement statistics do not. Table~5 and intervention-validity claims (\claimref{C3}, \claimref{C10}) remain blocked until a str

## introduction

- [cleanup] **planned** @ `paper/latexpaper/sections/01_introduction.tex:9` — The benchmark reports final-answer scores together with trajectory diagnostics for tool use, recovery, contradiction handling, memory verification, stopping behavior, and trajectory faithfulness. Agen
- [blocker_before_empirical_claims] **placeholder** @ `paper/latexpaper/sections/01_introduction.tex:21` — The open-source package now includes run planning and status monitoring, resume and interruption handling, deterministic mock diagnostic agents for detector validation, paper-asset export with enginee

## limitations

- [blocker_before_empirical_claims] **missing_human_validation** @ `paper/latexpaper/sections/10_limitations.tex:25` — Human validation can improve label quality but introduces annotator subjectivity, sampling limits, and compensation obligations. Agreement statistics should be reported with the same caution as model 
- [blocker_before_empirical_claims] **missing_ablations** @ `paper/latexpaper/sections/10_limitations.tex:34` — Bracketed results, ranking analyses, and ablation tables remain placeholders until \texttt{fill-paper-from-run} links verified non-oracle LLM runs. Deterministic stub and smoke runs validate engineeri

## metrics

- [cleanup] **planned** @ `paper/latexpaper/sections/05_metrics.tex:23` — To test \claimref{C4}, agents are ranked by clean success and by \acrs. The analysis reports rank deltas and Spearman correlation between rankings. A low correlation would indicate that clean success 

## related work

- [cleanup] **planned** @ `paper/latexpaper/sections/02_related_work.tex:26` — ReAct and AgentBoard (above) further motivate logging multi-step behavior; \CAB{} uses the same motivation but ties trajectory metrics to survival under named interventions, as planned in \claimref{C3

## results

- [cleanup] **planned** @ `paper/latexpaper/sections/07_results.tex:4` — \textbf{Planned test.} Compare baseline agents or LLM prompts with and without self-checking, planning scaffolds, tool-verification instructions, and recovery prompts. This tests \claimref{C6}.

## unknown

- [blocker_before_empirical_claims] **placeholder** @ `paper/latexpaper/sections/checklist.tex:4` — \item \textbf{Claims.} Scientific claims are tracked in \texttt{docs/CLAIM\_LEDGER.md} and \texttt{docs/claim\_ledger.json}. Unsupported claims remain planned, engineering-only, or placeholder. C1--C8
- [cleanup] **planned** @ `paper/latexpaper/sections/checklist.tex:4` — \item \textbf{Claims.} Scientific claims are tracked in \texttt{docs/CLAIM\_LEDGER.md} and \texttt{docs/claim\_ledger.json}. Unsupported claims remain planned, engineering-only, or placeholder. C1--C8
- [blocker_before_empirical_claims] **missing_human_validation** @ `paper/latexpaper/sections/checklist.tex:8` — \item \textbf{Human validation.} Export protocol and forms exist; annotations \textbf{not complete}. Required before strong claims about label quality, intervention validity, or trajectory-diagnostic 
- [blocker_before_empirical_claims] **placeholder** @ `paper/PAPER_STATUS.md:18` — - **Results:** Stronger placeholder status note
- [cleanup] **planned** @ `paper/PAPER_STATUS.md:20` — - **Ablations:** Planned matrix content (was empty)
- [blocker_before_empirical_claims] **placeholder** @ `paper/PAPER_STATUS.md:27` — ## What remains placeholder
- [cleanup] **TODO** @ `paper/PAPER_STATUS.md:33` — - Mini-study comparison table `[todo]` rows
- [cleanup] **planned** @ `paper/PAPER_STATUS.md:37` — - C1–C8, C10: **planned**
- [blocker_before_empirical_claims] **blocked** @ `paper/PAPER_STATUS.md:42` — | Section | Ready for draft? | Blocked for submission? |
- [blocker_before_empirical_claims] **placeholder** @ `paper/PAPER_STATUS.md:51` — | Results | Placeholder only | **Yes** |
- [cleanup] **planned** @ `paper/PAPER_STATUS.md:53` — | Ablations | Planned only | **Yes** |
- [cleanup] **planned** @ `paper/EVIDENCE_GAP_MAP.md:3` — **Source of truth** for what evidence exists vs what is required. All claims C1–C8, C10 are **planned** unless noted.
- [blocker_before_empirical_claims] **placeholder** @ `paper/EVIDENCE_GAP_MAP.md:13` — | **Current evidence** | Placeholder tables; stub/mock runs (engineering only) |
- [cleanup] **planned** @ `paper/EVIDENCE_GAP_MAP.md:14` — | **Status** | **planned** |
- [blocker_before_empirical_claims] **empirical_claim_without_eligible_evidence** @ `paper/EVIDENCE_GAP_MAP.md:22` — | **Forbidden wording now** | "Clean success overestimates…", "We show…", "significant gap" |
- [cleanup] **planned** @ `paper/EVIDENCE_GAP_MAP.md:32` — | **Status** | **planned** |
- [cleanup] **planned** @ `paper/EVIDENCE_GAP_MAP.md:48` — | **Status** | **planned** |
- [cleanup] **planned** @ `paper/EVIDENCE_GAP_MAP.md:63` — | **Status** | **planned** |
- [cleanup] **planned** @ `paper/EVIDENCE_GAP_MAP.md:76` — | **Status** | **planned** |
- [cleanup] **planned** @ `paper/EVIDENCE_GAP_MAP.md:88` — | **Status** | **planned** |
- [cleanup] **planned** @ `paper/EVIDENCE_GAP_MAP.md:98` — | **Status** | **planned** |
- [cleanup] **planned** @ `paper/EVIDENCE_GAP_MAP.md:108` — | **Status** | **planned** |
- [cleanup] **planned** @ `paper/EVIDENCE_GAP_MAP.md:128` — | **Status** | **planned** |
- [cleanup] **planned** @ `paper/EVIDENCE_GAP_MAP.md:131` — | **Allowed now** | "Interventions are **designed** to isolate…; audited automatically; human audit **planned**" |
