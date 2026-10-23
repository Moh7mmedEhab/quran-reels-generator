(function (root) {
  'use strict';

  function formatSurahCoverage(numbers) {
    if (!Array.isArray(numbers)) return 'Coverage not listed';
    const surahs = [...new Set(numbers.map(Number).filter(number =>
      Number.isInteger(number) && number >= 1 && number <= 114))].sort((a, b) => a - b);
    if (!surahs.length) return 'No Surahs listed';
    if (surahs.length === 114 && surahs[0] === 1 && surahs[113] === 114) {
      return 'all 114 Surahs';
    }

    const ranges = [];
    let start = surahs[0];
    let end = start;
    for (const number of surahs.slice(1)) {
      if (number === end + 1) {
        end = number;
        continue;
      }
      ranges.push(start === end ? String(start) : `${start}–${end}`);
      start = end = number;
    }
    ranges.push(start === end ? String(start) : `${start}–${end}`);
    return `${surahs.length} of 114 Surahs (${ranges.join(', ')})`;
  }

  root.QuranReciterCoverage = Object.freeze({ formatSurahCoverage });
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = root.QuranReciterCoverage;
  }
})(typeof window !== 'undefined' ? window : globalThis);
