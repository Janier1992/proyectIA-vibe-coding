/**
 * Logica pura de la calculadora de propinas (sin DOM).
 * Export dual: module.exports en Node, window.TipCalculator en navegador.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  } else {
    root.TipCalculator = api;
  }
})(typeof window !== 'undefined' ? window : globalThis, function () {
  'use strict';

  const MAX_BILL = 1000000;
  const MAX_TIP_PERCENT = 100;
  const MAX_PEOPLE = 100;

  const NUMBER_PATTERN = /^-?(\d+([.,]\d+)?|[.,]\d+)$/;

  const MESSAGES = Object.freeze({
    bill: 'Ingresa un monto mayor que 0 y hasta 1.000.000',
    tipPercent: 'Ingresa un porcentaje entre 0 y 100',
    people: 'Ingresa un número entero de personas entre 1 y 100',
  });

  /** Convierte texto a numero. Acepta coma o punto decimal; NaN si no es valido. */
  function parseNumber(raw) {
    if (typeof raw !== 'string') return NaN;
    const text = raw.trim();
    if (!NUMBER_PATTERN.test(text)) return NaN;
    const value = Number(text.replace(',', '.'));
    return Number.isFinite(value) ? value : NaN;
  }

  /** Acepta numeros (tal cual) o strings (via parseNumber). */
  function toNumber(value) {
    if (typeof value === 'number') return value;
    return parseNumber(value);
  }

  function isValidBill(value) {
    // Debe representar al menos 1 centavo tras el redondeo a centavos.
    return Number.isFinite(value) && value <= MAX_BILL && Math.round(value * 100) >= 1;
  }

  function isValidTip(value) {
    return Number.isFinite(value) && value >= 0 && value <= MAX_TIP_PERCENT;
  }

  function isValidPeople(value) {
    return Number.isInteger(value) && value >= 1 && value <= MAX_PEOPLE;
  }

  /** Valida las tres entradas y reporta todos los errores a la vez. */
  function validateInputs({ bill, tipPercent, people } = {}) {
    const errors = {};
    if (!isValidBill(toNumber(bill))) errors.bill = MESSAGES.bill;
    if (!isValidTip(toNumber(tipPercent))) errors.tipPercent = MESSAGES.tipPercent;
    if (!isValidPeople(toNumber(people))) errors.people = MESSAGES.people;
    return { valid: Object.keys(errors).length === 0, errors };
  }

  /**
   * Calcula propina y totales en centavos enteros.
   * Lanza RangeError si las entradas son invalidas (la UI valida antes).
   * Nota: perPerson * people puede diferir de total en 1-2 centavos; el total
   * mostrado es el exacto y no se reparte el resto (comportamiento aceptado).
   */
  function calculateTip({ bill, tipPercent, people } = {}) {
    const check = validateInputs({ bill, tipPercent, people });
    if (!check.valid) {
      throw new RangeError('Entradas invalidas: ' + Object.keys(check.errors).join(', '));
    }
    const billCents = Math.round(toNumber(bill) * 100);
    const tipCents = Math.round((billCents * toNumber(tipPercent)) / 100);
    const totalCents = billCents + tipCents;
    const peopleCount = toNumber(people);
    return {
      tipTotal: tipCents / 100,
      total: totalCents / 100,
      perPerson: Math.round(totalCents / peopleCount) / 100,
      tipPerPerson: Math.round(tipCents / peopleCount) / 100,
    };
  }

  return Object.freeze({
    MAX_BILL,
    MAX_TIP_PERCENT,
    MAX_PEOPLE,
    parseNumber,
    validateInputs,
    calculateTip,
  });
});
