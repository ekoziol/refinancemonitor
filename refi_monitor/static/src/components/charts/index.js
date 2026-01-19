// Chart infrastructure for Recharts
export { default as BaseChart } from './BaseChart';
export {
  defaultAxisConfig,
  defaultGridConfig,
  defaultMargin,
  createCurrencyAxisProps,
  createPercentAxisProps,
  createTimeAxisProps,
} from './BaseChart';

// Reusable chart components
export { default as ChartTooltip, formatTooltipValue, createTooltip } from './ChartTooltip';
export { default as ChartLegend, createLegend, SimpleLegend } from './ChartLegend';

// Color palette
export {
  chartColors,
  chartColorScale,
  semanticColors,
  areaColors,
  gridColors,
  referenceColors,
  getChartColor,
  generateColorScale,
} from './colors';
