import argparse
import json
import logging
import sys
from pathlib import Path

from .ai import request_ai
from .config import configure, reset_config, show_config
from .errors import ResumeError
from .files import check_ai_length, parse_pdf, read_jd
from .mock import mock_extract, mock_score


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="resume-cli", description="PDF 简历解析与 AI 岗位匹配")
    sub = parser.add_subparsers(dest="command", required=True)
    setup = sub.add_parser("configure", help="离线配置 AI 平台、模型和 API Key")
    options = setup.add_mutually_exclusive_group()
    options.add_argument("--show", action="store_true", help="查看生效配置（不显示 Key）")
    options.add_argument("--reset", action="store_true", help="删除本机保存的配置")
    for name, description in (("parse", "提取 PDF 文本"), ("extract", "提取结构化信息"),
                              ("score", "根据 JD 评分")):
        command = sub.add_parser(name, help=description, description=description)
        command.add_argument("pdf_path", type=Path, help="本地 PDF 简历")
        command.add_argument("--output", type=Path, help="保存结果（parse 为文本，其余为 JSON）")
        command.add_argument("--verbose", action="store_true", help="向 stderr 输出简要日志")
        if name != "parse":
            command.add_argument("--mock", action="store_true", help="离线规则演示，不调用 AI")
        if name == "score":
            command.add_argument("--jd", type=Path, required=True, help="UTF-8 岗位描述文本")
    return parser


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO if getattr(args, "verbose", False) else logging.WARNING,
                        format="%(levelname)s: %(message)s", force=True)
    try:
        if args.command == "configure":
            if args.show:
                show_config()
            elif args.reset:
                reset_config()
            else:
                configure()
            return 0
        if args.output:
            protected = [args.pdf_path] + ([args.jd] if args.command == "score" else [])
            if any(args.output.resolve() == path.resolve() for path in protected):
                raise ResumeError("输出路径不能覆盖输入 PDF 或 JD。")
        text = parse_pdf(args.pdf_path)
        logging.info("PDF 文本提取完成，共 %d 字符", len(text))
        if args.command == "parse":
            output = text
        else:
            jd = read_jd(args.jd) if args.command == "score" else None
            check_ai_length(text + (jd or ""))
            if args.mock:
                print("MOCK：离线规则演示，结果不代表 AI 分析。", file=sys.stderr)
                result = mock_extract(text) if jd is None else mock_score(text, jd)
            else:
                logging.info("正在调用 AI 服务")
                result = request_ai(text, jd)
            output = json.dumps(result.model_dump(), ensure_ascii=False, indent=2)
        if args.output:
            args.output.write_text(output + "\n", encoding="utf-8")
            logging.info("结果已保存")
        print(output)
        return 0
    except (ResumeError, OSError) as exc:
        message = str(exc) if isinstance(exc, ResumeError) else "文件读写失败，请检查路径和权限。"
        print(f"错误：{message}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("操作已取消。", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
