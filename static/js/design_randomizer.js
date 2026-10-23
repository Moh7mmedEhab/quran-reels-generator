(function exposeDesignRandomizer(root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.QuranReelsDesign = api;
})(typeof window !== 'undefined' ? window : globalThis, function createDesignRandomizer() {
  function parseHexColor(value) {
    const match = /^#([\da-f]{6})$/i.exec(String(value || ''));
    if (!match) return null;
    return [0, 2, 4].map(index => parseInt(match[1].slice(index, index + 2), 16));
  }

  function linearChannel(channel) {
    const value = Number(channel) / 255;
    return value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4;
  }

  function relativeLuminance(rgb) {
    return .2126 * linearChannel(rgb[0])
      + .7152 * linearChannel(rgb[1])
      + .0722 * linearChannel(rgb[2]);
  }

  function contrastRatio(first, second) {
    const firstRgb = parseHexColor(first);
    const secondRgb = parseHexColor(second);
    if (!firstRgb || !secondRgb) return 0;
    const firstLuminance = relativeLuminance(firstRgb);
    const secondLuminance = relativeLuminance(secondRgb);
    const light = Math.max(firstLuminance, secondLuminance);
    const dark = Math.min(firstLuminance, secondLuminance);
    return (light + .05) / (dark + .05);
  }

  function filterContrastSafeColors(elements, colorValues, {
    panelColor = '#090806', panelOpacity = .85,
    backgroundColor = '#ffffff', minimumContrast = 4.5,
  } = {}) {
    const panel = parseHexColor(panelColor);
    const background = parseHexColor(backgroundColor);
    if (!panel || !background || !Number.isFinite(panelOpacity)
        || panelOpacity < 0 || panelOpacity > 1 || !Number.isFinite(minimumContrast)) return [];
    const composite = `#${panel.map((channel, index) => Math.round(
      channel * panelOpacity + background[index] * (1 - panelOpacity),
    ).toString(16).padStart(2, '0')).join('')}`;
    return elements.filter(element => contrastRatio(
      colorValues?.[element?.dataset?.color], composite,
    ) >= minimumContrast);
  }

  return Object.freeze({parseHexColor, contrastRatio, filterContrastSafeColors});
});
