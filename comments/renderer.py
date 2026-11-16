from review.schema import Finding
from core.config import BOT_MARKER


def _render_suggestion(finding: Finding) -> str:
    replacement = finding.suggested_replacement

    if not replacement:
        return ""

    return f"\n\n```suggestion\n{replacement}\n```"


def render_inline_comment(finding: Finding) -> str:
    parts = [
        f"**{finding.severity.value.capitalize()} — {finding.title}**",
        "",
        finding.explanation,
    ]

    if finding.evidence:
        parts.extend(
            [
                "",
                "**Evidence:**",
                *[f"- {item}" for item in finding.evidence],
            ]
        )

    suggestion = _render_suggestion(finding)

    if suggestion:
        parts.append(suggestion)

    # Used to identify this finding in future review runs.
    parts.extend(
        [
            "",
            f"<!-- pr-review-bot:fingerprint={finding.fingerprint} -->",
        ]
    )

    return "\n".join(parts)


def render_summary(findings: list[Finding]) -> str:
    if not findings:
        return f"{BOT_MARKER}\n" "## PR Review\n\n" "No findings detected."

    counts = {}

    for finding in findings:
        severity = finding.severity.value
        counts[severity] = counts.get(severity, 0) + 1

    lines = [
        BOT_MARKER,
        "## PR Review",
        "",
        f"Found **{len(findings)} issue(s)**.",
        "",
        "### Summary",
        "",
    ]

    for severity in ["severe", "high", "medium", "low", "nit"]:
        count = counts.get(severity, 0)

        if count:
            lines.append(f"- **{severity.capitalize()}:** {count}")

    lines.extend(["", "### Findings", ""])

    for index, finding in enumerate(findings, start=1):
        lines.extend(
            [
                f"#### {index}. [{finding.severity.value.capitalize()}] "
                f"{finding.title}",
                "",
                f"**File:** `{finding.path}` "
                f"(lines {finding.start_line}-{finding.end_line})",
                "",
                finding.explanation,
                "",
            ]
        )

    return "\n".join(lines)
