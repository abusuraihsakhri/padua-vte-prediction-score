const test = require("node:test");
const assert = require("node:assert/strict");
const { PADUA_FACTORS, calculatePadua } = require("./app.js");

test("published factor weights and maximal score", () => {
  assert.equal(PADUA_FACTORS.length, 11);
  assert.equal(PADUA_FACTORS.reduce((sum, f) => sum + f.points, 0), 20);
  assert.equal(calculatePadua({}).score, 0);
  assert.equal(calculatePadua(Object.fromEntries(PADUA_FACTORS.map(f => [f.key, true]))).score, 20);
});
test("published threshold and individual factors", () => {
  for (const factor of PADUA_FACTORS) {
    const result = calculatePadua({ [factor.key]:true });
    assert.equal(result.score, factor.points, factor.key);
  }
  assert.deepEqual(calculatePadua({active_cancer:true}).risk_level, "Low");
  assert.deepEqual(calculatePadua({active_cancer:true, age_70_or_older:true}).risk_level, "High");
});
test("rejects nonboolean inputs", () => {
  assert.throws(() => calculatePadua({active_cancer:"false"}), TypeError);
});
