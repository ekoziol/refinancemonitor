import React, { useState, useEffect, useMemo } from 'react';
import { cn } from '../lib/utils';

/**
 * Animated SVG gauge showing proximity to refinance trigger point.
 * Displays a semi-circular arc that fills based on how close current
 * conditions are to the user's refinancing target.
 *
 * @param {Object} props
 * @param {number} props.value - Current proximity value (0-100)
 * @param {number} props.targetRate - Target interest rate (optional display)
 * @param {number} props.currentRate - Current market rate (optional display)
 * @param {string} props.label - Label text below gauge
 * @param {string} props.size - Gauge size: 'sm', 'md', 'lg'
 * @param {boolean} props.animate - Enable/disable animation
 * @param {string} props.className - Additional CSS classes
 */
function ProximityGauge({
  value = 0,
  targetRate,
  currentRate,
  label = 'Refi Proximity',
  size = 'md',
  animate = true,
  className,
}) {
  const [animatedValue, setAnimatedValue] = useState(animate ? 0 : value);

  // Animate value change
  useEffect(() => {
    if (!animate) {
      setAnimatedValue(value);
      return;
    }

    const startValue = animatedValue;
    const endValue = Math.min(100, Math.max(0, value));
    const duration = 800;
    const startTime = performance.now();

    const animateFrame = (currentTime) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // Ease-out cubic
      const easeOut = 1 - Math.pow(1 - progress, 3);
      const current = startValue + (endValue - startValue) * easeOut;

      setAnimatedValue(current);

      if (progress < 1) {
        requestAnimationFrame(animateFrame);
      }
    };

    requestAnimationFrame(animateFrame);
  }, [value, animate]);

  // Size configurations
  const sizes = {
    sm: { width: 120, height: 80, strokeWidth: 8, fontSize: 16 },
    md: { width: 180, height: 110, strokeWidth: 12, fontSize: 24 },
    lg: { width: 240, height: 140, strokeWidth: 16, fontSize: 32 },
  };

  const config = sizes[size] || sizes.md;
  const { width, height, strokeWidth, fontSize } = config;

  // SVG arc calculations
  const centerX = width / 2;
  const centerY = height - 10;
  const radius = Math.min(centerX, centerY) - strokeWidth;

  // Arc path for semi-circle (180 degrees)
  const startAngle = Math.PI;
  const endAngle = 0;
  const valueAngle = startAngle - (animatedValue / 100) * Math.PI;

  const startX = centerX + radius * Math.cos(startAngle);
  const startY = centerY + radius * Math.sin(startAngle);
  const endX = centerX + radius * Math.cos(endAngle);
  const endY = centerY + radius * Math.sin(endAngle);

  const valueX = centerX + radius * Math.cos(valueAngle);
  const valueY = centerY + radius * Math.sin(valueAngle);

  // Background arc path
  const bgArcPath = `M ${startX} ${startY} A ${radius} ${radius} 0 0 1 ${endX} ${endY}`;

  // Value arc path
  const largeArcFlag = animatedValue > 50 ? 1 : 0;
  const valueArcPath =
    animatedValue > 0
      ? `M ${startX} ${startY} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${valueX} ${valueY}`
      : '';

  // Color based on value
  const getGaugeColor = useMemo(() => {
    if (animatedValue >= 80) return '#22c55e'; // green-500
    if (animatedValue >= 60) return '#84cc16'; // lime-500
    if (animatedValue >= 40) return '#eab308'; // yellow-500
    if (animatedValue >= 20) return '#f97316'; // orange-500
    return '#ef4444'; // red-500
  }, [animatedValue]);

  // Status text based on value
  const getStatusText = () => {
    if (animatedValue >= 80) return 'Excellent';
    if (animatedValue >= 60) return 'Good';
    if (animatedValue >= 40) return 'Fair';
    if (animatedValue >= 20) return 'Low';
    return 'Not Ready';
  };

  return (
    <div
      className={cn(
        'bg-gradient-to-br from-gray-900 to-gray-800 rounded-xl p-6 shadow-lg',
        className
      )}
    >
      <div className="flex flex-col items-center">
        <svg
          width={width}
          height={height}
          viewBox={`0 0 ${width} ${height}`}
          className="overflow-visible"
        >
          {/* Background arc */}
          <path
            d={bgArcPath}
            fill="none"
            stroke="#374151"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />

          {/* Gradient definition */}
          <defs>
            <linearGradient
              id={`gauge-gradient-${size}`}
              x1="0%"
              y1="0%"
              x2="100%"
              y2="0%"
            >
              <stop offset="0%" stopColor="#ef4444" />
              <stop offset="50%" stopColor="#eab308" />
              <stop offset="100%" stopColor="#22c55e" />
            </linearGradient>
          </defs>

          {/* Value arc */}
          {valueArcPath && (
            <path
              d={valueArcPath}
              fill="none"
              stroke={getGaugeColor}
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              className="transition-all duration-300"
              style={{
                filter: `drop-shadow(0 0 8px ${getGaugeColor}40)`,
              }}
            />
          )}

          {/* Center value display */}
          <text
            x={centerX}
            y={centerY - 10}
            textAnchor="middle"
            fill="white"
            fontSize={fontSize}
            fontWeight="bold"
          >
            {Math.round(animatedValue)}%
          </text>

          {/* Status text */}
          <text
            x={centerX}
            y={centerY + fontSize * 0.6}
            textAnchor="middle"
            fill={getGaugeColor}
            fontSize={fontSize * 0.5}
            fontWeight="medium"
          >
            {getStatusText()}
          </text>
        </svg>

        {/* Label */}
        <p className="text-sm text-gray-400 mt-2">{label}</p>

        {/* Rate comparison */}
        {(targetRate !== undefined || currentRate !== undefined) && (
          <div className="flex justify-between w-full mt-4 px-2 text-xs text-gray-500">
            {currentRate !== undefined && (
              <span>Current: {currentRate.toFixed(2)}%</span>
            )}
            {targetRate !== undefined && (
              <span>Target: {targetRate.toFixed(2)}%</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default ProximityGauge;
