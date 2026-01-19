export { default as ChartWrapper } from './ChartWrapper';
export { default as MetricCards } from './MetricCards';
export { default as SavingsImpactChart } from './SavingsImpactChart';
export { default as TimelineVisualization } from './TimelineVisualization';

// Chart infrastructure (Recharts setup)
export {
  BaseChart,
  ChartTooltip,
  ChartLegend,
  SimpleLegend,
  chartColors,
  chartColorScale,
  semanticColors,
  areaColors,
  gridColors,
  referenceColors,
  getChartColor,
  generateColorScale,
  defaultAxisConfig,
  defaultGridConfig,
  defaultMargin,
  createCurrencyAxisProps,
  createPercentAxisProps,
  createTimeAxisProps,
  formatTooltipValue,
  createTooltip,
  createLegend,
} from './charts';

// UI Primitives (shadcn/ui)
export {
  Button,
  buttonVariants,
  Card,
  CardHeader,
  CardFooter,
  CardTitle,
  CardDescription,
  CardContent,
  Badge,
  badgeVariants,
  Input,
} from './ui';

// Layout components
export {
  Sidebar,
  Icons,
  DashboardLayout,
  DashboardHeader,
  DashboardMain,
  DashboardGrid,
  DashboardSection,
  useDashboardLayout,
} from './layout';
