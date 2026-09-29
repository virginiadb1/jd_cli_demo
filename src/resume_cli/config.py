"""Offline onboarding and local, provider-bound credentials."""
import getpass
import json
import os
import sys
import tempfile
import warnings
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import dotenv_values
from pydantic import BaseModel, ConfigDict, SecretStr, ValidationError

from .errors import ResumeError

# Models are entered explicitly: availability varies by account, region and date.
PROVIDERS = (
    ("OpenAI", "https://api.openai.com/v1"),
    ("DeepSeek", "https://api.deepseek.com"),
    ("阿里云百炼 / 通义千问（中国站）", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
    ("Google Gemini", "https://generativelanguage.googleapis.com/v1beta/openai/"),
    ("Moonshot / Kimi（中国站）", "https://api.moonshot.cn/v1"),
    ("智谱 GLM（通用 API）", "https://open.bigmodel.cn/api/paas/v4"),
    ("硅基流动 SiliconFlow（中国站）", "https://api.siliconflow.cn/v1"),
    ("火山方舟 / 豆包（北京）", "https://ark.cn-beijing.volces.com/api/v3"),
    ("自定义 OpenAI 兼容服务", ""),
)


class AISettings(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    provider: str
    base_url: str
    model: str
    api_key: SecretStr


def config_path() -> Path:
    if sys.platform == "win32":
        root = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    else:
        root = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return root / "resume-cli" / "config.json"


def validate_url(value: str) -> str:
    try:
        parsed = urlsplit(value)
        valid = (parsed.scheme == "https" and parsed.hostname and not parsed.username
                 and not parsed.password and not parsed.query and not parsed.fragment
                 and not any(char.isspace() for char in value))
        _ = parsed.port
    except ValueError:
        valid = False
    if not valid:
        raise ResumeError("服务地址必须是有效的 HTTPS Base URL，不能含账号、密码或查询参数。")
    return value


def valid_key(value: str) -> bool:
    return bool(value and not any(c.isspace() for c in value)
                and value not in {"replace-with-your-key", "your-key", "your-api-key"})


def validate_settings(settings: AISettings) -> AISettings:
    validate_url(settings.base_url)
    if not settings.model.strip():
        raise ResumeError("模型名称不能为空，请运行 resume-cli configure。")
    if not valid_key(settings.api_key.get_secret_value()):
        raise ResumeError("缺少有效的 OPENAI_API_KEY：请运行 resume-cli configure，或使用 --mock。")
    return settings


def load_saved() -> AISettings | None:
    path = config_path()
    if not path.exists():
        return None
    try:
        return validate_settings(AISettings.model_validate_json(path.read_text(encoding="utf-8")))
    except (OSError, ValueError, ValidationError) as exc:
        raise ResumeError("本机 AI 配置无法读取或格式不正确，请重新运行 resume-cli configure。") from exc


def resolve_settings() -> AISettings:
    """Select a complete credential bundle; never mix a saved key with another URL."""
    local_env = dotenv_values(Path.cwd() / ".env", interpolate=False)
    for source, name in ((os.environ, "环境变量"), (local_env, "当前目录 .env")):
        if "OPENAI_API_KEY" in source:
            return validate_settings(AISettings(
                provider=name,
                api_key=SecretStr((source.get("OPENAI_API_KEY") or "").strip()),
                base_url=source.get("OPENAI_BASE_URL") or "https://api.openai.com/v1",
                model=source.get("OPENAI_MODEL") or "gpt-4o-mini",
            ))
    settings = load_saved()
    if settings is None:
        raise ResumeError("缺少 OPENAI_API_KEY：请先运行 resume-cli configure，或使用 --mock 离线演示。")
    return settings


def timeout_value() -> str:
    return os.getenv("RESUME_AI_TIMEOUT") or dotenv_values(
        Path.cwd() / ".env", interpolate=False
    ).get("RESUME_AI_TIMEOUT") or "60"


def save_settings(settings: AISettings) -> Path:
    validate_settings(settings)
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Even an accidental repository initialized in this directory ignores credentials.
    (path.parent / ".gitignore").write_text("*\n", encoding="utf-8")
    payload = settings.model_dump(mode="json")
    payload["api_key"] = settings.api_key.get_secret_value()
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".config-", delete=False) as stream:
            temporary = Path(stream.name)
            if os.name != "nt":
                os.chmod(temporary, 0o600)
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return path


def configure() -> None:
    if not sys.stdin.isatty():
        raise ResumeError("请在交互式终端运行 resume-cli configure；不支持通过管道输入 Key。")
    print("首次配置 / 更换平台（全程离线，不会验证或发送 Key）")
    print("Key 以未加密配置文件保存在当前系统用户目录，不写入项目或 Git。")
    print("只有运行非 Mock 的 AI 命令时，才向所选服务发送 Key 用于认证。")
    try:
        if config_path().exists():
            if input("已有本机配置，是否替换？[y/N]：").strip().lower() != "y":
                print("已取消，原配置保持不变。")
                return
        for number, (label, _) in enumerate(PROVIDERS, 1):
            print(f"  {number}. {label}")
        while True:
            choice = input("选择平台编号：").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(PROVIDERS):
                break
            print("请输入列表中的有效编号。")
        provider, base_url = PROVIDERS[int(choice) - 1]
        if not base_url:
            while True:
                try:
                    base_url = validate_url(input("HTTPS Base URL：").strip())
                    break
                except ResumeError as exc:
                    print(str(exc))
        print(f"服务地址：{base_url}")
        print("请输入该平台控制台中可用且支持 JSON mode 的模型 ID；方舟也可填推理接入点 ID。")
        model = ""
        while not model:
            model = input("模型 ID：").strip()
        # Fail closed if getpass cannot disable echo; never fall back to visible input.
        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            key = getpass.getpass("API Key（输入隐藏）：").strip()
        if not valid_key(key):
            raise ResumeError("Key 不能为空、包含空白或使用示例占位值；配置未保存。")
        settings = AISettings(provider=provider, base_url=base_url, model=model,
                              api_key=SecretStr(key))
        if input("保存到本机？[Y/n]：").strip().lower() not in {"", "y"}:
            print("已取消，配置未保存。")
            return
        path = save_settings(settings)
        print(f"配置已保存：{path}（Key 不回显，未发送网络请求）")
        print("现在可运行 resume-cli extract examples/resume.pdf。")
        print("如已设置 OPENAI_API_KEY 环境变量或当前目录 .env，它们会优先于此配置。")
    except (EOFError, getpass.GetPassWarning) as exc:
        raise ResumeError("输入已中断或终端无法隐藏 Key，配置未保存。请使用本机交互式终端。") from exc


def show_config() -> None:
    settings = resolve_settings()
    print(json.dumps({"provider": settings.provider, "base_url": settings.base_url,
                      "model": settings.model, "api_key": "已配置（隐藏）"},
                     ensure_ascii=False, indent=2))


def reset_config() -> None:
    config_path().unlink(missing_ok=True)
    print("本机保存的 AI 配置已删除。环境变量和项目 .env 不受影响。")
