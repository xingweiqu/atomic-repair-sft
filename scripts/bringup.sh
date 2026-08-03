#!/bin/bash
# New-machine bring-up (SERVER_OPS §1, scripted). Idempotent.
set -x
cat > ~/atomic_env.sh << 'ENVEOF'
export http_proxy="http://sys-proxy-rd-relay.byted.org:8118"
export https_proxy="http://sys-proxy-rd-relay.byted.org:8118"
export no_proxy="byted.org"
export PATH="$HOME/.local/bin:$PATH"
export DISABLE_VERSION_CHECK=1
export HF_HUB_DISABLE_XET=1
ENVEOF
source ~/atomic_env.sh
cd /opt/tiger
[ -d atomic-repair-sft-github ] || git clone -b prescription-v1 https://github.com/xingweiqu/atomic-repair-sft.git atomic-repair-sft-github
cd atomic-repair-sft-github && git fetch -q origin prescription-v1 && git checkout -q -B prescription-v1 origin/prescription-v1
cd /opt/tiger
[ -d LLaMA-Factory ] || git clone --depth 1 https://github.com/hiyouga/LLaMA-Factory.git
cd LLaMA-Factory && pip3 install -q -e . --no-deps
pip3 install -q "datasets==4.0.0" "trl==0.24.0" "peft==0.18.1" "accelerate==1.11.0" "deepspeed==0.19.2" matplotlib fire omegaconf
python3 -c "import vllm, torch; print('vllm', vllm.__version__, 'torch', torch.__version__)"
which llamafactory-cli
echo "BRINGUP_OK"
