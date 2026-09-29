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

## 环境变量

Mock 和 parse 不需要配置。真实 AI 模式在项目根目录复制 `.env.example` 为 `.env`，填写自己的 Key：

```dotenv
OPENAI_API_KEY=your-key
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=https://api.openai.com/v1
RESUME_AI_TIMEOUT=60
```

程序只读取当前目录的 `.env`，系统环境变量优先。模型必须支持 JSON mode；兼容服务可调整 BASE_URL 和 MODEL。超时单位为秒，合法范围 `(0,300]`；SDK 对部分临时错误最多重试两次，因此整体等待可能长于单次超时。不要提交 `.env` 或真实简历。真实 AI 模式会把提取的简历文本和 JD 发送给配置的服务。

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
