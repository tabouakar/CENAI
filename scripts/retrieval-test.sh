#!/bin/sh

./deepseek/llama.cpp/build/bin/llama-retrieval \
	--top-k 3 \
	--model ./deepseek/DeepSeek-V3-Q2_K_XS-00001-of-00005.gguf \
	--context-file ./retrieval_docs/ethics.json
