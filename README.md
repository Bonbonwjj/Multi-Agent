# ChatDev 

本项目按照论文与官方 `chatdev1.0` 分支复现 ChatDev 的核心算法，并提供交互式可视化学习界面。

- 论文：<https://aclanthology.org/2024.acl-long.810/>
- 官方实现：<https://github.com/OpenBMB/ChatDev/tree/chatdev1.0>
- 可视化界面：`web/`

## 对齐内容

| 官方阶段 | 角色组合 | 最大循环 | CDH |
|---|---|---:|---|
| DemandAnalysis | CEO → CPO | 1 | ✓ |
| LanguageChoose | CEO → CTO | 1 | ✓ |
| Coding | CTO → Programmer | 1 | — |
| CodeComplete | CTO → Programmer | 10 | ✓ |
| CodeReview | Programmer ↔ Reviewer | 3 | ✓ |
| SystemTest | Tester ↔ Programmer | 3 | ✓ |
| EnvironmentDoc | CTO → Programmer | 1 | ✓ |
| Manual | CEO → CPO | 1 | — |

实现包含论文公式（7）的沟通式去幻觉：Instructor 发出指令后，Assistant 先以 `<CLARIFY>` 主动索取一个具体约束，Instructor 回答后，Assistant 才生成正式产物。阶段内保留完整短期对话；跨阶段只传递提取后的产物作为长期记忆。

## 运行算法

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# 无 API 的确定性教学演示
chatdev-repro --mock \
  --task "开发一个离线待办事项工具" \
  --output outputs/demo
```

接入 OpenAI Chat Completions 兼容服务：

```bash
export OPENAI_API_KEY="..."
export OPENAI_BASE_URL="https://api.openai.com/v1"
export OPENAI_MODEL="gpt-4o-mini"

chatdev-repro \
  --task "开发一个带测试的五子棋程序" \
  --output outputs/gomoku
```

生成代码默认只做静态语法验证。仅应在可信沙箱中使用 `--execute` 执行模型生成的代码：

```bash
chatdev-repro --execute --task "..." --output outputs/run
```

每次运行生成：

- 软件源代码
- `requirements.txt`
- `manual.md`
- `CHATDEV_RUN.json`：阶段、角色、轮次、对话与工具反馈

## 启动可视化界面

```bash
cd web
npm install
npm run dev
```

打开 <http://localhost:3000>。界面用于交互学习官方算法，不会把 API Key 发送到浏览器。真实模型运行通过 Python CLI 完成。

## 代码导读

```text
src/chatdev_repro/
├── config.py       官方阶段、角色、循环与目标
├── agents.py       双角色 seminar 与严格 CDH
├── pipeline.py     Chat Chain、记忆和修订循环
├── workspace.py    文件解析、路径隔离、语法与运行反馈
├── events.py       可观察事件模型
├── llm.py          OpenAI 兼容接口与离线 Mock
└── cli.py          命令行入口
```

## 验证

```bash
PYTHONPATH=src python3 -m pytest
cd web && npm run build
```

说明：这是忠实的算法与工作流复现，而非论文数值逐点复现。完全复现实验表格还需要论文使用的 70 个需求、固定的 ChatGPT-3.5 快照、人工/GPT-4 成对评价和原始执行环境。
