/* Numeric calculations only; not a diagnostic or treatment decision tool. */
(function (root) {
  'use strict';

  function value(input, name, optional) {
    if ((input === '' || input === null || input === undefined) && optional) return null;
    if (input === '' || input === null || input === undefined) {
      throw new Error(name + ' is required.');
    }
    const number = Number(input);
    if (!Number.isFinite(number) || number < 0) {
      throw new Error(name + ' must be a finite, non-negative number.');
    }
    return number;
  }

  function calculate(data) {
    const measured = value(data.measured, 'Measured osmolality');
    const sodium = value(data.sodium, 'Sodium');
    const glucose = value(data.glucose, 'Glucose');
    const bun = value(data.bun, 'BUN');
    const ethanol = value(data.ethanol, 'Ethanol', true);
    const chloride = value(data.chloride, 'Chloride', true);
    const bicarbonate = value(data.bicarbonate, 'Bicarbonate', true);
    if ((chloride === null) !== (bicarbonate === null)) {
      throw new Error('Provide both chloride and bicarbonate, or leave both blank.');
    }
    const calculated = 2 * sodium + glucose / 18 + bun / 2.8 + (ethanol === null ? 0 : ethanol / 4.6);
    return {
      calculatedOsmolarity: Math.round(calculated * 100) / 100,
      osmolalGap: Math.round((measured - calculated) * 100) / 100,
      anionGap: chloride === null ? null : Math.round((sodium - chloride - bicarbonate) * 100) / 100,
      ethanolIncluded: ethanol !== null
    };
  }

  function init() {
    const form = document.getElementById('calculator');
    if (!form) return;
    const output = document.getElementById('results');
    const error = document.getElementById('error');
    const exportButton = document.getElementById('export');
    const fields = ['measured', 'sodium', 'glucose', 'bun', 'ethanol', 'chloride', 'bicarbonate'];
    let latest = null;

    function setResult(id, val) {
      document.getElementById(id).textContent = val === null ? 'Not calculated' : val.toFixed(2);
    }

    function resetResults() {
      latest = null;
      output.hidden = true;
      exportButton.disabled = true;
    }

    form.addEventListener('input', function () {
      error.textContent = '';
      resetResults();
    });
    form.addEventListener('reset', function () {
      error.textContent = '';
      resetResults();
    });

    form.addEventListener('submit', function (event) {
      event.preventDefault();
      const data = Object.fromEntries(fields.map(k => [k, document.getElementById(k).value.trim()]));
      try {
        const result = calculate(data);
        latest = { data: data, result: result };
        setResult('calculated-osm', result.calculatedOsmolarity);
        setResult('osmol-gap', result.osmolalGap);
        setResult('anion-gap', result.anionGap);
        document.getElementById('ethanol-note').textContent = result.ethanolIncluded
          ? 'Ethanol contribution included (ethanol / 4.6).'
          : 'Ethanol was not provided. The gap is not ethanol-adjusted.';
        output.hidden = false;
        exportButton.disabled = false;
        error.textContent = '';
      } catch (e) {
        resetResults();
        error.textContent = e.message;
      }
    });

    exportButton.addEventListener('click', function () {
      if (!latest) return;
      const data = latest.data;
      const result = latest.result;
      const row = fields.map(k => data[k]).concat([
        result.calculatedOsmolarity, result.osmolalGap,
        result.anionGap === null ? '' : result.anionGap, result.ethanolIncluded
      ]);
      const names = fields.concat(['calculated_osmolarity', 'osmolal_gap', 'anion_gap', 'ethanol_included']);
      const csv = names.join(',') + '\r\n' + row.join(',') + '\r\n';
      const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
      const link = document.createElement('a');
      link.href = url;
      link.download = 'toxic-alcohol-gap-calculation.csv';
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    });
  }

  root.ToxicAlcoholCalculator = { calculate: calculate };
  if (typeof module !== 'undefined' && module.exports) module.exports = { calculate: calculate };
  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
    else init();
  }
})(typeof window === 'undefined' ? globalThis : window);
