#!/bin/sh

./deepseek/llama.cpp/build/bin/llama-server \
	--model ./deepseek/DeepSeek-V3-Q2_K_XS-00001-of-00005.gguf \
	--port 3000\
	--api-key dummy\
