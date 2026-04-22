"""
Action node implementations — Email, Notify, HTTP, File, Desktop.
"""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from loguru import logger

from config.settings import OUTPUTS_DIR


def _resolve(template: str, ctx: Dict[str, Any]) -> str:
    """Replace template variables with context values."""
    output = str(ctx.get("output", ""))
    return (template
            .replace("{input}", output)
            .replace("{output}", output)
            .replace("{date}", datetime.now().strftime("%Y-%m-%d"))
            .replace("{time}", datetime.now().strftime("%H-%M-%S"))
            .replace("{workflow_name}", ctx.get("_workflow_name", "workflow")))


def run_send_email(config: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    recipients = config.get("to", "")
    subject = _resolve(config.get("subject", "NexusAgent Report"), ctx)
    body_mode = config.get("body_mode", "use_previous_output")
    require_approval = config.get("require_approval", True)

    if not recipients:
        ctx["output"] = "Email skipped: no recipient configured"
        return ctx

    # Build body
    if body_mode == "use_previous_output":
        body = str(ctx.get("output", "No content"))
    elif body_mode == "custom":
        body = _resolve(config.get("custom_body", "{input}"), ctx)
    else:  # ai_draft
        try:
            from config.llm_config import get_llm
            llm = get_llm()
            body = llm.invoke(
                f"Write a professional email body about:\n{ctx.get('output', '')[:1000]}"
            ).strip()
        except Exception:
            body = str(ctx.get("output", ""))

    try:
        from action_tools.email_tool import compose_and_send
        for recipient in recipients.split(","):
            recipient = recipient.strip()
            if not recipient:
                continue
            result = compose_and_send(
                recipient=recipient,
                subject_hint=subject,
                context=body,
                test_mode=require_approval,  # require_approval=True → test_mode=True (no auto-send)
            )
            saved = result.get("saved_path")
            ctx["output"] = (
                f"Email draft saved for approval: {saved}"
                if require_approval else
                f"Email sent to {recipient}"
            )
        logger.info(f"[Action] send_email → {recipients}")
    except Exception as e:
        ctx["output"] = f"Email action failed: {e}"

    return ctx


def run_discord_notify(config: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    title = _resolve(config.get("title", "NexusAgent Alert"), ctx)
    message = _resolve(config.get("message", "{input}"), ctx)
    severity = config.get("severity", "info")

    try:
        from action_tools.discord_tool import send_alert
        send_alert(title, message[:1000], severity)
        ctx["output"] = f"Notification sent: [{severity}] {title}"
        logger.info(f"[Action] discord_notify: {title}")
    except Exception as e:
        ctx["output"] = f"Notification failed: {e}"

    return ctx


def run_http_request(config: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    import json as _json
    url = config.get("url", "")
    method = config.get("method", "POST")
    headers_raw = config.get("headers_json", '{"Content-Type": "application/json"}')
    body_template = config.get("body_template", '{"text": "{input}"}')
    api_key_name = config.get("api_key_name", "")

    if not url:
        ctx["output"] = "HTTP request skipped: no URL configured"
        return ctx

    try:
        headers = _json.loads(headers_raw) if headers_raw.strip() else {}
    except Exception:
        headers = {"Content-Type": "application/json"}

    # Inject API key if specified
    if api_key_name:
        from workflows.storage import get_api_key
        key_val = get_api_key(api_key_name)
        if key_val:
            headers["Authorization"] = f"Bearer {key_val}"

    body_str = _resolve(body_template, ctx)
    try:
        body = _json.loads(body_str)
    except Exception:
        body = {"text": body_str}

    try:
        import requests
        resp = getattr(requests, method.lower())(url, json=body, headers=headers, timeout=10)
        ctx["output"] = f"HTTP {method} {url} → {resp.status_code}"
        ctx["_http_response"] = resp.text[:500]
        logger.info(f"[Action] http_request → {resp.status_code}")
    except Exception as e:
        ctx["output"] = f"HTTP request failed: {e}"

    return ctx


def run_save_file(config: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    filename_template = config.get("filename_template", "{workflow_name}_{date}.txt")
    fmt = config.get("format", "txt")
    filename = _resolve(filename_template, ctx)
    if not filename.endswith(f".{fmt}"):
        filename = f"{filename}.{fmt}"

    out_dir = Path(OUTPUTS_DIR) / "workflow_outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / filename

    content = ctx.get("output", "")
    df = ctx.get("_last_df")

    try:
        if fmt == "csv" and df is not None:
            df.to_csv(str(out_path), index=False)
        elif fmt == "json":
            import json as _json
            out_path.write_text(
                _json.dumps({"output": content, "timestamp": datetime.now().isoformat()}, indent=2),
                encoding="utf-8"
            )
        else:
            out_path.write_text(str(content), encoding="utf-8")

        ctx["output"] = f"Saved to: {out_path}"
        logger.info(f"[Action] save_file → {out_path}")
    except Exception as e:
        ctx["output"] = f"Save file failed: {e}"

    return ctx


def run_desktop_notify(config: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    title = _resolve(config.get("title", "NexusAgent"), ctx)
    message = _resolve(config.get("message", "{input}"), ctx)

    try:
        from plyer import notification
        notification.notify(title=title, message=message[:256], timeout=8)
        ctx["output"] = f"Desktop notification shown: {title}"
    except Exception:
        print(f"\n[NOTIFY] {title}: {message}\n")
        ctx["output"] = f"Notification printed (plyer unavailable): {title}"

    return ctx


def run_wait_node(config: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    import time
    seconds = config.get("seconds", 5)
    logger.info(f"[Control] wait_node → sleeping {seconds}s")
    time.sleep(min(seconds, 300))  # max 5 min wait in workflows
    ctx["output"] = f"Waited {seconds} seconds"
    return ctx


def run_merge_node(config: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    strategy = config.get("strategy", "concat_text")
    branch_outputs = ctx.get("_branch_outputs", [])

    if strategy == "concat_text":
        ctx["output"] = "\n\n---\n\n".join(str(o) for o in branch_outputs if o)
    elif strategy == "first_available":
        ctx["output"] = next((o for o in branch_outputs if o), "")
    elif strategy == "concat_list":
        ctx["output"] = str(branch_outputs)
    else:
        ctx["output"] = str(branch_outputs)

    return ctx
