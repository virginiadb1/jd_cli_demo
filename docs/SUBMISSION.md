# 提交清单

- 仓库：https://github.com/virginiadb1/jd_cli_demo
- 演示视频链接：待上传后填写（不要把本地文件路径当成公开链接）
- 姓名：待本人填写
- 联系方式：待本人填写

提交前确认仓库可公开访问，并用自己的 API Key 跑一次 extract 和 score。不要上传招聘题目原文、API Key 或真实候选人隐私资料。

## 约 3 分钟演示讲解

1. 展示 README，说明 Python、pypdf、OpenAI SDK 和 Pydantic 的分工。
2. 展示虚拟环境安装及 `resume-cli --help`。
3. 运行 `resume-cli parse examples/resume.pdf`，解释文本 PDF 与扫描件区别。
4. 运行 `resume-cli extract examples/resume.pdf --mock`，展示 JSON，并说明 Mock 不访问网络、教育信息不猜测。
5. 运行 `resume-cli score examples/resume.pdf --jd examples/jd.txt --mock --output score.json`，说明技能命中规则和评分权重。
6. 展示 `.env.example`（不要展示真实 .env），说明去掉 --mock 即调用真实模型。
7. 运行不存在文件的命令，展示友好错误；运行 pytest 展示测试结果。
8. 展示 src/resume_cli 的文件结构，说明输入、模型、API、CLI 分层，以及 OCR 和真实服务验证的限制。

`scripts/demo.ps1` 可一次运行上述主要命令。录屏时可逐条运行以控制节奏。
