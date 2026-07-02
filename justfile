container_runtime := "docker"
vllm_model := "Qwen/Qwen2.5-1.5B-Instruct"
vllm_image := "docker.io/vllm/vllm-openai-cpu:v0.24.0"

no_cross_encoder := ""
rrf_min_score := ""
no_mlflow := ""
no_judge := ""
no_grounding := ""
temperature := ""
top_p := ""
top_k := ""

test:
    uv run pytest tests/ -rs -m "not slow"

test-all:
    uv run pytest tests/ -rs

test-slow:
    uv run pytest tests/ -rs -m slow

test-llm *args:
    uv run pytest tests/ -rs --test-llm -m llm -v -s --tb=short --timeout=120 -W ignore::DeprecationWarning {{ args }}

vllm-start:
    {{ container_runtime }} run -d --name vllm-server \
      --security-opt seccomp=unconfined \
      --cap-add SYS_NICE \
      --shm-size=4g \
      -p 8000:8000 \
      -v ~/.cache/huggingface:/root/.cache/huggingface \
      -e VLLM_CPU_KVCACHE_SPACE=4 \
      {{ vllm_image }} \
      --model {{ vllm_model }} \
      --max-model-len 4096
    @echo "Waiting for vLLM to be ready..."
    @for i in $(seq 1 90); do \
      curl -sf http://localhost:8000/health > /dev/null 2>&1 && echo "vLLM is ready." && break; \
      printf "  attempt %s/90\n" "$i"; \
      sleep 5; \
    done
    @echo ""
    @echo "Run tests with:"
    @echo "  LLM_BASE_URL=http://localhost:8000/v1 LLM_MODEL={{ vllm_model }} just test-llm"

vllm-stop:
    -{{ container_runtime }} stop vllm-server
    -{{ container_runtime }} rm vllm-server

tidy: format lint type-check

type-check:
    uv run mypy src/asago_policy_mapper/

lint:
    uv run ruff check src/ tests/

format:
    uv run ruff format src/ tests/

run-risk-extract-battery battery base_url="" model="" bi_encoder="" cross_encoder="" jobs="6":
    uv run python run_extract_battery.py {{ battery }} -j {{ jobs }} {{ if base_url != "" { "--base-url " + base_url } else { "" } }} {{ if model != "" { "--model " + model } else { "" } }} {{ if bi_encoder != "" { "--bi-encoder-model " + bi_encoder } else { "" } }} {{ if cross_encoder != "" { "--cross-encoder-model " + cross_encoder } else { "" } }} {{ if no_cross_encoder != "" { "--no-cross-encoder" } else { "" } }} {{ if rrf_min_score != "" { "--rrf-min-score " + rrf_min_score } else { "" } }} {{ if no_mlflow != "" { "--no-mlflow" } else { "" } }} {{ if no_judge != "" { "--no-judge" } else { "" } }} {{ if no_grounding != "" { "--no-grounding" } else { "" } }} {{ if temperature != "" { "--temperature " + temperature } else { "" } }} {{ if top_p != "" { "--top-p " + top_p } else { "" } }} {{ if top_k != "" { "--top-k " + top_k } else { "" } }}
