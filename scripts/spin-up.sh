#!/bin/bash

tmux new-session -d -s chroma 'cd /opt/team/retrieval_docs ; ./start-chroma.sh'
tmux new-session -d -s node 'cd /opt/team/cenai ; npm start'
tmux new-session -d -s php 'cd /opt/team/cenai/php/ ; sudo php -S localhost:8000'
