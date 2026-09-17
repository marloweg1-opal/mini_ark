"""HEXSEED project and capability token registry.

Tokens are stable identity handles: a compact way for Mini ARK to know
what something is, what it owns, how it should be routed, and how it may
show up on the user-facing surface.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


REGISTRY_RELATIVE_PATH = Path("config") / "project_tokens.json"

DEFAULT_REGISTRY: dict[str, Any] = {
    "schema_version": 1,
    "doctrine": {
        "summary": "HEXSEED tokens describe identity, capability ownership, routing, safety, and surface customization.",
        "canonical_system_token": "corestone",
        "identity_resolution": {
            "opalstone": "corestone",
        },
        "identity_note": "Opalstone may describe the person/identity; Corestone is the CareBloom expression of the INTEGRATE kernel. Mini ARK/Journey is the connective configuration engine and should not resolve as a Corestone alias.",
        "empty_folder_policy": "Never delete a folder solely because it is empty.",
        "routing_policy": "Files live in their natural canonical home first; specificity is added through representations such as shortcuts, manifests, tags, and project views.",
        "ambient_congruence_policy": "Corestone/HEXSEED should continuously pursue user-computer congruence by the least resistant, least disturbing path available. Always observe; auto-apply only safe, reversible, high-confidence, low-cost maintenance; throttle during active foreground or heavy compute; record receipts and preserve rollback for autonomous changes; ask only for ambiguity, judgment, destructive action, unclear ownership, or expensive/disruptive work.",
        "resource_doctrine": "Corestone is always aware, not always busy. Foreground responsiveness wins; heavy compute makes stewardship throttle or sleep; idle and low-load periods allow deeper maintenance.",
        "mutation_policy": "Detect and propose first; execute only through approved, reversible operations.",
        "prompt_policy": "Do not create routine 'run organizer' prompts or buttons for housekeeping. Prompts are for real judgment, not ordinary maintenance.",
        "auto_apply_policy": [
            "deterministic naming normalization",
            "index and manifest updates",
            "verified routing with unambiguous destinations",
            "broken-reference repair where destination is unambiguous",
            "non-destructive organizational maintenance",
            "report generation",
            "safe metadata normalization",
        ],
        "do_not_auto_apply_policy": [
            "deletion",
            "folder deletion",
            "ambiguous rename",
            "semantic merges",
            "system or app-managed path changes",
            "destructive dedupe",
            "high-cost scans during active workload",
            "changes with unclear ownership or destination",
        ],
        "visual_identity_policy": "HEXSEED_v4.ico is the selected canonical HEXSEED identity icon. Expression profiles may provide profile-specific icons, but the foundation icon remains the stable HEXSEED mark unless explicitly changed.",
    },
    "visual_identity": {
        "selected_hexseed_icon": "C:\\HEXSEED\\10_ASSETS\\HEXSEED_ICONS\\ICO\\HEXSEED_v4.ico",
        "selection_note": "Chosen for practical icon readability and stable HEXSEED identity: outer hex, central seed/crystal, and clear silhouette at small sizes.",
        "selected_mini_ark_icon": "C:\\HEXSEED\\10_ASSETS\\HEXSEED_ICONS\\ICO\\mini_ark.ico",
        "future_journey_icon": "C:\\HEXSEED\\10_ASSETS\\HEXSEED_ICONS\\ICO\\journey.ico",
        "mini_ark_journey_icon_policy": "Use mini_ark.ico for the active C:\\mini_ark implementation. Hold journey.ico for the future Journey identity and do not apply it until the deliberate Journey migration is approved.",
        "selected_carebloomos_app_icon_source": "C:\\HEXSEED\\10_ASSETS\\HEXSEED_ICONS\\ICO\\cAREBLOOM_BABY.png",
        "selected_carebloomos_app_icon": "C:\\HEXSEED\\10_ASSETS\\HEXSEED_ICONS\\ICO\\cAREBLOOM_BABY.ico",
        "selected_carebloomos_app_icon_note": "Selected as the one CareBloomOS application icon. The bloom-within-bloom mark has the strongest standalone silhouette, says CareBloom without requiring a secondary glyph, communicates the recursive multi-domain system, and avoids over-specifying what the OS is currently doing. The PNG is the source art; the ICO is the Windows/application icon artifact.",
        "carebloomos_icon_audition": {
            "locked_choice_source": "C:\\HEXSEED\\10_ASSETS\\HEXSEED_ICONS\\ICO\\cAREBLOOM_BABY.png",
            "locked_choice": "C:\\HEXSEED\\10_ASSETS\\HEXSEED_ICONS\\ICO\\cAREBLOOM_BABY.ico",
            "nursery_assets": [
                "C:\\HEXSEED\\10_ASSETS\\HEXSEED_ICONS\\ICO\\CareBloomOS.ico",
                "C:\\HEXSEED\\10_ASSETS\\HEXSEED_ICONS\\ICO\\CareBloomOS_v1.ico",
                "C:\\HEXSEED\\10_ASSETS\\HEXSEED_ICONS\\ICO\\CareBloomOS_v2.ico",
            ],
            "nursery_policy": "Hold the other candidates briefly for genuine reuse opportunities. Do not build a permanent hierarchy around them; prune them if no real use appears.",
        },
        "carebloom_stone_icons": {
            "moonstone": "C:\\HEXSEED\\10_ASSETS\\HEXSEED_ICONS\\ICO\\moonstone.ico",
            "cloverstone": "C:\\HEXSEED\\10_ASSETS\\HEXSEED_ICONS\\ICO\\cloverstone.ico",
            "heartstone": "C:\\HEXSEED\\10_ASSETS\\HEXSEED_ICONS\\ICO\\heartstone.ico",
            "cloudstone": "C:\\HEXSEED\\10_ASSETS\\HEXSEED_ICONS\\ICO\\cloudstone.ico",
            "wishstone": "C:\\HEXSEED\\10_ASSETS\\HEXSEED_ICONS\\ICO\\wishstone.ico",
            "musicstone": "C:\\HEXSEED\\10_ASSETS\\HEXSEED_ICONS\\ICO\\musicstone.ico",
        },
        "carebloom_identity_policy": "Use cAREBLOOM_BABY.png as the selected CareBloomOS application icon. The other CareBloomOS icon candidates remain nursery assets only, not a canonical semantic hierarchy.",
        "stone_icon_policy": "Folders or surfaces explicitly named for a CareBloom stone may use that stone's canonical icon. Filesystem application must be previewed first and should write only presentation metadata such as desktop.ini unless explicitly approved.",
    },
    "tokens": {
        "corestone": {
            "display_name": "Corestone",
            "type": "system",
            "aliases": ["opalstone"],
            "owns": [
                "computer_user_congruency",
                "capability_registry",
                "stewardship_surface",
                "audit",
                "rollback",
            ],
            "routes": {},
            "representations": {
                "kernel": "integrate",
                "expression_profile": "carebloom",
                "role": "carebloom_integrator_expression",
            },
            "customization": {
                "surface_label": "Corestone",
                "icon": None,
                "accent": "#8ee36f",
                "wallpaper": None,
            },
        },
        "journey": {
            "display_name": "Journey",
            "type": "configuration_engine",
            "aliases": ["mini_ark", "mini ark", "miniark", "adaptive local orchestration layer"],
            "owns": [
                "configuration_engine",
                "expression_profile_selection",
                "functional_kernel_translation",
                "navigator_surface",
                "continuity_across_manifestations",
            ],
            "routes": {
                "home": "C:\\mini_ark",
                "docs": "C:\\mini_ark\\docs",
                "ledger": "C:\\mini_ark\\ark.sqlite",
            },
            "representations": {
                "implementation": "Mini ARK",
                "canonical_working_tree": "C:\\mini_ark",
                "role": "connective_orchestration_layer",
                "status": "active_implementation_name_future_identity_planning",
            },
            "customization": {
                "surface_label": "Journey",
                "icon": "C:\\HEXSEED\\10_ASSETS\\HEXSEED_ICONS\\ICO\\mini_ark.ico",
                "future_icon": "C:\\HEXSEED\\10_ASSETS\\HEXSEED_ICONS\\ICO\\journey.ico",
                "accent": "#7fd9d2",
            },
        },
        "wishstone": {
            "display_name": "Wishstone",
            "type": "stone",
            "aliases": ["asset ark", "asset_ark", "wishstone intake"],
            "owns": [
                "acquisition",
                "asset_intake",
                "asset_routing",
                "dedupe",
                "provenance",
                "project_representations",
            ],
            "routes": {
                "inbox": "C:\\mini_ark\\asset_pipeline\\inbox",
                "outbox": "C:\\mini_ark\\asset_pipeline\\outbox",
                "approved": "C:\\mini_ark\\asset_pipeline\\approved",
                "library": "C:\\mini_ark\\asset_pipeline\\library",
            },
            "representations": {
                "canonical": "C:\\mini_ark\\asset_pipeline",
                "surface": "Tools > Wishstone Intake",
                "role": "asset_acquisition_and_routing",
            },
            "customization": {
                "surface_label": "Wishstone Intake",
                "icon": "C:\\HEXSEED\\10_ASSETS\\HEXSEED_ICONS\\ICO\\wishstone.ico",
                "accent": "#f4c95d",
                "default_group_mode": "keep_separate",
            },
        },
        "cloverstone": {
            "display_name": "Cloverstone",
            "type": "stone",
            "aliases": ["clover", "clover care"],
            "owns": ["naming", "normalization", "maintenance", "folder_hygiene", "cadence", "drift_reports"],
            "routes": {},
            "representations": {},
            "customization": {"icon": "C:\\HEXSEED\\10_ASSETS\\HEXSEED_ICONS\\ICO\\cloverstone.ico", "accent": "#58d46f"},
        },
        "moonstone": {
            "display_name": "Moonstone",
            "type": "stone",
            "aliases": ["moon", "hidden layer"],
            "owns": ["hidden_state", "system_state", "restoration", "privacy", "history"],
            "routes": {},
            "representations": {},
            "customization": {"icon": "C:\\HEXSEED\\10_ASSETS\\HEXSEED_ICONS\\ICO\\moonstone.ico", "accent": "#9bb7ff"},
        },
        "heartstone": {
            "display_name": "Heartstone",
            "type": "stone",
            "aliases": ["heart", "protection layer"],
            "owns": ["protection", "treatment", "quarantine", "containment", "remediation"],
            "routes": {},
            "representations": {},
            "customization": {"icon": "C:\\HEXSEED\\10_ASSETS\\HEXSEED_ICONS\\ICO\\heartstone.ico", "accent": "#ff7fa1"},
        },
        "cloudstone": {
            "display_name": "Cloudstone",
            "type": "stone",
            "aliases": ["cloud", "atmosphere layer", "environment layer"],
            "owns": ["environment", "atmosphere", "comfort", "conditions", "regulation"],
            "routes": {},
            "representations": {},
            "customization": {"icon": "C:\\HEXSEED\\10_ASSETS\\HEXSEED_ICONS\\ICO\\cloudstone.ico", "accent": "#4db5ff"},
        },
        "musicstone": {
            "display_name": "Musicstone",
            "type": "stone",
            "aliases": ["music", "rhythm layer", "audio layer"],
            "owns": ["audio", "rhythm", "resonance", "communication", "synchronization"],
            "routes": {},
            "representations": {},
            "customization": {"icon": "C:\\HEXSEED\\10_ASSETS\\HEXSEED_ICONS\\ICO\\musicstone.ico", "accent": "#ff6b57"},
        },
        "carebloomos": {
            "display_name": "CareBloomOS",
            "type": "project",
            "aliases": ["carebloom", "carebloom os"],
            "owns": ["carestone_widgets", "rainmeter_skins", "wallpaper_engine_assets", "care_rails"],
            "routes": {
                "project_root": "R:\\Projects\\CareBloomOS",
                "active_source": "R:\\Projects\\CareBloomOS\\01_Active_Source\\CareBloomOS",
                "media_root": "R:\\Media\\CareBloomOS",
            },
            "representations": {
                "canonical": "R:\\Projects\\CareBloomOS",
                "active_source": "R:\\Projects\\CareBloomOS\\01_Active_Source\\CareBloomOS",
                "media": "R:\\Media\\CareBloomOS",
                "surface": "CareBloomOS project views may reference assets without becoming the source of truth",
                "role": "carestone_project",
            },
            "customization": {
                "surface_label": "CareBloomOS",
                "icon": "C:\\HEXSEED\\10_ASSETS\\HEXSEED_ICONS\\ICO\\cAREBLOOM_BABY.ico",
                "accent": "#c8b6ff",
                "manifestation_profile": "carestone",
            },
        },
    },
    "reserved_roots": [
        "C:\\mini_ark\\asset_pipeline\\inbox",
        "C:\\mini_ark\\asset_pipeline\\inbox\\archive",
        "C:\\mini_ark\\asset_pipeline\\outbox",
        "C:\\mini_ark\\asset_pipeline\\approved",
        "C:\\mini_ark\\asset_pipeline\\library",
        "C:\\mini_ark\\asset_pipeline\\recipes",
        "C:\\mini_ark\\asset_pipeline\\logs",
        "R:\\HEXSEED",
        "R:\\ark_quarantine",
        "R:\\.System_Records",
    ],
}


def registry_path(root: Path) -> Path:
    return root / REGISTRY_RELATIVE_PATH


def ensure_token_registry(root: Path) -> dict[str, Any]:
    path = registry_path(root)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        write_token_registry(root, DEFAULT_REGISTRY)
    registry = load_token_registry(root)
    validate_token_registry(registry)
    return registry


def load_token_registry(root: Path) -> dict[str, Any]:
    path = registry_path(root)
    with path.open("r", encoding="utf-8") as handle:
        registry = json.load(handle)
    validate_token_registry(registry)
    return registry


def write_token_registry(root: Path, registry: dict[str, Any]) -> None:
    validate_token_registry(registry)
    path = registry_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(registry, handle, indent=2)
        handle.write("\n")


def validate_token_registry(registry: dict[str, Any]) -> None:
    if not isinstance(registry, dict):
        raise ValueError("Token registry must be a JSON object.")
    if registry.get("schema_version") != 1:
        raise ValueError("Token registry schema_version must be 1.")
    tokens = registry.get("tokens")
    if not isinstance(tokens, dict) or not tokens:
        raise ValueError("Token registry must contain a non-empty tokens object.")
    for token_id, token in tokens.items():
        if not isinstance(token_id, str) or not token_id.strip():
            raise ValueError("Token ids must be non-empty strings.")
        if not isinstance(token, dict):
            raise ValueError(f"Token {token_id!r} must be an object.")
        for field in ("display_name", "type", "aliases", "owns", "routes", "customization"):
            if field not in token:
                raise ValueError(f"Token {token_id!r} is missing {field!r}.")
        if not isinstance(token["aliases"], list):
            raise ValueError(f"Token {token_id!r} aliases must be a list.")
        if not isinstance(token["owns"], list):
            raise ValueError(f"Token {token_id!r} owns must be a list.")


def resolve_token(registry: dict[str, Any], value: str) -> tuple[str, dict[str, Any]] | None:
    needle = value.strip().lower()
    if not needle:
        return None
    for token_id, token in registry["tokens"].items():
        candidates = [token_id, token["display_name"], *token.get("aliases", [])]
        if needle in {str(candidate).strip().lower() for candidate in candidates}:
            return token_id, deepcopy(token)
    return None


def token_summary(registry: dict[str, Any]) -> dict[str, Any]:
    validate_token_registry(registry)
    tokens = registry["tokens"]
    return {
        "schema_version": registry["schema_version"],
        "token_count": len(tokens),
        "tokens": [
            {
                "id": token_id,
                "display_name": token["display_name"],
                "type": token["type"],
                "aliases": token.get("aliases", []),
                "owns": token.get("owns", []),
                "routes": token.get("routes", {}),
                "representations": token.get("representations", {}),
                "customization": token.get("customization", {}),
            }
            for token_id, token in sorted(tokens.items())
        ],
        "reserved_roots": registry.get("reserved_roots", []),
        "policies": registry.get("doctrine", {}),
    }


def route_summary(registry: dict[str, Any]) -> dict[str, Any]:
    validate_token_registry(registry)
    routed_tokens = []
    for token_id, token in sorted(registry["tokens"].items()):
        routes = token.get("routes", {})
        representations = token.get("representations", {})
        if routes or representations:
            routed_tokens.append(
                {
                    "id": token_id,
                    "display_name": token["display_name"],
                    "type": token["type"],
                    "routes": routes,
                    "representations": representations,
                }
            )
    return {
        "schema_version": registry["schema_version"],
        "routed_token_count": len(routed_tokens),
        "tokens": routed_tokens,
        "rule": "Canonical roots are the source of truth; representations are useful views, shortcuts, manifests, or surfaces.",
        "routing_policy": registry.get("doctrine", {}).get("routing_policy", ""),
    }
