# Resume CLI

一个可安装的 Python 命令行 Demo：读取 PDF 简历、调用大模型提取结构化信息、结合 JD 输出匹配评分。包含离线 Mock 模式，克隆后无需 API Key 即可演示。示例全部为虚构数据。

## 技术选型

- Python 3.11+、argparse：轻量 CLI，支持标准帮助和退出码。
- pypdf：本地提取 PDF 文本，不上传 PDF 原文件。
- OpenAI Python SDK：调用支持 Chat Completions 和 JSON mode 的 API，可配置兼容服务。
- Pydantic 2：严格校验 JSON 字段、类型、评分范围；禁止额外字段。
- pytest、httpx MockTransport：离线测试文件、CLI、模型校验和真实 SDK 请求链路。

## 安装

```powershell
git clone https://github.com/virginiadb1/jd_cli_demo.git
cd jd_cli_demo
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
resume-cli --help
```

macOS/Linux 使用 `source .venv/bin/activate`。如 PowerShell 不允许激活脚本，可直接执行 `.\.venv\Scripts\resume-cli.exe`。也支持 `python -m resume_cli`。有 uv 时可用 `uv sync --extra dev --frozen` 和 `uv run resume-cli --help`。

## 首次使用：选择平台并录入 API Key

安装完成后运行：

```powershell
resume-cli configure
```

向导会依次让你选择平台、确认默认模型（直接回车即可）、隐藏输入 API Key，再确认保存。全程离线，不会自动验证 Key，也不会发出测试请求；无需把 Key 放到命令参数或聊天里。可随时再次运行此命令更换平台，已有配置会先询问是否替换。

预置平台如下，每个预置平台都有默认模型，**不必手动选择或填写，直接回车即可**。需要覆盖时，可填写自己账户可用且支持 **Chat Completions + JSON mode** 的模型 ID。向导不联网获取模型列表，避免在配置阶段传输 Key。不同地区、计费方案的 Key 和接口不能混用。

| 平台 | 默认模型（回车使用） | 预置 Base URL |
| --- | --- | --- |
| OpenAI | `gpt-4o-mini` | `https://api.openai.com/v1` |
| DeepSeek | `deepseek-flash` | `https://api.deepseek.com` |
| 阿里云百炼 / 通义千问（中国站） | `qwen-plus` | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| Google Gemini | `gemini-3.8-flash` | `https://generativelanguage.googleapis.com/v1beta/openai/` |
| Moonshot / Kimi（中国站） | `kimi-k2.6` | `https://api.moonshot.cn/v1` |
| 智谱 GLM（通用 API） | `glm-4-flash` | `https://open.bigmodel.cn/api/paas/v4` |
| 硅基流动（中国站） | `deepseek-ai/DeepSeek-V3.2` | `https://api.siliconflow.cn/v1` |
| 火山方舟 / 豆包（北京） | `doubao-seed-2-0-lite-260215` | `https://ark.cn-beijing.volces.com/api/v3` |
| 自定义兼容服务 | 未知地址需手动填写；已知地址使用对应默认值 | 手动填写 HTTPS Base URL |

例如选择 DeepSeek 后，模型一栏直接回车会保存 `deepseek-flash`，以后 extract/score 会自动使用它。显式填写的模型始终保留，不会被默认值覆盖。缺失或空白模型会根据已知 Base URL 补默认值；未知地址会在本地提示填写模型，绝不会误用 OpenAI 模型。火山方舟也可填写已创建的推理接入点 ID。其他地区或 Coding Plan 专用接口使用“自定义兼容服务”。Anthropic 原生 Messages API、Azure 特有鉴权接口未接入，不能仅修改地址就宣称支持。默认值是离线预设，不代表账户一定已开通该模型；无权限、余额不足或模型下线仍会明确报错，可重新 configure 修改模型。不会自动切换平台或偷偷换用其他收费模型。针对预置的通义、DeepSeek、Kimi、豆包默认模型，程序带上关闭思考模式的参数以适配本任务；其他手动模型不自动附加这些参数。尚未逐个平台真实联网验证。

完整使用流程：

```powershell
resume-cli configure
resume-cli configure --show
resume-cli parse examples/resume.pdf
resume-cli extract examples/resume.pdf --output result.json
resume-cli score examples/resume.pdf --jd examples/jd.txt --output score.json
```

配置管理：

```powershell
resume-cli configure --help
resume-cli configure --show   # 显示实际生效的平台、地址、模型，始终隐藏 Key
resume-cli configure --reset  # 删除本机保存的配置；不修改环境变量或 .env
```

### Key 保存位置与隐私边界

- Windows：`%LOCALAPPDATA%\resume-cli\config.json`。
- macOS/Linux：`$XDG_CONFIG_HOME/resume-cli/config.json`，未设置时为 `~/.config/resume-cli/config.json`。
- 配置写入系统用户目录，不写入项目仓库；配置目录额外生成忽略全部内容的 `.gitignore`。本项目也忽略 `.env` 和本地配置副本，不会通过正常 `git add` 提交 Key。不要手动强制提交或复制到受版本管理的文件。
- **本地配置是未加密 JSON 文件**；Unix 文件权限为仅当前用户读写（0600），Windows 使用用户目录继承权限。请不要分享该文件或放入同步盘；本机管理员或能访问该目录的程序仍可能读取它。
- 输入 Key 时不回显，查看配置、日志和错误都不显示 Key；不接受 Key 命令行参数或管道输入。终端无法隐藏输入时直接退出，不退回明文输入。
- **安装、配置、查看/删除配置、parse 和 Mock 模式均不会发送 Key。实际执行非 Mock 的 extract/score 时，必须通过 HTTPS 向所选 AI 平台发送 Key 用于认证，同时发送简历/JD 文本。**没有另设上传、遥测或 Key 收集服务；并不承诺联网 AI 调用期间 Key 完全不传输。

### 没有 Key 会怎样？

未配置 Key 时，`parse` 和 `--mock` 正常工作。对有效输入运行非 Mock 的 `extract` 或 `score` 会在创建 AI 客户端前失败，退出码为 **1**，不发出 AI 请求：

```text
错误：缺少 OPENAI_API_KEY：请先运行 resume-cli configure，或使用 --mock 离线演示。
```

保存配置不会判断 Key 的线上有效性。Key 错误、失效、额度不足或模型不支持，会在真实调用时报告相应错误。

## 环境变量（可选，兼容原用法）

Mock 和 parse 不需要配置。除向导外，也可以在项目根目录复制 `.env.example` 为 `.env`，填写自己的 Key：

```dotenv
OPENAI_API_KEY=your-key
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=https://api.openai.com/v1
RESUME_AI_TIMEOUT=60
```

配置来源优先级为：**含 OPENAI_API_KEY 的系统环境变量 → 含 OPENAI_API_KEY 的当前目录 .env → configure 保存的本机配置**。Key、BASE_URL、MODEL 作为同一来源的一组读取，避免把某平台的本机 Key 发往另一个来源的地址。环境变量或 .env 来源省略地址时默认 OpenAI 地址；省略或留空模型时，按该来源的 Base URL 自动选用上表默认模型。使用其他平台必须在同一来源中配置 Key 和地址，模型可以不填。仅设置 BASE_URL 不会覆盖本机配置的地址。高优先级来源的 Key 为空或为示例占位符时会明确报错，不悄悄使用其他 Key。

程序只读取当前目录的 `.env`，不修改进程环境变量。超时配置仍按系统环境变量、当前目录 `.env`、默认 60 秒读取；合法范围 `(0,300]`。SDK 对部分临时错误最多重试两次，因此整体等待可能长于单次超时。不要提交 `.env` 或真实简历。

## CLI 命令

```powershell
resume-cli parse examples/resume.pdf
resume-cli parse examples/resume.pdf --output resume.txt
resume-cli extract examples/resume.pdf --mock
resume-cli extract examples/resume.pdf --output result.json
resume-cli score examples/resume.pdf --jd examples/jd.txt --mock
resume-cli score examples/resume.pdf --jd examples/jd.txt --output score.json --verbose
resume-cli score --help
```

`--output` 同时保留终端输出，文件使用 UTF-8；父目录必须存在，已有结果文件会覆盖，但禁止覆盖输入文件。`--verbose` 日志及错误写入 stderr；stdout 仅包含文本或 JSON，适合管道使用。退出码：成功 0、运行失败 1、参数错误 2、用户中断 130。

## 示例输入与输出

`examples/resume.pdf` 包含虚构候选人 Alex Chen 的 Python、React、FastAPI、Docker 项目经历；`examples/jd.txt` 是虚构全栈岗位要求。可通过 `python scripts/create_sample.py` 重建 PDF。

Mock 提取示例（规则仅识别显式姓名、城市、电话、邮箱和技能词；教育列表不作推测）：

```json
{
  "name": "Alex Chen",
  "phone": "",
  "email": "alex@example.com",
  "city": "Beijing",
  "education": [],
  "skills": ["Python", "React", "FastAPI", "Docker", "PostgreSQL", "Git", "OpenAI"]
}
```

真实模式的教育项包含 `school`、`major`、`degree`、`graduation_time` 四个字符串。未知信息输出空字符串或空列表，不凭空补全。

评分 JSON 格式示例（仅说明结构，不是实测模型结论）：

```json
{
  "overall_score": 82,
  "skill_score": 88,
  "experience_score": 80,
  "education_score": 70,
  "comment": "技能较匹配，需进一步核实项目规模及独立交付经验。",
  "interview_questions": ["请介绍一个你负责的全栈项目及技术取舍。"]
}
```

真实模式先校验模型返回的所有分数，再由程序按技能 50%、经验 30%、教育 20%计算总分，四舍五入到整数，保证总分一致性。缺少岗位或简历证据时，要求模型在理由中标明不确定性。评分用于演示，仍需人工核实。

Mock 评分按 JD 中受支持技能词的命中比例计算技能分；经验和教育未评估，占位为 0，总分使用同样权重。输出理由和 stderr 均明确标记 MOCK，不能用于判断真实能力。

## 项目结构

```text
src/resume_cli/
  cli.py       参数、流程编排、输出和退出码
  config.py    离线配置向导、本机凭据及配置优先级
  files.py     PDF / JD 校验及文本读取
  ai.py        提示词、API 调用、JSON 清理和校验
  models.py    简历、教育、评分的数据模型
  mock.py      无网络的确定性演示
tests/         单元、CLI、SDK HTTP 模拟测试
examples/      虚构 PDF、JD 和示例结果
scripts/       样例生成与演示脚本
docs/          演示讲解与提交清单
```

## 测试

```powershell
python -m pytest -q
python -m ruff check .
```

测试不消耗 API 额度。HTTP 模拟覆盖 SDK 请求格式、成功解析及错误转换；它不等同于真实线上模型验证。GitHub Actions 配置了 Windows/Linux 和 Python 3.11/3.13 检查。

## 已实现功能

- parse / extract / score 与子命令帮助。
- configure 首次配置向导、8 个国内外平台预设、自定义接口、隐藏输入、脱敏查看与删除。
- PDF 不存在、扩展名错误、伪 PDF、损坏、加密、空文本等错误提示。
- JD 不存在、空白、非 UTF-8、路径不是文件等错误提示。
- JSON 严格校验，0–100 整数评分，非空理由和面试问题。
- 清理完整的 Markdown JSON 代码围栏；不猜测修复缺失字段或错误分数。
- Mock、结果保存、stderr 日志、Dockerfile、离线测试与 CI。
- 文件 20 MB、PDF 100 页、AI 输入合计 60000 字符限制；超长输入明确拒绝，不静默截断。
- 提示词将简历/JD 视为数据，要求忽略其中指令；日志不输出 Key、简历正文和 API 错误响应正文。

## 已知问题与未完成内容

- 扫描件不支持 OCR；复杂多栏、表格、缺字体的 PDF 文本顺序可能不准确。
- 没有真实 API Key 的环境仅完成 Mock 和 SDK 模拟验证；提交前建议使用自己的 Key 验证一次真实服务。
- 模型支持、费用、上下文限制由提供商决定；提示词不能完全消除幻觉或提示注入。
- JSON mode 保证语法的能力取决于服务；本地仍执行严格校验，不自动重试修复错误数据。
- 未实现批量处理、OCR、缓存、数据库和 UI，以保持 Demo 范围清晰。
- 姓名、联系方式及公开视频链接需提交者填写，参见 `docs/SUBMISSION.md`。

## Docker（可选）

```bash
docker build -t resume-cli .
docker run --rm resume-cli extract examples/resume.pdf --mock
docker run --rm --env-file .env resume-cli score examples/resume.pdf --jd examples/jd.txt
```

容器默认包含虚构示例。自己的文件通过 volume 挂载，输出路径也应挂载到宿主机。Docker 构建需联网安装依赖。

API 接口依据：[OpenAI Structured Outputs 官方文档](https://developers.openai.com/api/docs/guides/structured-outputs)。

平台配置参考：[DeepSeek](https://api-docs.deepseek.com/)、[百炼](https://help.aliyun.com/zh/model-studio/base-url)、[Gemini OpenAI 兼容接口](https://ai.google.dev/gemini-api/docs/openai)、[Kimi](https://platform.moonshot.cn/docs)、[智谱](https://docs.bigmodel.cn/)、[硅基流动](https://docs.siliconflow.cn/docs/userguide/quickstart)、[火山方舟](https://docs.volcengine.com/docs/ark/deep-thinking)。
