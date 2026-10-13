"use strict";
// This browser implementation mirrors the published eleven-factor Padua scale
// and the reference Python PADUA_RISK_FACTORS table in padua.py.
const PADUA_FACTORS = Object.freeze([
  { key:"active_cancer", label:"Active cancer", detail:"Metastases and/or chemotherapy or radiotherapy within 6 months", points:3 },
  { key:"previous_vte", label:"Previous VTE", detail:"Excluding superficial vein thrombosis", points:3 },
  { key:"reduced_mobility", label:"Reduced mobility", detail:"Bed rest with bathroom privileges for at least 3 days", points:3 },
  { key:"thrombophilic_condition", label:"Known thrombophilia", detail:"Established inherited or acquired thrombophilic condition", points:3 },
  { key:"recent_trauma_or_surgery", label:"Recent trauma or surgery", detail:"Within the previous month", points:2 },
  { key:"age_70_or_older", label:"Age ≥70 years", detail:"Age at assessment", points:1 },
  { key:"heart_or_respiratory_failure", label:"Heart or respiratory failure", detail:"Current heart and/or respiratory failure", points:1 },
  { key:"acute_mi_or_ischemic_stroke", label:"Acute MI or ischemic stroke", detail:"Current acute event", points:1 },
  { key:"acute_infection_or_rheumatologic", label:"Acute infection or rheumatologic disorder", detail:"Current illness", points:1 },
  { key:"obesity_bmi_30_or_more", label:"Obesity", detail:"Body mass index ≥30 kg/m²", points:1 },
  { key:"ongoing_hormonal_treatment", label:"Ongoing hormonal treatment", detail:"Current hormonal treatment", points:1 }
]);

function calculatePadua(selection) {
  let score = 0;
  const active = [];
  for (const factor of PADUA_FACTORS) {
    const selected = selection[factor.key] === undefined ? false : selection[factor.key];
    if (typeof selected !== "boolean") throw new TypeError(factor.key + " must be boolean");
    if (selected) {
      score += factor.points;
      active.push({ key:factor.key, label:factor.label, points:factor.points });
    }
  }
  return { score, risk_level: score >= 4 ? "High" : "Low", active_factors:active };
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { PADUA_FACTORS, calculatePadua };
}

if (typeof document !== "undefined") {
  const list = document.getElementById("factor-list");
  const form = document.getElementById("risk-form");
  for (const factor of PADUA_FACTORS) {
    const label = document.createElement("label");
    label.className = "factor";
    const input = document.createElement("input");
    input.type = "checkbox";
    input.name = factor.key;
    const info = document.createElement("span");
    info.className = "info";
    const name = document.createElement("span");
    name.className = "name";
    name.textContent = factor.label;
    const detail = document.createElement("span");
    detail.className = "detail";
    detail.textContent = factor.detail;
    const points = document.createElement("span");
    points.className = "points";
    points.textContent = "+" + factor.points;
    info.append(name, detail);
    label.append(input, info, points);
    list.append(label);
  }

  function selection() {
    const selected = {};
    for (const field of PADUA_FACTORS) selected[field.key] = form.elements.namedItem(field.key).checked;
    return selected;
  }
  function render() {
    const result = calculatePadua(selection());
    document.getElementById("score").firstChild.nodeValue = result.score + " ";
    const classification = document.getElementById("classification");
    classification.dataset.risk = result.risk_level.toLowerCase();
    classification.textContent = result.risk_level + " VTE-risk category";
    document.getElementById("interpretation").textContent = result.risk_level === "High"
      ? "Score ≥4. Elevated VTE-risk category; evaluate individual bleeding risk, contraindications and appropriate preventive measures."
      : "Score <4. Low VTE-risk category; reassess if the clinical condition changes.";
    const breakdown = document.getElementById("breakdown");
    breakdown.replaceChildren();
    if (!result.active_factors.length) {
      const item = document.createElement("li");
      item.textContent = "No factors selected";
      breakdown.append(item);
    } else {
      for (const factor of result.active_factors) {
        const item = document.createElement("li");
        const name = document.createElement("span");
        name.textContent = factor.label;
        const points = document.createElement("strong");
        points.textContent = "+" + factor.points;
        item.append(name, points);
        breakdown.append(item);
      }
    }
  }
  form.addEventListener("change", render);
  document.getElementById("clear").addEventListener("click", () => {
    for (const element of form.querySelectorAll('input[type="checkbox"]')) element.checked = false;
    render();
  });
  document.getElementById("export").addEventListener("click", () => {
    const result = calculatePadua(selection());
    const data = {
      scale: "Padua Prediction Score", score: result.score,
      risk_level: result.risk_level, selected_factors: result.active_factors,
      note: "Reference assessment only; bleeding risk and contraindications not evaluated"
    };
    const blob = new Blob([JSON.stringify(data, null, 2) + "\n"], { type:"application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "padua-vte-score.json";
    link.click();
    URL.revokeObjectURL(url);
  });
  render();
}
