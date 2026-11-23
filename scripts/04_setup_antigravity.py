#!/usr/bin/env python3
"""Task 04: Configure Google Antigravity (agy) APIs, separated Custom IAM Role (geStandardChatUser), and MCP Allowlist."""

import json
import sys
from pathlib import Path
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT_DIR, api_headers, get_access_token, load_env


def main():
    env = load_env()
    project_id = env["PROJECT_ID"]
    token = get_access_token()

    print(f"[Step 1/3] Ensuring businessaicode.googleapis.com (Google Antigravity API) is enabled on {project_id}...")
    r = requests.post(
        f"https://serviceusage.googleapis.com/v1/projects/{project_id}/services/businessaicode.googleapis.com:enable",
        headers=api_headers(token, project_id),
        json={},
    )
    print(f"  - businessaicode.googleapis.com: {'ENABLED' if r.ok else r.status_code}")

    # Trigger service identity creation via Service Usage generateServiceIdentity (v1beta1)
    si = requests.post(
        f"https://serviceusage.googleapis.com/v1beta1/projects/{project_id}/services/businessaicode.googleapis.com:generateServiceIdentity",
        headers=api_headers(token, project_id),
        json={},
    )
    if si.ok:
        print("  - Verified Antigravity Service Identity (gcp-sa-businessaicode).")

    print("\n[Step 2/3] Building Custom IAM Role 'geStandardChatUser' (GE Web + Canvas allowed, Antigravity blocked)...")
    base_role = requests.get(
        "https://iam.googleapis.com/v1/roles/discoveryengine.agentspaceUser",
        headers=api_headers(token, project_id),
    )
    base_role.raise_for_status()
    all_perms = base_role.json().get("includedPermissions", [])

    # Exclude businessaicode.* (Antigravity) and org/folder-only permissions like resourcemanager.projects.list
    excluded_agy = [p for p in all_perms if p.startswith("businessaicode.")]
    filtered_perms = [
        p for p in all_perms
        if not p.startswith("businessaicode.") and p != "resourcemanager.projects.list"
    ]
    canvas_perms = [p for p in filtered_perms if "immersiveArtifacts" in p]
    print(f"  - Standard agentspaceUser permissions : {len(all_perms)}")
    print(f"  - Removed businessaicode.* permissions : {len(excluded_agy)} ({', '.join(excluded_agy)})")
    print(f"  - Retained Canvas permissions          : {len(canvas_perms)}")

    role_url = f"https://iam.googleapis.com/v1/projects/{project_id}/roles/geStandardChatUser"
    role_spec = {
        "title": "GE Standard Chat User (No Antigravity)",
        "description": "Grants Gemini Enterprise Web App, Search, Agents, and Canvas access while excluding Google Antigravity (businessaicode.*) permissions.",
        "includedPermissions": filtered_perms,
        "stage": "GA",
    }

    existing = requests.get(role_url, headers=api_headers(token, project_id))
    if existing.status_code == 200:
        if existing.json().get("deleted"):
             requests.post(f"{role_url}:undelete", headers=api_headers(token, project_id), json={})
        ur = requests.patch(
            f"{role_url}?updateMask=title,description,includedPermissions,stage",
            headers=api_headers(token, project_id),
            json=role_spec,
        )
        ur.raise_for_status()
        print(f"  [UPDATED] projects/{project_id}/roles/geStandardChatUser ({len(filtered_perms)} permissions)")
    else:
        cr = requests.post(
            f"https://iam.googleapis.com/v1/projects/{project_id}/roles",
            headers=api_headers(token, project_id),
            json={"roleId": "geStandardChatUser", "role": role_spec},
        )
        if not cr.ok:
            raise RuntimeError(f"Create Custom Role failed ({cr.status_code}): {cr.text[:400]}")
        print(f"  [CREATED] projects/{project_id}/roles/geStandardChatUser ({len(filtered_perms)} permissions)")

    print("\n[Step 3/3] Validating Antigravity MCP Allowlist JSON configuration...")
    mcp_path = ROOT_DIR / "agy_workspace" / "configs" / "mcp_allowlist.json"
    mcp_data = json.loads(mcp_path.read_text(encoding="utf-8"))
    assert "mcpServers" in mcp_data, "Invalid MCP allowlist root key"
    print(f"  [OK] Validated {mcp_path.relative_to(ROOT_DIR)}:")
    print(json.dumps(mcp_data, indent=2))
    print("\nPaste the JSON above into GCP Console > Gemini Enterprise > Settings > AI developer tools > Allowed server configuration.")


if __name__ == "__main__":
    main()
