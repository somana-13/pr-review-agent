# pr-review-agent

A CLI tool that reviews a GitHub pull request using a multi-agent LangGraph
pipeline: specialist agents for security, test coverage, and style, real
tool-calling (Semgrep, ruff, the GitHub API), a LoRA-fine-tuned CodeBERT
classifier that gates the (expensive) security specialist, and AWS Bedrock
Guardrails on both the input diff and the output comment. Runs standalone
(`pr-review review <pr-url>`) or auto-triggered on this repo's own PRs via
GitHub Actions.

## Why this exists

Built to demonstrate three things directly, with real working code behind
each claim rather than a description of them:

- **A real generative LLM in the loop** — Claude models via AWS Bedrock
  (`langchain_aws.ChatBedrockConverse`), not an extractive pipeline.
- **Genuine multi-agent tool-calling** — specialists that decide, mid-review,
  to invoke a tool (Semgrep, ruff, a test-coverage heuristic) and reason over
  the result, via LangGraph's `create_react_agent` (bind_tools + ToolNode +
  tools_condition under the hood).
- **Real fine-tuning of a generative/code-aware transformer** — a LoRA
  adapter trained on top of `microsoft/codebert-base` (CodeSearchNet
  pretraining), not just an encoder classifier fine-tune.

## Architecture

```
guardrail_input_check (Bedrock ApplyGuardrail, masks secrets/PII in the diff)
  → classifier_gate (LoRA-CodeBERT, local CPU/MPS inference, no network)
  → planner_router (deterministic: threshold vs. classifier score)
  → clone_workspace (shallow git clone of the PR head, shared by specialists
    that need real files on disk, not just diff hunks)
  → [parallel fan-out via langgraph.types.Send — security_specialist only
     dispatched when the classifier says the diff is security-relevant]:
       security_specialist       (Semgrep, via a ReAct tool loop)
       test_coverage_specialist  (a diff-based heuristic tool, always runs)
       style_specialist          (ruff, always runs)
  → cleanup_workspace (join point; deletes the clone)
  → synthesizer (LLM merges all findings into one comment; deterministically
    appends the routing decision so the classifier's skip/run choice is
    always visible, regardless of what the LLM chose to summarize)
  → guardrail_output_check (masks secrets/PII in the final comment)
  → post_pr_comment
```

State flows through a `TypedDict` (`graph/state.py`). Every field more than
one node can write to a reducer (`Annotated[list[str], operator.add]`) —
required because LangGraph raises `InvalidUpdateError` on an unreduced key
written by more than one node in the same step, and also because two
*sequential* writes to the same key (e.g. the input and output guardrail
checks both logging to `guardrail_flags`) would otherwise silently overwrite
each other instead of accumulating.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # fill in the values below
```

Required in `.env`:

| Variable | Notes |
|---|---|
| `GITHUB_TOKEN` | Fine-grained PAT: `Pull requests: Read and write`, `Contents: Read-only` |
| `AWS_REGION` | `us-east-1` |
| `BEDROCK_MODEL_ID` | See "Bedrock gotchas" below — not the bare model ID |
| `GUARDRAIL_ID` / `GUARDRAIL_VERSION` | From a Bedrock Guardrail you create (see below) |
| `CLASSIFIER_ADAPTER_PATH` | A local path, or a HF Hub repo id (e.g. `somana13/pr-review-agent-classifier`) |
| `HF_TOKEN` | Only needed to run `finetune/export.py`; optional otherwise |

### Bedrock gotchas discovered while building this

- Some models (including the Claude Haiku used here) can't be invoked by
  their bare model ID on Bedrock — you get
  `ValidationException: ... isn't supported ... use an inference profile`.
  Use the region-prefixed inference profile ID instead
  (`us.anthropic.claude-haiku-4-5-20251001-v1:0`), found via
  `aws bedrock list-inference-profiles`.
- The old Bedrock "Model access" console page is retired — models
  auto-enable on first invoke now — but Anthropic models still require a
  one-time "use case details" form, submitted per-model via
  **Bedrock Console → Model catalog → (the model) → Playground**. The error
  (`ResourceNotFoundException: Model use case details have not been
  submitted...`) can take several minutes to clear after submitting.
- Not every model tier is available to every account by default (we hit this
  with `claude-sonnet-5` specifically — a different `AccessDeniedException`
  than the use-case-form one — and fell back to `claude-sonnet-4-5` as the
  dataset-labeling teacher model instead).

### Create the Guardrail

Bedrock Console → Guardrails → Create guardrail. Content filters at a medium
threshold; sensitive-information filters for AWS keys/email/etc. set to
**Mask** (not Block — a masked review beats a fully failed one); a custom
regex for generic `key/secret/token = "..."` patterns, also set to Mask. The
`DRAFT` version works fine without formally publishing a numbered version.

## Usage

```bash
pr-review review <pr-url>          # print the review
pr-review review <pr-url> --post   # also post it as a PR comment
```

## Fine-tuning the classifier

```bash
python finetune/data/scrape_commits.py   # gold-positive CVE commits + a diverse unlabeled pool
python finetune/data/label_with_llm.py   # Claude Sonnet labels the pool: {label, confidence, rationale}
python finetune/data/build_dataset.py    # repo-level 70/15/15 split (no repo spans train+test)
python finetune/train.py                 # LoRA r=8/alpha=16 on CodeBERT's query/value projections
python finetune/eval.py                  # recall-constrained threshold sweep on the held-out test split
python finetune/export.py <hf-repo-id>   # push the adapter to Hugging Face Hub
```

`scrape_commits.py` fetches diffs concurrently (`ThreadPoolExecutor`) since
that's plain GitHub REST traffic; `label_with_llm.py` deliberately runs
**sequentially** with a 2s pause between calls, because this account's
Bedrock quota for Sonnet turned out to be tight enough that even 2 concurrent
workers produced a >50% throttling rate despite an adaptive-retry boto3
config — a real constraint discovered by hitting it, not a default choice.
It writes results incrementally (one line per success) rather than batching
everything until the end, so an interrupted run doesn't lose completed work.

### Dataset scale and an honest finding about the recall/precision trade-off

The pipeline was first proven end to end on a ~27-example toy set, then
scaled up to a real **700-example** dataset (79 gold-positive CVE commits +
621 Sonnet-labeled diverse-pool examples, out of ~1,580 scraped — GitHub's
commit-search rate limit and the account's Bedrock Sonnet throughput quota
both capped how much further this could scale in one run). Repo-level split:
485 train / 95 val / 120 test, each with a meaningful number of positives
(unlike the toy run's val split, which had zero).

On the held-out test set, the recall-constrained threshold sweep picked
threshold **0.015**, giving **recall 0.929** (catches 93% of genuinely
security-relevant diffs — clears the 0.90 target) at **precision 0.243**
(~3 in 4 flags are false positives). That's the deliberate, correct
trade-off for this use case: a false positive just costs one extra
specialist call, a false negative silently skips a real security check.

The honest finding: re-running the eval harness (`scripts/eval_classifier_gate.py`)
against the same 4 real PRs at this new threshold produced a **0% skip
rate** — every PR cleared 0.015, including clearly benign ones. This isn't
a bug; it's the direct mathematical consequence of pushing the threshold low
enough to hit 93% recall on a 700-example dataset with only ~120 test-set
positives to fit against. At this scale, achieving high recall requires
"catch almost everything," which trades away essentially all of the
classifier gate's cost-saving benefit in exchange for safety. Getting both
high recall *and* a usefully selective threshold (real skip-rate, real cost
savings) needs more data — the plan's original ~2,000-example target, with
positives spread across dozens of repos instead of a handful, so the model
has enough signal to separate the classes without needing such an extreme
cutoff. The *mechanism* itself (routing, the `Send`-based skip, the
transparency footer, the counterfactual cost measurement) is independently
verified correct via unit tests and a forced-skip integration test — what's
data-scale-limited is the classifier's actual judgment, not the plumbing
around it.

**Why LoRA-CodeBERT over GraphCodeBERT:** GraphCodeBERT's data-flow-graph
preprocessing overhead isn't justified for a binary "is this diff
security-sensitive" gate — that's a coarse relevance signal, not a task that
needs GraphCodeBERT's finer-grained code-semantics representation.

## Repo structure

```
src/pr_review_agent/
  cli.py                 # `pr-review review <pr-url>`
  config.py               # pydantic-settings, loads .env
  graph/                  # LangGraph state, node build, and node implementations
  tools/                  # GitHub API, Semgrep, ruff, diff parsing, test-coverage heuristic
  guardrails/              # ApplyGuardrail client + check_input/check_output
  classifier/              # local inference (score_diff, get_threshold) + shared preprocessing
  llm/                     # Bedrock chat model factory (adaptive retry config)
finetune/                 # one-off pipeline: scrape -> label -> build -> train -> eval -> export
tests/unit/                # fast, deterministic tests (no network calls)
scripts/                  # diagnostic/debug scripts used while building this
.github/workflows/         # ci.yml (lint+test), pr-review.yml (auto-review this repo's own PRs)
```

