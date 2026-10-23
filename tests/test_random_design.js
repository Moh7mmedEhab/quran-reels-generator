const assert = require('node:assert/strict');
const test = require('node:test');
const {contrastRatio, filterContrastSafeColors} = require('../static/js/design_randomizer.js');

test('random design filters caption colors against its strongest light-background panel blend', () => {
  const colors = {
    white:'#ffffff', gold:'#ffd166', coral:'#ff8066', pink:'#ff6fb5',
    blue:'#006aff', ink:'#27241e',
  };
  const options = Object.keys(colors).map(color => ({dataset:{color}}));
  const safe = filterContrastSafeColors(options, colors);
  assert.deepEqual(safe.map(option => option.dataset.color), ['white','gold','coral','pink']);
  assert.ok(contrastRatio(colors.white, '#353433') >= 4.5);
  assert.ok(contrastRatio(colors.blue, '#353433') < 4.5);
  assert.ok(contrastRatio(colors.ink, '#353433') < 4.5);
});

test('random design returns no palette choices when its panel colors are invalid', () => {
  assert.deepEqual(filterContrastSafeColors([{dataset:{color:'white'}}], {white:'#ffffff'}, {
    panelColor:'transparent',
  }), []);
});
