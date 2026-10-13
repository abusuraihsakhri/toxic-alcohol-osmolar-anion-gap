const test = require('node:test');
const assert = require('node:assert/strict');
const { calculate } = require('./calculator.js');
const normal = { measured: '290', sodium: '140', glucose: '100', bun: '15', ethanol: '', chloride: '104', bicarbonate: '24' };

test('osmolal and anion gaps from standard units', () => {
  assert.deepEqual(calculate(normal), { calculatedOsmolarity: 290.91, osmolalGap: -0.91, anionGap: 12, ethanolIncluded: false });
});
test('ethanol correction reduces residual gap', () => {
  const r = calculate({ ...normal, measured: '320', ethanol: '46' });
  assert.equal(r.osmolalGap, 19.09);
  assert.equal(r.ethanolIncluded, true);
});
test('anion gap can be omitted', () => {
  assert.equal(calculate({ ...normal, chloride: '', bicarbonate: '' }).anionGap, null);
});
test('paired anion gap inputs required', () => {
  assert.throws(() => calculate({ ...normal, chloride: '' }), /both chloride and bicarbonate/);
});
test('rejects blank, negative, infinity, and nonnumeric input', () => {
  for (const measured of ['', '-1', 'Infinity', 'NaN', 'abc']) {
    assert.throws(() => calculate({ ...normal, measured }), /required|finite/);
  }
});
test('zero ethanol included distinctly from unknown ethanol', () => {
  assert.equal(calculate({ ...normal, ethanol: '0' }).ethanolIncluded, true);
});
