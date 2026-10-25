/* Capa DOM: unico archivo que toca el DOM. Solo escribe con textContent y value. */
(function () {
  'use strict';

  const CURRENCY = 'USD';
  const FIELDS = ['bill', 'tipPercent', 'people'];
  const DEFAULTS = { bill: '', tipPercent: '15', people: '1' };

  const calc = window.TipCalculator;
  const formatter = new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency: CURRENCY,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  const EMPTY_BILL = 'Ingresa el monto de la cuenta para ver el resultado';
  const EMPTY_FIX = 'Corrige los campos marcados para ver el resultado';

  const byId = (id) => document.getElementById(id);
  const inputs = Object.fromEntries(FIELDS.map((f) => [f, byId(f)]));
  const touched = { bill: false, tipPercent: false, people: false };

  function readValues() {
    return Object.fromEntries(FIELDS.map((f) => [f, inputs[f].value]));
  }

  function showFieldError(field, message) {
    const el = byId(field + '-error');
    const show = Boolean(message) && touched[field];
    el.textContent = show ? message : '';
    if (show) inputs[field].setAttribute('aria-invalid', 'true');
    else inputs[field].removeAttribute('aria-invalid');
  }

  function emptyMessage(errors) {
    return errors.bill ? EMPTY_BILL : EMPTY_FIX;
  }

  function showResults(result, errors) {
    const list = byId('results-list');
    byId('empty-state').hidden = Boolean(result);
    byId('empty-state').textContent = emptyMessage(errors);
    list.hidden = !result;
    if (!result) return;
    byId('tip-total').textContent = formatter.format(result.tipTotal);
    byId('total').textContent = formatter.format(result.total);
    byId('per-person').textContent = formatter.format(result.perPerson);
  }

  function render() {
    const values = readValues();
    const { valid, errors } = calc.validateInputs(values);
    FIELDS.forEach((f) => showFieldError(f, errors[f]));
    showResults(valid ? calc.calculateTip(values) : null, errors);
    syncShortcuts(values.tipPercent);
  }

  function syncShortcuts(tipValue) {
    document.querySelectorAll('[data-tip]').forEach((btn) => {
      btn.setAttribute('aria-pressed', String(btn.dataset.tip === tipValue.trim()));
    });
  }

  function onInput(field) {
    touched[field] = true;
    render();
  }

  function reset() {
    FIELDS.forEach((f) => {
      inputs[f].value = DEFAULTS[f];
      touched[f] = false;
    });
    render();
    inputs.bill.focus();
  }

  function init() {
    FIELDS.forEach((f) => {
      inputs[f].addEventListener('input', () => onInput(f));
      inputs[f].addEventListener('blur', () => onInput(f));
    });
    document.querySelectorAll('[data-tip]').forEach((btn) => {
      btn.addEventListener('click', () => {
        inputs.tipPercent.value = btn.dataset.tip;
        onInput('tipPercent');
      });
    });
    byId('reset').addEventListener('click', reset);
    byId('tip-form').addEventListener('submit', (e) => e.preventDefault());
    render();
  }

  init();
})();
