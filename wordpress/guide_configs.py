"""Guide-cluster configuration registry (Roadie Labs).

Ported from gravel-race-automation. Each guide owns its URL namespace,
capture behavior, analytics namespace, and conversion surfaces. The road
guide is worker-first from day one — there is no grandfathered FormSubmit
gate in this repo.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Mapping

from generate_neo_brutalist import COACHING_URL, TRAINING_PLANS_URL


REPO_ROOT = Path(__file__).parent.parent
GUIDE_DIR = REPO_ROOT / "guide"
OUTPUT_ROOT = Path(__file__).parent / "output"
LEAD_INTAKE_WORKER_URL = "https://fueling-lead-intake.gravelgodcoaching.workers.dev"


class GateEndpointMode(str, Enum):
    """Submission behavior for a chapter gate."""

    FORM_SUBMIT = "formsubmit"
    WORKER_FIRST = "worker_first"


@dataclass(frozen=True)
class GateFormConfig:
    """Gate form copy and delivery settings.

    ``WORKER_FIRST`` posts to the shared lead-intake worker in JavaScript,
    unlocks immediately, and leaves the configured FormSubmit endpoint
    available only as a no-JS fallback. ``worker_brand_value`` is mandatory
    for non-gravel brands: without ``brand`` in the payload the worker
    enrolls the lead in gravel sequences.
    """

    subject_label: str
    worker_source_value: str
    endpoint_mode: GateEndpointMode
    worker_brand_value: str = ""
    worker_endpoint: str = LEAD_INTAKE_WORKER_URL
    formsubmit_endpoint: str = "https://formsubmit.co/gravelgodcoaching@gmail.com"


@dataclass(frozen=True)
class CtaSetConfig:
    """CTA blocks to render and their canonical targets."""

    pillar_blocks: tuple[str, ...]
    finale_blocks: tuple[str, ...]
    targets: Mapping[str, str]


@dataclass(frozen=True)
class GuideConfig:
    """All generator-owned settings for one independently deployable guide."""

    key: str
    content_path: Path
    output_dir: Path
    url_base: str
    chapter_meta: Mapping[str, Mapping[str, str]]
    ga4_event_label_prefix: str
    local_storage_key_prefix: str
    gate_form: GateFormConfig
    cta_set: CtaSetConfig
    glossary_source: Path
    guide_label: str = "Training Guide"
    include_configurator: bool = False
    date_published: str = "2026-08-05"
    date_modified: str = ""


ROAD_CHAPTER_META = {
    "what-is-road-racing": {
        "title_suffix": "What Is Road Racing? — Fondos, Sportives & Centuries",
        "description": "What road racing actually is: gran fondos, sportives, centuries, and what each demands. Free chapter from the Roadie Labs Training Guide.",
    },
    "choosing-your-race": {
        "title_suffix": "How to Choose a Road Race — Selection Guide",
        "description": "How to choose the right road race: scored dimensions, tier rankings, runway math, and honest fit. Free chapter from the Roadie Labs Training Guide.",
    },
    "building-the-engine": {
        "title_suffix": "Road Race Training Fundamentals",
        "description": "Training fundamentals for road racing: zones, FTP, periodization, and building the aerobic engine that decides your day.",
    },
    "workout-execution": {
        "title_suffix": "Road Workout Execution — Interval Training Guide",
        "description": "How to execute road-specific workouts: threshold and VO2 intervals, group rides with a purpose, and quality control.",
    },
    "fueling-for-the-distance": {
        "title_suffix": "Road Race Nutrition & Fueling Strategy",
        "description": "Complete road race fueling guide: carbohydrate targets, hydration, eating in a pack, and how to avoid the bonk.",
    },
    "pack-skills-and-tactics": {
        "title_suffix": "Pack Skills & Race Craft for Road Racing",
        "description": "Pack riding and race craft: drafting, positioning, pacelines, cornering in a group, and the skills that buy free speed.",
    },
    "race-week": {
        "title_suffix": "Race Week Protocol — Road Race Preparation",
        "description": "Race week for road events: taper, equipment checks, carb loading, start-pen logistics, and race-morning routine.",
    },
    "after-the-finish": {
        "title_suffix": "Post-Race Recovery & What's Next",
        "description": "Post-race recovery for road riders: immediate recovery, the debrief, training restart timeline, and picking the next target.",
    },
}


ROAD_GUIDE = GuideConfig(
    key="road",
    content_path=GUIDE_DIR / "road-guide-content.json",
    output_dir=OUTPUT_ROOT / "guide",
    url_base="/guide/",
    chapter_meta=ROAD_CHAPTER_META,
    ga4_event_label_prefix="guide",
    local_storage_key_prefix="rl_guide",
    gate_form=GateFormConfig(
        subject_label="Guide Unlock",
        worker_source_value="training_guide",
        endpoint_mode=GateEndpointMode.WORKER_FIRST,
        worker_brand_value="roadielabs",
    ),
    cta_set=CtaSetConfig(
        pillar_blocks=("training_plans", "coaching"),
        finale_blocks=("training_plans", "coaching"),
        targets={
            "training_plans": TRAINING_PLANS_URL,
            "coaching": COACHING_URL,
        },
    ),
    glossary_source=GUIDE_DIR / "road-guide-content.json",
    guide_label="Road Training Guide",
    date_published="2026-08-05",
)


GUIDE_CONFIGS = {config.key: config for config in (ROAD_GUIDE,)}
