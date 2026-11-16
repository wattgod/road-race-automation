"""Tests for the Roadie Labs coaching page + coaching apply page generators.

Coaching page rebuilt 2026-11-15 as "Field Notes", matching the Gravel God
sibling page Matti picked: hero + ID card (real photo crossfading to the
v6.7 character in the Roadie kit) -> fit -> terms (what you get) -> week ->
how-it-works -> tiers (ledger + 3-question picker) -> faq -> final-cta.
This suite describes the page as it ships now.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

# Add wordpress/ to path so we can import the generators
WORDPRESS_DIR = Path(__file__).parent.parent / "wordpress"
sys.path.insert(0, str(WORDPRESS_DIR))

from generate_coaching import (
    ID_ROWS,
    IMAGES,
    IMG_OUTPUT_SUBDIR,
    IMG_SRC_DIR,
    LEDGER_GROUPS,
    PICKER_QUESTIONS,
    QUESTIONNAIRE_URL,
    TIER_BLURBS,
    TIERS,
    build_nav,
    build_hero,
    build_id_card,
    build_terms,
    build_week,
    build_how_it_works,
    build_tiers,
    build_fit_check,
    build_honest_check,
    build_faq,
    build_application_close,
    build_footer,
    build_mobile_sticky_cta,
    build_coaching_css,
    build_coaching_js,
    build_jsonld,
    generate_coaching_page,
    write_coaching_images,
)
from generate_coaching_apply import (
    COACHING_INTAKE_WORKER_URL,
    build_apply_css,
    build_apply_js,
    build_tier_selector,
    generate_apply_page,
)
from generate_neo_brutalist import SITE_BASE_URL, write_shared_assets

OUTPUT_DIR = WORDPRESS_DIR / "output"
SECTION_IDS = ("hero", "fit", "terms", "week", "how-it-works", "tiers", "faq", "final-cta")


# ── Fixtures ─────────────────────────────────────────────────

# ── Fixtures ─────────────────────────────────────────────────


@pytest.fixture(scope="module")
def coaching_html():
    return generate_coaching_page()


@pytest.fixture(scope="module")
def coaching_css():
    return build_coaching_css()


@pytest.fixture(scope="module")
def coaching_js():
    return build_coaching_js()


@pytest.fixture(scope="module")
def apply_html():
    return generate_apply_page()


@pytest.fixture(scope="module")
def apply_js():
    return build_apply_js()


# ── Page Generation ──────────────────────────────────────────


class TestPageGeneration:
    def test_returns_html(self, coaching_html):
        assert isinstance(coaching_html, str)
        assert "<!DOCTYPE html>" in coaching_html

    def test_has_canonical(self, coaching_html):
        assert 'rel="canonical"' in coaching_html
        assert "/coaching/" in coaching_html

    def test_has_ga4(self, coaching_html):
        assert "G-WQ7W8XN11N" in coaching_html
        assert "googletagmanager.com" in coaching_html

    def test_has_ab_snippet(self, coaching_html):
        assert "dataLayer" in coaching_html

    def test_has_jsonld(self, coaching_html):
        assert 'application/ld+json' in coaching_html
        assert '"@type":"WebPage"' in coaching_html
        assert '"@type":"Service"' in coaching_html

    def test_has_meta_robots(self, coaching_html):
        assert 'name="robots"' in coaching_html
        assert 'content="index, follow"' in coaching_html

    def test_has_meta_description(self, coaching_html):
        assert 'name="description"' in coaching_html

    def test_has_og_tags(self, coaching_html):
        assert 'og:title' in coaching_html
        assert 'og:description' in coaching_html

    def test_has_title(self, coaching_html):
        assert "<title>" in coaching_html
        assert "Coaching" in coaching_html


# ── Nav ──────────────────────────────────────────────────────


class TestNav:
    def test_nav_links(self, coaching_html):
        assert "/coaching/" in coaching_html
        assert "/about/" in coaching_html
        assert ">SERVICES</a>" in coaching_html
        assert ">ABOUT</a>" in coaching_html

    def test_breadcrumb(self, coaching_html):
        assert "rl-breadcrumb" in coaching_html
        assert "Coaching" in coaching_html

    def test_current_page_marker(self, coaching_html):
        assert 'aria-current="page"' in coaching_html
        assert 'aria-current="page">SERVICES</a>' in coaching_html


# ── Hero — "The Dossier" hero with corner CTA ───────────────


# ── Layout ───────────────────────────────────────────────────


class TestFullBleedLayout:
    def test_container_override(self, coaching_css):
        assert "max-width: none" in coaching_css

    def test_inner_measure(self, coaching_css):
        assert "rl-coach-inner" in coaching_css
        assert "max-width: 1200px" in coaching_css

    def test_all_sections_use_inner_wrapper(self, coaching_html):
        bands = coaching_html.count('<section class="rl-coach-band')
        inners = len(re.findall(r'class="rl-coach-inner[ "]', coaching_html))
        assert bands == inners == len(SECTION_IDS)

    def test_consent_banner_rendered(self, coaching_html):
        assert "{get_consent_banner_html()}" not in coaching_html


# ── Hero + ID card + sections ────────────────────────────────


class TestHero:
    def test_hero_id_and_cta(self):
        hero = build_hero()
        assert 'id="hero"' in hero
        assert f'href="{QUESTIONNAIRE_URL}"' in hero
        assert 'data-cta="hero_apply"' in hero
        assert "START YOUR APPLICATION &rarr;" in hero

    def test_headline_visible_text(self, coaching_html):
        h1 = re.search(r"<h1>(.*?)</h1>", coaching_html, re.DOTALL).group(1)
        text = re.sub(r"<[^>]+>", "", h1)
        assert text == "One-on-one coaching for road racers, from Tuesday-night crits to the long road race."
        assert coaching_html.count("<h1>") == 1

    def test_highlights(self):
        hero = build_hero()
        assert "<mark>Tuesday-night crits</mark>" in hero
        assert "<mark>the long road race.</mark>" in hero

    def test_subhead(self):
        hero = build_hero()
        assert "I raced Cat 1 and on the NRC." in hero
        assert "<strong>$199, $299 or $1,200</strong> every 4 weeks." in hero


class TestIdCard:
    def test_bio_line_verbatim(self):
        """Matti, 2026-11-15: the bio line, word for word."""
        card = build_id_card()
        assert "I&#39;m Matti Rowe. Peddler of bikes and hot takes, and really fast clients." in card

    def test_resume_rows(self):
        card = build_id_card()
        for label, value in ID_ROWS:
            assert f"<span>{label}</span>{value}" in card

    def test_talent_line(self):
        """Matti asked the resume to say very few have gotten farther on less talent."""
        talent = dict(ID_ROWS)["Talent"]
        assert "Very few people have gotten farther on less." in talent

    def test_only_public_road_facts(self):
        values = " ".join(v for _l, v in ID_ROWS)
        for fact in ("Cat 1", "NRC", "Cat 5 handling skills", "Rio Grande Elite", "third kid",
                     "TrainingPeaks", "Promoted twice"):
            assert fact in values

    def test_photo_and_cartoon(self):
        card = build_id_card()
        photo, pw, ph = IMAGES["photo"]
        toon, tw, th = IMAGES["cartoon"]
        assert f'src="/coaching/img/{photo}"' in card
        assert f'width="{pw}" height="{ph}"' in card
        assert f'src="/coaching/img/{toon}"' in card
        assert "roadie" in toon
        assert re.search(r'<img class="rl-coach-id-toon"[^>]*alt=""[^>]*aria-hidden="true"', card)
        assert re.search(r'<img class="rl-coach-id-real"[^>]*alt="[^"]+"', card)

    def test_swap_animation_and_reduced_motion(self, coaching_css):
        assert "@keyframes rl-coach-idswap" in coaching_css
        assert "animation: rl-coach-idswap" in coaching_css
        rm = coaching_css.split("prefers-reduced-motion: reduce", 1)[1]
        assert ".rl-coach-id-toon { animation: none; opacity: 0; }" in rm

    def test_photo_preloaded(self, coaching_html):
        assert f'<link rel="preload" as="image" href="/coaching/img/{IMAGES["photo"][0]}">' in coaching_html

    def test_no_reading_applications_line(self, coaching_html):
        """Matti, 2026-11-15: don't say I read every application myself. Of course I do."""
        visible = _visible_text(coaching_html).lower()
        for phrase in ("read every application", "read your application", "answer every one myself",
                       "read it myself", "myself, every time"):
            assert phrase not in visible, phrase


class TestCoachingImages:
    def test_every_image_is_in_the_repo(self):
        from PIL import Image
        for name, w, h in IMAGES.values():
            path = IMG_SRC_DIR / name
            assert path.is_file(), f"missing {path}"
            with Image.open(path) as im:
                assert im.size == (w, h), f"{name} is {im.size}, page says {(w, h)}"
                # Opaque: a transparent cartoon would show the photo through it mid-swap.
                assert im.mode == "RGB", f"{name} has transparency ({im.mode})"

    def test_write_copies_all(self, tmp_path):
        dest = write_coaching_images(tmp_path)
        assert dest == tmp_path / IMG_OUTPUT_SUBDIR
        assert sorted(p.name for p in dest.iterdir()) == sorted(n for n, _w, _h in IMAGES.values())

    def test_missing_image_refuses(self, tmp_path, monkeypatch):
        import generate_coaching
        monkeypatch.setattr(generate_coaching, "IMG_SRC_DIR", tmp_path / "nowhere")
        with pytest.raises(FileNotFoundError):
            generate_coaching.write_coaching_images(tmp_path / "out")

    def test_no_borrowed_close_art(self):
        """No v6.7 Roadie-kit scene exists yet, so the close runs without
        a picture rather than borrowing Gravel God art."""
        assert "<img" not in build_application_close()
        assert set(IMAGES) == {"photo", "cartoon"}


class TestFit:
    def test_fit_id_dark_band(self):
        fit = build_honest_check()
        assert 'id="fit"' in fit
        assert "rl-coach-band--dark" in fit

    def test_yes_no_lists(self):
        fit = build_honest_check()
        yes, no = fit.split('class="rl-coach-fit-no"')
        assert yes.count("<li>") == 3
        assert no.count("<li>") == 3
        assert "Coaching fits if" in yes
        assert "Probably not a fit if" in no
        assert "That&#39;s a physio&#39;s job." in no


class TestTerms:
    def test_five_items(self):
        terms = build_terms()
        assert 'id="terms"' in terms
        assert terms.count("<li>") == 5
        for t in ("Your race files, read.", "Training for how road races are decided.",
                  "A season around your A race.", "Plans that bend.", "Honest reads."):
            assert f"<h3>{t}</h3>" in terms

    def test_tier_claims_match_inclusions(self):
        terms = build_terms()
        assert "every quarter at Min and every 4 weeks at Mid and Max" in terms
        assert "At Mid and Max, a missed day" in terms


class TestWeek:
    def test_off_text_is_readable(self, coaching_css):
        """Steel on paper is about 2.7:1; graphite clears 4.5:1."""
        assert ".rl-coach-cad-off { color: var(--rl-color-graphite); }" in coaching_css

    def test_rows(self):
        week = build_week()
        assert 'id="week"' in week
        rows = re.findall(r'<th scope="row">([^<]+)</th>', week)
        assert rows == ["Each ride", "Each week", "Life happens", "Strategy calls", "Race week", "The season"]

    def test_phone_labels_follow_tiers(self):
        week = build_week()
        for _k, name, _p in TIERS:
            assert f'data-t="{name.upper()}"' in week


class TestHowItWorks:
    def test_five_steps(self):
        how = build_how_it_works()
        assert 'id="how-it-works"' in how
        assert how.count("<li>") == 5

    def test_real_flow(self):
        how = build_how_it_works()
        for bit in ("About 10 min", "2 business days", "your first 4 weeks and the $99 setup fee",
                    "set up on TrainingPeaks"):
            assert bit in how


class TestServiceTiers:
    def test_tiers_id(self):
        assert 'id="tiers"' in build_tiers()

    def test_prices_from_tiers(self):
        tiers = build_tiers()
        for key, name, price in TIERS:
            assert f'data-tier="{key}"' in tiers
            assert f'<span class="rl-coach-tprice">{price}</span>' in tiers
            assert TIER_BLURBS[key] in tiers
        assert tiers.count('<span class="rl-coach-tper">every 4 weeks</span>') == 3

    def test_apply_links(self):
        tiers = build_tiers()
        for key, name, _p in TIERS:
            assert f'href="{QUESTIONNAIRE_URL}?tier={key}"' in tiers
            assert f'data-cta="tier_{key}"' in tiers
            assert f">START WITH {name.upper()}</a>" in tiers

    def test_ledger_rows(self):
        tiers = build_tiers()
        rows = re.findall(r'<th scope="row">([^<]+)</th>', tiers)
        expected = [label for _g, group in LEDGER_GROUPS for label, *_v in group]
        assert rows == expected
        assert len(rows) == 15

    def test_inclusions_are_cumulative(self):
        for _g, group in LEDGER_GROUPS:
            for label, mn, md, mx in group:
                if mn is True:
                    assert md is True and mx is True, label
                if md is True:
                    assert mx is True, label

    def test_setup_fee_and_cancel_fine_print(self):
        tiers = build_tiers()
        assert "$99 one-time setup fee" in tiers
        assert "Any waiver is offered privately, case by case." in tiers
        assert "no cancellation fee." in tiers

    def test_phone_tabs_default_mid(self):
        tiers = build_tiers()
        assert 'data-show="mid"' in tiers
        assert 'data-tab="mid" aria-selected="true"' in tiers
        assert tiers.count('role="tab"') == 3

    def test_no_js_shows_every_column(self, coaching_css, coaching_js):
        """Tabs ship hidden and columns only collapse once the JS has
        wired the tabs, so a phone without JS still sees all three levels."""
        assert '<div class="rl-coach-tabs" role="tablist" aria-label="Levels" hidden>' in build_tiers()
        assert ".rl-coach-tabs[hidden] { display: none !important; }" in coaching_css
        hides = re.findall(r'\.rl-coach-ledger[^ {,]*\[data-show="\w+"\] \.rl-coach-t-\w+', coaching_css)
        assert len(hides) == 6
        assert all(h.startswith(".rl-coach-ledger.rl-coach-tabbed[") for h in hides)
        assert "ledger.classList.add('rl-coach-tabbed');" in coaching_js
        assert "tabs[0].parentNode.hidden = false;" in coaching_js
        # Untabbed phone rows label each cell with its level.
        assert ".rl-coach-ledger:not(.rl-coach-tabbed) tbody td::before { content: attr(data-t);" in coaching_css
        tiers = build_tiers()
        for key, name, _p in TIERS:
            assert f'<td class="rl-coach-t-{key}" data-t="{name.upper()}">' in tiers


class TestPicker:
    @pytest.fixture(scope="class")
    def picker(self):
        return build_fit_check()

    def test_hidden_without_js(self, picker):
        assert '<form class="rl-coach-picker" id="rl-coach-picker" aria-label="Three questions to pick a level" hidden>' in picker
        assert 'id="rl-coach-picker-out" aria-live="polite" hidden' in picker

    def test_three_questions_nine_radios(self, picker):
        assert picker.count("<fieldset>") == 3
        assert picker.count('type="radio"') == 9
        for text, options in PICKER_QUESTIONS:
            assert f"<p>{text}</p>" in picker
            for opt in options:
                assert f"<span>{opt}</span>" in picker

    def test_js_shows_it(self, coaching_js):
        assert "form.hidden = false;" in coaching_js
        assert "out.hidden = false;" in coaching_js

    def test_scoring_every_combination(self, coaching_js):
        """Rounded mean of the three answers: 1 → min, 2 → mid, 3 → max."""
        js = coaching_js.replace("<script>", "").replace("</script>", "")
        m = re.search(r"var names = (\{[^}]*\});", js)
        assert m
        script = (
            "var names=" + m.group(1) + ";var out=[];"
            "for(var a=1;a<4;a++)for(var b=1;b<4;b++)for(var c=1;c<4;c++)"
            "out.push(names[Math.round((a+b+c)/3)]);console.log(out.join(','));"
        )
        res = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=30)
        got = res.stdout.strip().split(",")
        names = {1: "min", 2: "mid", 3: "max"}
        # Three integers over 3 never land on .5, so Python's round agrees with Math.round.
        want = [names[round((a + b + c) / 3)] for a in (1, 2, 3) for b in (1, 2, 3) for c in (1, 2, 3)]
        assert got == want

    def test_result_labels_from_tiers(self, coaching_js):
        for _k, name, price in TIERS:
            assert f"Marked: {name}, {price} every 4 weeks." in coaching_js

    def test_analytics(self, coaching_js):
        assert "coaching_fitcheck_answer" in coaching_js
        assert "coaching_fitcheck_result" in coaching_js


class TestFAQ:
    def test_eight_details(self):
        faq = build_faq()
        assert 'id="faq"' in faq
        assert faq.count('<details class="rl-coach-faq-item">') == 8
        assert faq.count("<summary>") == 8

    def test_setup_fee_and_cancel(self):
        faq = build_faq()
        assert "What&#39;s the $99 setup fee?" in faq
        assert "Can I cancel anytime?" in faq

    def test_missed_workout_answer_by_tier(self):
        faq = build_faq()
        assert "At Mid and Max I move things that week, and at Min we sort it out in the weekly review." in faq


class TestApplicationClose:
    def test_close(self):
        close = build_application_close()
        assert 'id="final-cta"' in close
        assert "Get on the start list." in close
        assert 'data-cta="final_fill_intake"' in close
        assert f'href="{QUESTIONNAIRE_URL}"' in close
        assert 'href="mailto:coach@roadielabs.com"' in close


class TestNothingUnbuiltShips:
    def test_no_placeholders(self, coaching_html):
        visible = _visible_text(coaching_html)
        assert "NOT BUILT" not in visible
        assert "placeholder" not in visible.lower()
        assert coaching_html.count("<blockquote") == 0


class TestMobileStickyCTA:
    def test_label_updated(self):
        sticky = build_mobile_sticky_cta()
        assert "START YOUR APPLICATION &rarr;" in sticky
        assert "Apply for coaching" not in sticky

    def test_data_cta_and_href(self):
        sticky = build_mobile_sticky_cta()
        assert 'data-cta="sticky_cta"' in sticky
        assert f'href="{QUESTIONNAIRE_URL}"' in sticky


# ── Brand Compliance ─────────────────────────────────────────


class TestBrandCompliance:
    def test_no_hardcoded_hex_in_coaching_css(self, coaching_css):
        css = re.sub(r'/\*.*?\*/', '', coaching_css, flags=re.DOTALL)
        hex_colors = re.findall(r'#[0-9a-fA-F]{3,8}\b', css)
        assert len(hex_colors) == 0, f"Found hardcoded hex in coaching CSS: {hex_colors[:5]}"

    def test_no_hardcoded_hex_in_apply_css(self):
        css = re.sub(r'/\*.*?\*/', '', build_apply_css(), flags=re.DOTALL)
        hex_colors = re.findall(r'#[0-9a-fA-F]{3,8}\b', css)
        assert len(hex_colors) == 0, f"Found hardcoded hex in apply CSS: {hex_colors[:5]}"

    def test_no_border_radius(self, coaching_css):
        assert "border-radius" not in coaching_css

    def test_no_box_shadow(self, coaching_css):
        assert "box-shadow" not in coaching_css

    def test_uses_brand_tokens(self, coaching_css):
        assert "var(--rl-color-" in coaching_css
        assert "var(--rl-font-" in coaching_css

    def test_no_bounce_easing(self, coaching_css):
        assert "cubic-bezier(0.34, 1.56" not in coaching_css

    def test_correct_class_prefix(self, coaching_css):
        allowed_roots = (
            'rl-coach-', 'rl-neo-brutalist', 'rl-site-header', 'rl-hero',
            'rl-section', 'rl-breadcrumb', 'rl-footer', 'rl-mega-footer',
            'rl-has-js', 'rl-in-view',
        )
        classes = set(re.findall(r'\.([a-zA-Z][\w-]*)', coaching_css))
        for cls in classes:
            assert cls.startswith(allowed_roots), (
                f"Non-prefixed class in coaching CSS: .{cls}"
            )


class TestTokenValidation:
    @pytest.fixture(scope="class")
    def defined_tokens(self):
        from brand_tokens import get_tokens_css
        return set(re.findall(r'(--rl-[\w-]+)\s*:', get_tokens_css()))

    def test_coaching_css_all_var_refs_defined(self, coaching_css, defined_tokens):
        used = set(re.findall(r'var\((--rl-[\w-]+)\)', coaching_css))
        undefined = used - defined_tokens
        assert not undefined, f"Undefined CSS tokens in coaching CSS: {undefined}"

    def test_apply_css_all_var_refs_defined(self, defined_tokens):
        used = set(re.findall(r'var\((--rl-[\w-]+)\)', build_apply_css()))
        undefined = used - defined_tokens
        assert not undefined, f"Undefined CSS tokens in apply CSS: {undefined}"


# ── GA4 Events ───────────────────────────────────────────────


class TestGA4Events:
    def test_all_events_present(self, coaching_js):
        events = [
            "coaching_faq_open",
            "coaching_scroll_depth",
            "coaching_cta_click",
            "coaching_page_view",
        ]
        for event in events:
            assert event in coaching_js, f"Missing GA4 event: {event}"

    def test_no_carousel_events(self, coaching_js):
        assert "coaching_carousel" not in coaching_js

    def test_ga4_present_in_both_outputs(self, coaching_html, apply_html):
        for html_doc in (coaching_html, apply_html):
            assert "G-WQ7W8XN11N" in html_doc
            assert "googletagmanager.com" in html_doc

    def test_scroll_depth_section_ids_match_real_sections(self, coaching_js, coaching_html):
        """Every id referenced by the scroll-depth IIFE must exist in the
        shipped HTML, and the set must be exactly the real content
        sections: no dead ids, no missing sections."""
        section_ids = re.findall(r"id:\s*'([\w-]+)'", coaching_js)
        assert set(section_ids) == set(SECTION_IDS)
        for sid in section_ids:
            assert f'id="{sid}"' in coaching_html, f"Dead section id in scroll-depth JS: {sid}"

    def test_old_section_labels_removed(self, coaching_js):
        for old_id in ("'problem'", "'deliverables'", "'honest-check'"):
            assert old_id not in coaching_js, f"Stale scroll-depth id still present: {old_id}"


# ── JS Syntax ────────────────────────────────────────────────


class TestJSSyntax:
    def test_coaching_js_parses_via_node(self, coaching_js):
        js_body = coaching_js.replace("<script>", "").replace("</script>", "")
        result = subprocess.run(
            [
                "node", "--input-type=module", "-e",
                "const src = process.argv[1];"
                "new Function(src);"
                "console.log('SYNTAX_OK');",
                js_body,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"JS syntax error: {result.stdout} {result.stderr}"
        assert "SYNTAX_OK" in result.stdout

    def test_apply_js_parses_via_node(self, apply_js):
        js_body = apply_js.replace("<script>", "").replace("</script>", "")
        result = subprocess.run(
            [
                "node", "--input-type=module", "-e",
                "const src = process.argv[1];"
                "new Function(src);"
                "console.log('SYNTAX_OK');",
                js_body,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"JS syntax error: {result.stdout} {result.stderr}"
        assert "SYNTAX_OK" in result.stdout


# ── JSON-LD ──────────────────────────────────────────────────


class TestJSONLD:
    def test_race_count_loaders_require_the_race_index(self, monkeypatch, tmp_path):
        """A missing index must fail the build instead of publishing a zero count."""
        import generate_blog_index_page
        import generate_coaching

        missing_index = tmp_path / "missing-race-index.json"
        for module in [generate_coaching, generate_blog_index_page]:
            monkeypatch.setattr(module, "RACE_INDEX_JSON", missing_index)
            with pytest.raises(RuntimeError, match="Required race index is missing"):
                module.load_race_count()

    def test_webpage_schema(self):
        ld = build_jsonld()
        assert '"@type":"WebPage"' in ld
        assert "/coaching/" in ld
        assert "Roadie Labs" in ld

    def test_service_schema(self):
        ld = build_jsonld()
        assert '"@type":"Service"' in ld
        assert "Road Cycling Coaching" in ld

    def test_description_reflects_new_hero(self):
        """The old description referenced the removed 'Fitness is common'
        hero — it must be gone, replaced by wording consistent with the
        one-coach / N-courses hero. The count is dynamic from
        race-index.json (never hardcode — stale-count trap)."""
        from generate_coaching import load_race_count
        ld = build_jsonld()
        page = generate_coaching_page()
        count = load_race_count()
        assert "Fitness is common" not in ld
        assert count > 300
        # Matti, 2026-11-15: never position against AI ("a human coach")
        # and never name the coach in the third person, even in meta tags.
        for bad in ("human", "the coach behind", "one coach,"):
            assert bad not in ld.lower() and bad not in page.lower(), bad
        assert "One-on-one road coaching from Matti Rowe." in ld
        assert "One-on-one coaching for road racers" in page

    def test_uses_safe_json_for_script(self):
        """JSON-LD must go through _safe_json_for_script — a '</script>'
        payload should never be able to break out of the <script> tag."""
        from generate_neo_brutalist import _safe_json_for_script
        payload = {"a": "</script><script>alert(1)</script>"}
        safe = _safe_json_for_script(payload)
        assert "</script>" not in safe


# ── Accessibility ────────────────────────────────────────────


class TestAccessibility:
    def test_skip_to_content_link(self, coaching_html):
        assert 'class="rl-coach-skip-link"' in coaching_html
        assert 'Skip to content' in coaching_html

    def test_reduced_motion_css(self, coaching_css):
        assert "prefers-reduced-motion: reduce" in coaching_css

    def test_faq_uses_native_disclosure(self, coaching_html):
        assert "<details" in coaching_html and "<summary>" in coaching_html
        assert 'role="button"' not in build_faq()

    def test_ledger_marks_have_names(self):
        tiers = build_tiers()
        assert 'role="img" aria-label="Included"' in tiers
        assert 'role="img" aria-label="Not included"' in tiers


# ── Scroll Animations ────────────────────────────────────────


class TestNoScrollAnimations:
    """No entrance animations and no observer-gated content. The only
    motion is the ID-card photo/cartoon swap, which reduced motion stops."""

    def test_no_data_animate(self, coaching_html):
        assert "data-animate" not in coaching_html

    def test_only_the_cartoon_starts_hidden(self, coaching_css):
        rules = re.findall(r"([^{}]+)\{[^{}]*opacity: 0;", coaching_css)
        assert [r.strip() for r in rules if not r.strip().endswith("%")] == [".rl-coach-id-toon", ".rl-coach-id-toon"]



# ── Restraint Guard ──────────────────────────────────────────
# The page asserts; it doesn't perform. Banned substrings from the old
# loud template must never come back.


BANNED_SUBSTRINGS = [
    "$14.95",
    "/ride",
    "If you can pedal",
    "blown race",
    "costs you",
    "suffer smarter",
    "Not a Spreadsheet",
    "generated in 2 seconds",
    "Honest Check",
    "Can't Get From a Prompt",
    "328 races",
    "brake pads",
    "Strava KOM",
]

# Checked against VISIBLE TEXT ONLY (script/style stripped, tags stripped) —
# these are generic words that can legitimately appear in class names,
# comments, or CSS without being loud marketing copy on the rendered page.
NEW_BANNED_VISIBLE_TEXT = [
    "unlock",
    "transform",
    "crush",
    "Fitness is common",
]


def _visible_text(html_doc: str) -> str:
    """Strip <script>...</script> and <style>...</style> blocks, then strip
    remaining HTML tags, leaving only what a reader actually sees."""
    no_script = re.sub(r'<script.*?</script>', '', html_doc, flags=re.DOTALL)
    no_style = re.sub(r'<style.*?</style>', '', no_script, flags=re.DOTALL)
    return re.sub(r'<[^>]+>', '', no_style)


class TestRestraintGuard:
    @pytest.mark.parametrize("phrase", BANNED_SUBSTRINGS)
    def test_banned_phrase_absent(self, coaching_html, phrase):
        assert phrase not in coaching_html, f"Banned phrase found in coaching page: {phrase!r}"

    @pytest.mark.parametrize("phrase", NEW_BANNED_VISIBLE_TEXT)
    def test_banned_visible_text_absent(self, coaching_html, phrase):
        visible = _visible_text(coaching_html)
        assert phrase not in visible, f"Banned word found in visible coaching page text: {phrase!r}"

    def test_no_defensive_messaging(self, coaching_html):
        lower = coaching_html.lower()
        assert "no sponsors" not in lower
        assert "not sponsored" not in lower
        assert "no affiliates" not in lower


# ── Required Content ─────────────────────────────────────────


class TestRequiredContent:
    def test_no_visible_course_count(self, coaching_html):
        """Owner revision 2026-07-18: the courses-on-file flex removed from
        visible copy. (JSON-LD metadata may still carry it.)"""
        assert "COURSES ON FILE" not in coaching_html



    def test_link_to_about(self, coaching_html):
        assert f"{SITE_BASE_URL}/about/" in coaching_html

    def test_apply_url_present(self, coaching_html):
        assert QUESTIONNAIRE_URL in coaching_html
        assert QUESTIONNAIRE_URL == f"{SITE_BASE_URL}/coaching/apply/"

    def test_setup_fee(self, coaching_html):
        assert "$99 setup fee" in coaching_html

    def test_hero_h1(self, coaching_html):
        assert "from <mark>Tuesday-night crits</mark> to <mark>the long road race.</mark></h1>" in coaching_html

    def test_banned_copy_absent(self, coaching_html):
        """Copy rules: no AI positioning, the retired headline, monthly
        billing words, the wrong coach name, or third-person coach."""
        import re
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", coaching_html, flags=re.S)
        for banned in ("Not an AI", "not an AI", "better than you think",
                       "monthly", "Monthly", "/mo", "per month", "Matt ",
                       "your coach", "Your coach", "GET ME IN YOUR CORNER"):
            assert banned not in text, banned

    def test_final_contact_line(self, coaching_html):
        assert "coach@roadielabs.com" in coaching_html
        assert 'href="mailto:coach@roadielabs.com"' in coaching_html

    def test_old_sections_removed(self, coaching_html):
        assert 'id="problem"' not in coaching_html
        assert 'id="deliverables"' not in coaching_html

    def test_all_section_ids_present(self, coaching_html):
        for sid in SECTION_IDS:
            assert f'id="{sid}"' in coaching_html


# ── Cross-Brand Leakage ──────────────────────────────────────


class TestCrossBrandLeakage:
    def test_coaching_no_gg_classes(self, coaching_html):
        assert 'class="gg-' not in coaching_html

    def test_coaching_no_gravel_domain(self, coaching_html):
        assert "gravelgodcycling.com" not in coaching_html

    def test_apply_no_gg_classes(self, apply_html):
        assert 'class="gg-' not in apply_html

    def test_apply_no_gravel_domain(self, apply_html):
        assert "gravelgodcycling.com" not in apply_html

    def test_no_gravel_god_prose(self, coaching_html):
        """Testimonials + provenance removed 2026-07-18 — nothing on the
        page should reference the sibling brand anymore."""
        assert "Gravel God" not in coaching_html


# ── Apply Page ───────────────────────────────────────────────


class TestApplyPage:
    def test_shared_intake_endpoint(self, apply_html):
        assert COACHING_INTAKE_WORKER_URL in apply_html
        assert "formsubmit.co" not in apply_html.lower()
        assert '"Content-Type": "application/json"' in apply_html

    def test_tier_selector_uses_min_mid_max(self, apply_html):
        selector = build_tier_selector()
        assert 'name="tier"' in selector
        assert 'option value="min"' in selector
        assert 'option value="mid"' in selector
        assert 'option value="max"' in selector
        assert "TrainingPeaks Premium is included" in selector
        assert "initializeTier" in apply_html

    def test_submission_id_is_stable_for_retry(self, apply_html):
        assert "coaching_intake_submission_id" in apply_html
        assert "crypto.randomUUID" in apply_html
        assert "data.submission_id = getSubmissionId()" in apply_html

    def test_apply_funnel_events_are_present(self, apply_html):
        assert "coaching_apply_started" in apply_html
        assert "coaching_apply_submitted" in apply_html
        assert "coaching_apply_error" in apply_html

    def test_submission_preserves_consent_mode_state(self, apply_html):
        assert "analyticsConsentState" in apply_html
        assert "rl_consent=accepted" in apply_html
        assert "rl_consent=declined" in apply_html
        from cookie_consent import ANALYTICS_CONSENT_STATE_JS
        assert ANALYTICS_CONSENT_STATE_JS in apply_html
        assert "data.analytics_consent = analyticsConsentState()" in apply_html

    def test_low_friction_onboarding_context_is_collected(self, apply_html):
        for field in (
                'date_of_birth', 'home_location', 'desired_start_date',
                'preferred_contact_channel', 'trainingpeaks_connection_status',
                'home_timezone', 'guardian_name', 'guardian_email',
                'guardian_relationship'):
            assert f'name="{field}"' in apply_html
        assert 'Intl.DateTimeFormat().resolvedOptions().timeZone' in apply_html
        assert 'id="home_timezone" required' not in apply_html
        assert 'min="13"' in apply_html
        assert 'separate consent step' in apply_html

    def test_header_js_present(self, apply_html):
        """Distinctive substring of get_site_header_js() — proves the
        mobile hamburger behavior is wired into the apply page."""
        assert "rl-site-header-toggle" in apply_html
        assert "aria-expanded" in apply_html

    def test_no_auto_mailto_redirect(self, apply_html):
        assert 'window.location.href = "mailto' not in apply_html

    def test_mailto_fallback_link_built_via_dom(self, apply_html):
        """Failure offers a plain mailto link (no body); the subject carries
        the athlete's name, so it is built with createElement, not innerHTML."""
        failure = apply_html.split(".catch(function(err)", 1)[1]
        assert '"mailto:coach@roadielabs.com?subject=" + encodeURIComponent(' in failure
        assert "body=" not in failure.split("messageDiv.appendChild(mailtoLink);", 1)[0]
        assert 'document.createElement("a")' in failure
        assert "mailtoLink.textContent" in failure

    def test_honeypot_field_present(self, apply_html):
        assert 'name="website"' in apply_html
        assert "rl-apply-honeypot" in apply_html

    def test_honeypot_client_check_present(self, apply_html):
        assert "if (data.website)" in apply_html

    def test_confidentiality_footer_links_privacy_policy(self, apply_html):
        assert 'href="/privacy/"' in apply_html

    def test_success_requires_explicit_flag(self, apply_html):
        assert "!response.ok || !result.success" in apply_html

    def test_failure_keeps_saved_answers(self, apply_html):
        failure = apply_html.split(".catch(function(err)", 1)[1]
        assert "still saved in this browser" in failure
        assert 'removeItem("athlete_questionnaire_progress")' not in failure
        # The claim must be true without a prior "Save Progress" click.
        assert failure.index("saveProgress();") < failure.index('showMessage("error"')

    def test_failure_ga4_keeps_both_series(self, apply_html):
        failure = apply_html.split(".catch(function(err)", 1)[1].split("/* ── Show message", 1)[0]
        assert 'ga4("apply_form_error"' in failure
        assert 'ga4("coaching_apply_error"' in failure
        assert 'ga4("apply_form_fallback", { method: "mailto" });' in failure


# ── Drift Guard ──────────────────────────────────────────────
# Regenerating each page in-memory must equal the checked-in output
# byte-for-byte. A failure here means someone edited the generator
# source without regenerating wordpress/output/*.html.


class TestDriftGuard:
    def test_coaching_html_matches_checked_in_output(self, tmp_path):
        checked_in_path = OUTPUT_DIR / "coaching.html"
        if not checked_in_path.exists():
            pytest.skip("wordpress/output/coaching.html not generated yet")
        assets = write_shared_assets(tmp_path)
        regenerated = generate_coaching_page(external_assets=assets)
        checked_in = checked_in_path.read_text(encoding="utf-8")
        assert regenerated == checked_in, (
            "wordpress/output/coaching.html is stale — run "
            "`python3 wordpress/generate_coaching.py` to regenerate it."
        )

    def test_apply_html_matches_checked_in_output(self, tmp_path):
        checked_in_path = OUTPUT_DIR / "coaching-apply.html"
        if not checked_in_path.exists():
            pytest.skip("wordpress/output/coaching-apply.html not generated yet")
        assets = write_shared_assets(tmp_path)
        regenerated = generate_apply_page(external_assets=assets)
        checked_in = checked_in_path.read_text(encoding="utf-8")
        assert regenerated == checked_in, (
            "wordpress/output/coaching-apply.html is stale — run "
            "`python3 wordpress/generate_coaching_apply.py` to regenerate it."
        )


class TestApplyButtonsFitAPhone:
    """Submit sat beside Save Progress and ran 14px past a 375px screen
    (live check, 2026-11-16). On phones the two stack full width."""

    def test_buttons_stack_on_phone(self):
        css = build_apply_css()
        phone = css[css.index("@media (max-width: 600px)"):]
        actions = phone[phone.index(".rl-apply-actions {"):]
        assert "flex-direction: column;" in actions.split("}", 1)[0]
        submit = phone[phone.index(".rl-apply-submit-btn {"):].split("}", 1)[0]
        assert "width: 100%;" in submit and "flex: none;" in submit


class TestApplyContactIsRoadie:
    """Roadie riders write to coach@roadielabs.com, never the Gravel God inbox."""

    def test_privacy_line_points_to_roadie_inbox(self, apply_html):
        assert 'mailto:coach@roadielabs.com">coach@roadielabs.com</a>' in apply_html
        assert "gravelgodcoaching@gmail.com" not in apply_html
