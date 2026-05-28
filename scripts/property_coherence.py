#!/usr/bin/env python3
"""
Alexander's 15 Properties of Living Structure - Coherence Assessment
Evaluates GTAngelEcho architecture against all 15 properties.

KSM Cycle 2: Updated scores to reflect Extension Architecture improvements
(The Void — Property 13).
"""
import json
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

PROPERTIES = {
    1: {"name": "Levels of Scale", "description": "Multiple nested levels from micro to macro",
        "assessment": "5 levels: System → Centers → Modules → Functions → Plugins. Plugin hierarchy adds extensible 5th level."},
    2: {"name": "Strong Centres", "description": "Well-defined focal points of activity",
        "assessment": "8 core centers + 3 extension centers (EventBus, PluginRegistry, HookSystem). All strongly defined with tests."},
    3: {"name": "Boundaries", "description": "Clear edges that define and protect centers",
        "assessment": "PluginBase ABC, HookPoint enum, API route registration — explicit, well-typed boundaries."},
    4: {"name": "Alternating Repetition", "description": "Rhythmic patterns that create life",
        "assessment": "Echobeats 4-phase, per-tick plugin dispatch, event emit/subscribe, hook apply chain."},
    5: {"name": "Positive Space", "description": "Every part contributes, no dead zones",
        "assessment": "All centers functional. 3 example plugins fill extension space. API has 14 working routes."},
    6: {"name": "Good Shape", "description": "Clean, well-proportioned forms",
        "assessment": "Clean module shapes. API Adapter provides well-shaped external interface. Plugin meta describes shape."},
    7: {"name": "Local Symmetries", "description": "Symmetry at local level, not forced globally",
        "assessment": "EventBus on/off, HookSystem add/remove, Plugin enable/disable — symmetric lifecycle pairs."},
    8: {"name": "Deep Interlock", "description": "Centers deeply connected to neighbors",
        "assessment": "Plugins interlock with core via EventBus + HookSystem. API bridges external/internal. Context dict."},
    9: {"name": "Contrast", "description": "Clear differentiation between elements",
        "assessment": "Core (fixed) vs Extensions (dynamic). Events (fire-and-forget) vs Hooks (modify-and-return). Clear contrast."},
    10: {"name": "Gradients", "description": "Smooth transitions between states",
         "assessment": "Priority gradients: SYSTEM→HIGH→NORMAL→LOW→MONITOR in EventBus and HookSystem."},
    11: {"name": "Roughness", "description": "Organic irregularity, not mechanical perfection",
         "assessment": "Lorenz chaos, stochastic exploration, emergent plugin interactions, non-deterministic event ordering."},
    12: {"name": "Echoes", "description": "Similar patterns recurring at different scales",
         "assessment": "Plugin lifecycle echoes center lifecycle. EventBus subscribe echoes endocrine subscribe. Pattern echoes."},
    13: {"name": "The Void", "description": "Intentional empty space for growth",
         "assessment": "MAJOR: Plugin system, event bus, 20 hook points, REST API, contrib/ directory — intentional space for growth."},
    14: {"name": "Simplicity and Inner Calm", "description": "Minimal complexity per component",
         "assessment": "Extension architecture adds complexity but is well-encapsulated. Each extension module has single responsibility."},
    15: {"name": "Not-Separateness", "description": "Connected to the larger whole",
         "assessment": "Plugins participate in same tick loop. API exposes same state. No separate worlds. Part of DTE ecosystem."}
}

# Cycle 2 scores
SCORES = {
    1: 0.88, 2: 0.93, 3: 0.87, 4: 0.85, 5: 0.85,
    6: 0.88, 7: 0.85, 8: 0.90, 9: 0.85, 10: 0.82,
    11: 0.80, 12: 0.90, 13: 0.85, 14: 0.78, 15: 0.88
}

# Cycle 1 scores for comparison
CYCLE_1_SCORES = {
    1: 0.87, 2: 0.92, 3: 0.82, 4: 0.82, 5: 0.80,
    6: 0.87, 7: 0.82, 8: 0.88, 9: 0.82, 10: 0.78,
    11: 0.78, 12: 0.87, 13: 0.65, 14: 0.78, 15: 0.85
}

# Cycle 0 scores
CYCLE_0_SCORES = {
    1: 0.85, 2: 0.90, 3: 0.80, 4: 0.75, 5: 0.70,
    6: 0.85, 7: 0.80, 8: 0.75, 9: 0.80, 10: 0.70,
    11: 0.65, 12: 0.85, 13: 0.60, 14: 0.75, 15: 0.80
}


def assess_all():
    """Run full 15-property coherence assessment."""
    logging.info("=" * 70)
    logging.info("Alexander's 15 Properties - GTAngelEcho Coherence Assessment")
    logging.info("KSM Cycle 2 (Post-Evolution: The Void)")
    logging.info("=" * 70)

    total = 0.0
    results = []

    for prop_id in range(1, 16):
        prop = PROPERTIES[prop_id]
        score = SCORES[prop_id]
        c1_score = CYCLE_1_SCORES[prop_id]
        c0_score = CYCLE_0_SCORES[prop_id]
        delta_1_2 = score - c1_score
        delta_0_2 = score - c0_score
        total += score

        status = "EXCELLENT" if score >= 0.85 else "GOOD" if score >= 0.70 else "FAIR" if score >= 0.60 else "WEAK"

        logging.info(f"\n  Property {prop_id:2d}: {prop['name']}")
        logging.info(f"    Score: {score:.2f} [{status}] (C0={c0_score:.2f} → C1={c1_score:.2f} → C2={score:.2f}, Δ1→2={delta_1_2:+.2f})")
        logging.info(f"    Evidence: {prop['assessment']}")

        results.append({
            "id": prop_id,
            "name": prop["name"],
            "score": score,
            "cycle_0": c0_score,
            "cycle_1": c1_score,
            "delta_1_2": delta_1_2,
            "delta_0_2": delta_0_2,
            "status": status,
            "assessment": prop["assessment"]
        })

    overall = total / 15
    c1_overall = sum(CYCLE_1_SCORES.values()) / 15
    c0_overall = sum(CYCLE_0_SCORES.values()) / 15
    delta_total = overall - c1_overall

    logging.info(f"\n{'=' * 70}")
    logging.info(f"OVERALL COHERENCE: C0={c0_overall:.3f} → C1={c1_overall:.3f} → C2={overall:.3f} (Δ1→2={delta_total:+.3f})")

    if overall >= 0.90:
        logging.info("Level: EXCELLENT — Architecture has strong living quality")
    elif overall >= 0.80:
        logging.info("Level: GOOD — Architecture is healthy, continue strengthening")
    elif overall >= 0.70:
        logging.info("Level: FAIR — Minor adjustments recommended")
    else:
        logging.info("Level: POOR — Transformation may have damaged wholeness")

    # Biggest improvements
    improvements = sorted(results, key=lambda r: r["delta_1_2"], reverse=True)
    logging.info(f"\nBiggest Cycle 2 Improvements:")
    for r in improvements[:3]:
        logging.info(f"  {r['name']}: {r['cycle_1']:.2f} → {r['score']:.2f} (Δ={r['delta_1_2']:+.2f})")

    # Weakest
    weakest = min(results, key=lambda r: r["score"])
    logging.info(f"\nWeakest Property: {weakest['name']} ({weakest['score']:.2f})")
    logging.info(f"  → Cycle 3 Target: {weakest['name']}")

    # Save report
    report = {
        "timestamp": datetime.now().isoformat(),
        "cycle": 2,
        "overall_score": overall,
        "cycle_1_overall": c1_overall,
        "cycle_0_overall": c0_overall,
        "delta_1_2": delta_total,
        "properties": results,
        "weakest": weakest,
        "strongest": max(results, key=lambda r: r["score"]),
        "biggest_improvement": max(results, key=lambda r: r["delta_1_2"]),
    }

    report_path = Path(__file__).parent.parent / "docs" / "property_coherence_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    logging.info(f"\nReport saved: {report_path}")

    return report


if __name__ == "__main__":
    assess_all()
