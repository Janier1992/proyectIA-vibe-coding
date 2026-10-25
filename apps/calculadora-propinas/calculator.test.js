'use strict';
const { describe, test } = require('node:test');
const assert = require('node:assert/strict');
const calc = require('./calculator.js');

const { parseNumber, validateInputs, calculateTip, MAX_BILL, MAX_TIP_PERCENT, MAX_PEOPLE } = calc;
const ok = { bill: 100, tipPercent: 15, people: 1 };

describe('parseNumber', () => {
  test('acepta punto y coma decimal', () => {
    assert.equal(parseNumber('12.5'), 12.5);
    assert.equal(parseNumber('12,5'), 12.5);
  });
  test('recorta espacios', () => {
    assert.equal(parseNumber('  7 '), 7);
  });
  test('devuelve NaN para entradas no numericas', () => {
    for (const raw of ['', '   ', 'abc', '12abc', '1e999', '1,000.50', undefined, null]) {
      assert.ok(Number.isNaN(parseNumber(raw)), `esperaba NaN para ${JSON.stringify(raw)}`);
    }
  });
});

describe('calculateTip', () => {
  test('caso base', () => {
    assert.deepEqual(calculateTip(ok), { tipTotal: 15, total: 115, perPerson: 115, tipPerPerson: 15 });
  });
  test('caso dividido', () => {
    const r = calculateTip({ bill: 200, tipPercent: 10, people: 4 });
    assert.equal(r.tipTotal, 20);
    assert.equal(r.total, 220);
    assert.equal(r.perPerson, 55);
  });
  test('propina 0%', () => {
    const r = calculateTip({ bill: 50, tipPercent: 0, people: 2 });
    assert.equal(r.tipTotal, 0);
    assert.equal(r.total, 50);
    assert.equal(r.perPerson, 25);
  });
  test('redondeo 33.33 / 15% / 3 personas', () => {
    // 3333 centavos; propina 499.95 -> 500; total 3833; por persona 1277.67 -> 1278
    const r = calculateTip({ bill: 33.33, tipPercent: 15, people: 3 });
    assert.equal(r.tipTotal, 5);
    assert.equal(r.total, 38.33);
    assert.equal(r.perPerson, 12.78);
  });
  test('sin artefactos de coma flotante', () => {
    const a = calculateTip({ bill: 0.1, tipPercent: 20, people: 1 });
    assert.equal(a.tipTotal, 0.02);
    assert.equal(a.total, 0.12);
    const b = calculateTip({ bill: 19.99, tipPercent: 18, people: 1 });
    assert.equal(b.tipTotal, 3.6);
    assert.equal(b.total, 23.59);
    for (const v of [...Object.values(a), ...Object.values(b)]) {
      assert.equal(v, Math.round(v * 100) / 100);
    }
  });
  test('acepta strings con coma decimal', () => {
    assert.equal(calculateTip({ bill: '100,00', tipPercent: '15', people: '1' }).total, 115);
  });
  test('lanza RangeError con entradas invalidas', () => {
    assert.throws(() => calculateTip({ bill: 0, tipPercent: 15, people: 1 }), RangeError);
    assert.throws(() => calculateTip({}), RangeError);
  });
});

describe('validateInputs: rechazos', () => {
  const badBills = ['', 0, -5, NaN, Infinity, MAX_BILL + 1, 'abc'];
  for (const bill of badBills) {
    test(`bill ${String(bill)}`, () => {
      const r = validateInputs({ ...ok, bill });
      assert.equal(r.valid, false);
      assert.ok(r.errors.bill && r.errors.bill.length > 0);
      assert.equal(r.errors.tipPercent, undefined);
    });
  }
  for (const tipPercent of [-1, MAX_TIP_PERCENT + 1, '', NaN]) {
    test(`tipPercent ${String(tipPercent)}`, () => {
      const r = validateInputs({ ...ok, tipPercent });
      assert.ok(r.errors.tipPercent && r.errors.tipPercent.length > 0);
    });
  }
  for (const people of [0, -2, 2.5, '', MAX_PEOPLE + 1, '2,5']) {
    test(`people ${String(people)}`, () => {
      const r = validateInputs({ ...ok, people });
      assert.ok(r.errors.people && r.errors.people.length > 0);
    });
  }
  test('reporta multiples errores a la vez', () => {
    const r = validateInputs({ bill: '', tipPercent: -1, people: 0 });
    assert.equal(r.valid, false);
    assert.deepEqual(Object.keys(r.errors).sort(), ['bill', 'people', 'tipPercent']);
  });
});

describe('validateInputs: limites exactos', () => {
  test('acepta limites', () => {
    const cases = [
      { ...ok, tipPercent: 0 },
      { ...ok, tipPercent: MAX_TIP_PERCENT },
      { ...ok, people: 1 },
      { ...ok, people: MAX_PEOPLE },
      { ...ok, bill: 0.01 },
      { ...ok, bill: MAX_BILL },
    ];
    for (const c of cases) {
      const r = validateInputs(c);
      assert.equal(r.valid, true, JSON.stringify(c));
      assert.deepEqual(r.errors, {});
    }
  });
  test('constantes', () => {
    assert.equal(MAX_BILL, 1000000);
    assert.equal(MAX_TIP_PERCENT, 100);
    assert.equal(MAX_PEOPLE, 100);
  });
});

describe('casos adicionales', () => {
  test('rechaza bill 0.004 (menos de 1 centavo) y acepta 0.005', () => {
    const r = validateInputs({ ...ok, bill: 0.004 });
    assert.equal(r.valid, false);
    assert.ok(r.errors.bill);
    assert.equal(validateInputs({ ...ok, bill: 0.005 }).valid, true);
  });
  test('tipPerPerson divide la propina entre las personas', () => {
    const r = calculateTip({ bill: 200, tipPercent: 10, people: 4 });
    assert.equal(r.tipPerPerson, 5);
  });
  test('mensaje de personas lleva tilde', () => {
    assert.match(validateInputs({ ...ok, people: 2.5 }).errors.people, /número/);
  });
});
