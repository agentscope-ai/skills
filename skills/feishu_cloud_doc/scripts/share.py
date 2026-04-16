#!/usr/bin/env python3
"""Manage permissions for a Feishu cloud document.

Usage:
    python scripts/share.py --workspace-dir DIR --token TOKEN --type docx --member-type openid --member-id ou_xxx --perm view
    python scripts/share.py --workspace-dir DIR --token TOKEN --type docx --public --link-access tenant_readable
    python scripts/share.py --workspace-dir DIR --token TOKEN --type docx --transfer --member-type openid --member-id ou_xxx

Supported --type values: docx, sheet, bitable, wiki, file, folder
Supported --perm values: view, edit, full_access
Supported --link-access values: tenant_readable, tenant_editable, anyone_readable, anyone_editable
"""

from __future__ import annotations

import argparse
import json
import sys

import httpx

from feishu_auth import auth_headers, get_base_url, init_workspace


def add_member(
    token: str,
    doc_type: str,
    member_type: str,
    member_id: str,
    perm: str = "view",
) -> dict:
    """Add a collaborator to a document."""
    base = get_base_url()
    url = (
        f"{base}/open-apis/drive/v1/permissions/{token}/members"
        f"?type={doc_type}&need_notification=false"
    )
    body = {
        "member_type": member_type,
        "member_id": member_id,
        "perm": perm,
    }
    resp = httpx.post(url, headers=auth_headers(), json=body, timeout=30)
    data = resp.json()

    if data.get("code") != 0:
        return {
            "success": False,
            "error": data.get("msg", "unknown error"),
            "code": data.get("code"),
        }

    return {
        "success": True,
        "token": token,
        "member_type": member_type,
        "member_id": member_id,
        "perm": perm,
    }


def set_public_access(
    token: str,
    doc_type: str,
    link_share_entity: str = "tenant_readable",
) -> dict:
    """Set the link sharing permission for a document."""
    base = get_base_url()
    url = (
        f"{base}/open-apis/drive/v1/permissions/{token}/public"
        f"?type={doc_type}"
    )
    body = {
        "external_access_entity": "open",
        "security_entity": "anyone_can_view",
        "comment_entity": "anyone_can_view",
        "share_entity": "anyone",
        "link_share_entity": link_share_entity,
    }
    resp = httpx.patch(url, headers=auth_headers(), json=body, timeout=30)
    data = resp.json()

    if data.get("code") != 0:
        return {
            "success": False,
            "error": data.get("msg", "unknown error"),
            "code": data.get("code"),
        }

    return {
        "success": True,
        "token": token,
        "link_share_entity": link_share_entity,
    }


def transfer_owner(
    token: str,
    doc_type: str,
    member_type: str,
    member_id: str,
) -> dict:
    """Transfer document ownership to another user.

    The caller (app) must be the current owner of the document.
    After transfer, the new owner has full control and the app
    becomes a regular collaborator.
    """
    base = get_base_url()
    url = (
        f"{base}/open-apis/drive/v1/permissions/{token}/members/transfer_owner"
        f"?type={doc_type}&need_notification=true"
    )
    body = {
        "member_type": member_type,
        "member_id": member_id,
    }
    resp = httpx.post(url, headers=auth_headers(), json=body, timeout=30)
    data = resp.json()

    if data.get("code") != 0:
        return {
            "success": False,
            "error": data.get("msg", "unknown error"),
            "code": data.get("code"),
        }

    return {
        "success": True,
        "token": token,
        "new_owner_type": member_type,
        "new_owner_id": member_id,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage Feishu document permissions")
    parser.add_argument("--token", required=True, help="Document/file token")
    parser.add_argument(
        "--type",
        required=True,
        choices=["docx", "sheet", "bitable", "wiki", "file", "folder"],
        help="Document type",
    )
    parser.add_argument("--member-type", default="", help="Member type: openid, userid, email, chat_id, department_id")
    parser.add_argument("--member-id", default="", help="Member ID")
    parser.add_argument("--perm", default="view", choices=["view", "edit", "full_access"], help="Permission level")
    parser.add_argument("--public", action="store_true", help="Set link sharing instead of adding member")
    parser.add_argument(
        "--link-access",
        default="tenant_readable",
        choices=["tenant_readable", "tenant_editable", "anyone_readable", "anyone_editable"],
        help="Link sharing access level",
    )
    parser.add_argument("--transfer", action="store_true", help="Transfer ownership to the specified member")
    parser.add_argument("--workspace-dir", required=True, help="Workspace directory containing agent.json")
    args = parser.parse_args()
    init_workspace(args.workspace_dir)

    if args.transfer:
        if not args.member_type or not args.member_id:
            print(json.dumps({"success": False, "error": "--member-type and --member-id required for transfer"}))
            sys.exit(1)
        result = transfer_owner(args.token, args.type, args.member_type, args.member_id)
    elif args.public:
        result = set_public_access(args.token, args.type, args.link_access)
    else:
        if not args.member_type or not args.member_id:
            print(json.dumps({"success": False, "error": "--member-type and --member-id required"}))
            sys.exit(1)
        result = add_member(args.token, args.type, args.member_type, args.member_id, args.perm)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result.get("success"):
        sys.exit(1)


if __name__ == "__main__":
    main()
