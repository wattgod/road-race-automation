#!/usr/bin/env python3
"""Infographic renderers for guide image blocks — intentionally empty for Roadie Labs.

The gravel repo's guide_infographics.py (2,689 lines) dispatches `image` blocks
with known `asset_id`s to inline SVG/HTML renderers. The road guide content
(guide/road-guide-content.json) deliberately uses no infographic asset_ids —
per docs/specs/roadie-guide-handoff.md §5.2, the module is dead weight until
the content adds infographic blocks.

If road content ever adds an image block with an asset_id, port the matching
renderer from gravel-race-automation/wordpress/guide_infographics.py and
register it here; unknown asset_ids render as nothing (a hole), which is the
failure mode this stub exists to document.
"""

INFOGRAPHIC_RENDERERS: dict = {}
