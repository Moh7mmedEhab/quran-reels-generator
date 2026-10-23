const test = require('node:test');
const assert = require('node:assert/strict');
const {formatSurahCoverage} = require('../static/js/reciter_coverage.js');

test('formats a full Quran recording as full coverage', () => {
  assert.equal(formatSurahCoverage(Array.from({length:114}, (_, index) => index + 1)), 'all 114 Surahs');
});

test('compresses available surahs into readable ranges', () => {
  const salman = [1, 2, 3, 10, 11, 14, 16, 19, 23, 25, 32, 36, 38, 39, 40,
    46, 48, 50, 52, 55, 56, 58, 59, 61, 62, 63, 64, ...Array.from({length:49}, (_, index) => index + 66)];
  assert.equal(formatSurahCoverage(salman),
    '76 of 114 Surahs (1–3, 10–11, 14, 16, 19, 23, 25, 32, 36, 38–40, 46, 48, 50, 52, 55–56, 58–59, 61–64, 66–114)');
});

test('handles missing Surahs, duplicates, and invalid values', () => {
  assert.equal(formatSurahCoverage([114, 1, 2, 3, 3, 0, 115, '2']),
    '4 of 114 Surahs (1–3, 114)');
  assert.equal(formatSurahCoverage([]), 'No Surahs listed');
  assert.equal(formatSurahCoverage(null), 'Coverage not listed');
});
