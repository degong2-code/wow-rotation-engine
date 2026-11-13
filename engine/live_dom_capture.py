"""Bounded read-only browser DOM evidence capture for authorized pages.

Optional Playwright tool. No headless browser is required for normal ChatGPT-first
guide writing. Does not bypass site access controls. Can revisit safe UI states
and hover visible tooltip triggers, exporting PRIVATE local content and a separate
metadata-only audit without screenshots or source text in public reports.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse, urlsplit

CONTROL_SELECTOR = (
    "button[aria-controls], [role=tab], select, input[type=radio], "
    "input[type=checkbox], summary"
)
TOOLTIP_SELECTOR = (
    "[title], [data-hint-body], [data-tippy-content], [aria-describedby], "
    "[tooltip], [tooltip2], [data-tooltip], [data-tooltip-content], [data-bs-title]"
)
MAX_HTML = 12 * 1024 * 1024
MAX_TEXT = 250000

OBSERVE = r"""() => {
  const controlSelector = 'button[aria-controls], [role=tab], select, input[type=radio], input[type=checkbox], summary';
  const tipSelector = '[title], [data-hint-body], [data-tippy-content], [aria-describedby], [tooltip], [tooltip2], [data-tooltip], [data-tooltip-content], [data-bs-title]';
  const visible = (e) => {
    if (!e || !e.isConnected) return false;
    if (e.closest('[hidden], [inert], [aria-hidden="true"]')) return false;
    let cur=e;
    while (cur && cur.nodeType===1) {
      const cs=getComputedStyle(cur);
      if (cs.display==='none' || cs.visibility==='hidden') return false;
      cur=cur.parentElement;
    }
    return e.getClientRects().length > 0;
  };
  const controls=[...document.querySelectorAll(controlSelector)].map((e,index)=>{
    if (!visible(e)) return null;
    const kind=e.tagName.toLowerCase()==='select' ? 'select' :
      e.tagName.toLowerCase()==='summary' ? 'summary' :
      e.matches('input[type=radio]') ? 'radio' :
      e.matches('input[type=checkbox]') ? 'checkbox' : 'tab';
    const options=kind==='select' ? [...e.options].map(o=>({value:o.value,text:o.textContent.trim()})) : [];
    return {index,kind,id:e.id||null,name:e.getAttribute('name')||null,
            label:(e.getAttribute('aria-label')||e.textContent||e.value||'').trim().slice(0,140),
            target:e.getAttribute('aria-controls')||null,expanded:e.getAttribute('aria-expanded'),
            selected:e.getAttribute('aria-selected'),checked:!!e.checked,
            selected_value:kind==='select' ? e.value : null,options};
  }).filter(Boolean);
  const main=document.querySelector('main,[role=main]')||document.body;
  const body=(main.innerText||'').slice(0,250000);
  const markedTips=[...document.querySelectorAll(tipSelector)];
  const questionOnly=[...document.querySelectorAll('button,a,span')].filter(
    e=>e.children.length===0 && (e.textContent||'').trim()==='?'
  );
  const candidates=[...new Set([...markedTips,...questionOnly])];
  const cssPath=(e)=>{
    const parts=[];
    for(let node=e;node && node.nodeType===1 && node!==document.documentElement;node=node.parentElement){
      const siblings=[...node.parentElement.children].filter(el=>el.tagName===node.tagName);
      parts.unshift(node.tagName.toLowerCase()+':nth-of-type('+(siblings.indexOf(node)+1)+')');
    }
    return 'html > '+parts.join(' > ');
  };
  const tooltipTriggersAll=candidates.map((e,index)=>{
    if (!visible(e)) return null;
    const attr={};
    for (const k of ['title','data-hint-body','data-tippy-content','data-tooltip-content',
                     'data-bs-title','data-tooltip','aria-describedby','tooltip','tooltip2']) {
      const v=e.getAttribute(k);
      if(v!==null) attr[k]=v.slice(0,8000);
    }
    const refs={};
    for (const k of ['aria-describedby','tooltip','tooltip2','data-tooltip']) {
      const value=e.getAttribute(k)||'';
      if (!value) continue;
      const ids=(k==='aria-describedby'?value.split(/\s+/):[value.replace(/^#/,'')]);
      refs[k]=ids.map(id=>{const n=document.getElementById(id);
        return {id,body:n ? (n.textContent||'').trim().slice(0,8000) : null};});
    }
    const row=e.closest('tr');
    return {index,tag:e.tagName.toLowerCase(),id:e.id||null,
       css_path:cssPath(e),bare_question:!markedTips.includes(e),
       row_id:row?.id||null,near:(row?.innerText||e.parentElement?.innerText||'').slice(0,220),
       attributes:attr,references:refs};
  }).filter(Boolean);
  const dynamicOverlays=[...document.querySelectorAll('[role=tooltip],.tippy-box,.tooltip-inner')]
    .filter(visible).map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,20);
  return {title:document.title, url:location.href,body,controls,
          tooltip_trigger_total:tooltipTriggersAll.length,
          tooltip_triggers_truncated:tooltipTriggersAll.length>150,
          tooltip_triggers:tooltipTriggersAll.slice(0,150),
          dynamic_tooltips:dynamicOverlays,
          visible_page_heading:(main.querySelector('h1')?.innerText||'').slice(0,200)};
}"""

def digest(text: str) -> dict:
    normalized = " ".join(text.split())
    return {"characters": len(normalized),
            "sha256": hashlib.sha256(normalized.encode("utf-8")).hexdigest()}


def summarize(record: dict) -> dict:
    """Metadata-only public-safe report: drop UI prose and raw tooltip contents."""
    url = urlsplit(record["source_url"])
    return {
        "schema_version": "live-dom-capture-report-v1",
        "source_kind": url.scheme,
        "host": url.hostname or "",
        "path_sha256": hashlib.sha256(url.path.encode("utf-8")).hexdigest(),
        # Never expose query strings, fragments, filesystem paths or credentials.
        "source_sha256": record["source_sha256"],
        "observed_state_count": len(record["states"]),
        "pending_state_count": record.get("pending_state_count", 0),
        "capture_bounded": record.get("pending_state_count", 0) > 0,
        "depth_limited_state_count": record.get("depth_limited_state_count", 0),
        "states": [
            {"path": [{"kind": step["kind"], "index": step["index"],
                       "value_sha256": digest(str(step.get("value", "")))["sha256"]}
                      for step in state["path"]],
             "body_digest": digest(state["observation"]["body"]),
             "visible_controls": len(state["observation"]["controls"]),
             "visible_tooltip_triggers": state["observation"].get("tooltip_trigger_total",
                                           len(state["observation"]["tooltip_triggers"])),
             "tooltip_snapshot_truncated": state["observation"].get("tooltip_triggers_truncated", False),
             "unhovered_tooltip_triggers": max(0, state["observation"].get("tooltip_trigger_total",
                                           len(state["observation"]["tooltip_triggers"]))
                                           - len(state["hover_results"])),
             "hovered_tooltips": len(state["hover_results"]),
             "hover_body_found": sum(bool(h["dynamic_tooltips"]) for h in state["hover_results"])}
            for state in record["states"]],
        "errors": [{"state_index": e["state_index"], "type": e["type"]}
                   for e in record["errors"]],
        "known_capture_gaps": (record.get("pending_state_count", 0) > 0
                               or record.get("depth_limited_state_count", 0) > 0
                               or bool(record["errors"])
                               or any(
                                  st["observation"].get("tooltip_trigger_total",
                                      len(st["observation"]["tooltip_triggers"])) >
                                  len(st["hover_results"])
                                  for st in record["states"]
                               )),
        "full_source_text_in_report": False,
        "real_site_completeness_verified": False,
        "gameplay_meaning_verified": False,
        "automatic_publish_allowed": False,
    }


def controls_to_actions(observation: dict, path: list[dict]) -> list[dict]:
    ancestor_controls = {(step["index"], step["kind"]) for step in path}
    result = []
    for c in observation["controls"]:
        if (c["index"], c["kind"]) in ancestor_controls:
            continue
        if c["kind"] == "select":
            for option in c["options"]:
                if option["value"] != c["selected_value"]:
                    result.append({"index": c["index"], "kind": "select", "dom_id": c.get("id"), "value": option["value"]})
        elif c["kind"] in {"radio", "checkbox"}:
            if not c["checked"]:
                result.append({"index": c["index"], "kind": c["kind"], "dom_id": c.get("id")})
        elif c["kind"] in {"tab", "summary"}:
            # Strictly only controlled tabs or HTML disclosure summaries, never
            # arbitrary page buttons with potential non-navigation side effects.
            if c["kind"] == "summary" or c["target"] or c["selected"] is not None:
                if c["selected"] != "true" and c["expanded"] != "true":
                    result.append({"index": c["index"], "kind": c["kind"], "dom_id": c.get("id")})
    return result


def _perform(page, action: dict) -> None:
    # Prefer stable ids: expanding an ancestor may insert new controls before it.
    dom_id = action.get("dom_id")
    if dom_id:
        item = page.locator('[id=' + json.dumps(dom_id) + ']')
        if item.count() != 1:
            raise RuntimeError("Control stable id is not uniquely present")
    else:
        item = page.locator(CONTROL_SELECTOR).nth(action["index"])
    kind = action["kind"]
    if kind == "select":
        item.select_option(value=action["value"], timeout=2000)
    elif kind in ("checkbox", "radio"):
        item.check(timeout=2000)
    else:
        item.click(timeout=2000)
    page.wait_for_timeout(75)


def _hover(page, max_tips: int) -> list[dict]:
    observed = page.evaluate(OBSERVE)["tooltip_triggers"]
    result = []
    for trigger in observed[:max_tips]:
        try:
            dom_id = trigger.get("id")
            if dom_id:
                target = page.locator('[id=' + json.dumps(dom_id) + ']')
                if target.count() != 1:
                    raise RuntimeError("Tooltip stable id not unique")
            elif trigger.get("css_path"):
                target = page.locator(trigger["css_path"])
                if target.count() != 1:
                    raise RuntimeError("Tooltip DOM path no longer uniquely present")
            else:
                target = page.locator(TOOLTIP_SELECTOR).nth(trigger["index"])
            target.hover(timeout=1200)
            page.wait_for_timeout(40)
            overlays = page.evaluate(OBSERVE)["dynamic_tooltips"]
            result.append({"trigger_index": trigger["index"],
                           "trigger": trigger,
                           "dynamic_tooltips": overlays})
        except Exception as exc:
            result.append({"trigger_index": trigger["index"], "trigger": trigger,
                           "dynamic_tooltips": [], "error_type": type(exc).__name__})
    return result


def capture(page, max_states: int = 24, max_depth: int = 3,
            max_tooltips_per_state: int = 30, validate_state=None) -> dict:
    if max_states < 1 or max_states > 150 or max_depth < 0 or max_depth > 8 or max_tooltips_per_state < 0 or max_tooltips_per_state > 150:
        raise ValueError("Out-of-range capture limits")
    html = page.content()
    if len(html.encode("utf-8")) > MAX_HTML:
        raise ValueError("HTML input limit exceeded")
    result = {
        "schema_version": "live-dom-private-observation-v1",
        "source_url": page.url,
        "source_sha256": hashlib.sha256(html.encode("utf-8")).hexdigest(),
        "states": [], "errors": [], "pending_state_count": 0,
        "depth_limited_state_count": 0,
    }
    queue = [[]]
    seen = set()
    while queue and len(result["states"]) < max_states:
        path = queue.pop(0)
        signature = json.dumps(path, sort_keys=True)
        if signature in seen:
            continue
        seen.add(signature)
        try:
            page.reload(wait_until="domcontentloaded", timeout=12000)
            page.wait_for_timeout(80)
            for step in path:
                _perform(page, step)
                if page.url != result["source_url"]:
                    raise RuntimeError("Controlled element navigated away from the authorized source")
            # Optional caller-supplied guide identity/patch check. This runs
            # BEFORE a state's body or tooltip text enters private evidence.
            # Invalid states are recorded as capture errors, not mixed into
            # an otherwise valid source packet.
            if validate_state is not None:
                validate_state(page)
            observation = page.evaluate(OBSERVE)
            hovers = _hover(page, max_tooltips_per_state)
            observation["body"] = observation["body"][:MAX_TEXT]
            result["states"].append(
                {"path": path, "observation": observation, "hover_results": hovers}
            )
            potential = controls_to_actions(observation, path)
            if len(path) < max_depth:
                for action in potential:
                    queue.append(path + [action])
            elif potential:
                result["depth_limited_state_count"] += 1
        except Exception as exc:
            result["errors"].append(
                {"state_index": len(result["states"]), "type": type(exc).__name__}
            )
    result["pending_state_count"] = len(queue)
    # Private only: identifies unvisited branches for the source coverage audit.
    result["pending_paths"] = queue[:500]
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, help="Local synthetic or authorized saved HTML")
    parser.add_argument("--url", help="Explicitly authorized HTTPS page")
    parser.add_argument("--allow-remote", action="store_true")
    parser.add_argument("--private-output", type=Path, required=True)
    parser.add_argument("--audit-output", type=Path, required=True)
    parser.add_argument("--max-states", type=int, default=24)
    parser.add_argument("--max-depth", type=int, default=3)
    options = parser.parse_args(argv)
    if bool(options.html) == bool(options.url):
        parser.error("Specify exactly one of --html and --url")
    if options.url:
        url = urlparse(options.url)
        if not options.allow_remote or url.scheme != "https" or not url.hostname:
            parser.error("Remote pages require explicit --allow-remote and HTTPS")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SystemExit("Optional Playwright dependency is not installed") from exc
    with sync_playwright() as driver:
        browser = driver.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            target = options.url or options.html.absolute().as_uri()
            page.goto(target, wait_until="domcontentloaded", timeout=20000)
            output = capture(page, options.max_states, options.max_depth)
        finally:
            browser.close()
    options.private_output.parent.mkdir(parents=True, exist_ok=True)
    options.private_output.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    # Only this metadata report may be exported to public CI; full text private.
    options.audit_output.parent.mkdir(parents=True, exist_ok=True)
    options.audit_output.write_text(json.dumps(summarize(output), indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
