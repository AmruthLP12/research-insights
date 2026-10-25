/**
 * chart-theme.js - Shared Chart.js defaults & palette helpers for Research Insights.
 * Compatible with Chart.js v4.x.
 */
(function (global) {
  'use strict';

  var palette = {
    primary: '#1E40AF',       // Navy blue
    primaryLight: '#3B82F6',  // Blue
    secondary: '#0D9488',     // Teal
    accent: '#F59E0B',        // Amber
    neutral: '#64748B',       // Slate
    info: '#0284C7',          // Sky
    success: '#10B981',       // Emerald
    warning: '#D97706',       // Dark Amber
    error: '#EF4444',         // Rose / Red
  };

  // Coordinated palette sequence for categorical and multi-series charts
  var colors = [
    '#1E40AF', // Primary Navy
    '#0D9488', // Teal
    '#3B82F6', // Blue
    '#F59E0B', // Amber
    '#8B5CF6', // Purple
    '#10B981', // Emerald
    '#EC4899', // Pink
    '#06B6D4', // Cyan
    '#6366F1', // Indigo
    '#F97316', // Orange
    '#64748B', // Slate
    '#14B8A6', // Light Teal
  ];

  function applyDefaults() {
    if (!global.Chart) return;

    var defaults = global.Chart.defaults;
    if (!defaults) return;

    // Typography
    if (defaults.font) {
      defaults.font.family = 'Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
      defaults.font.size = 12;
    }
    defaults.color = '#64748B';
    defaults.responsive = true;
    defaults.maintainAspectRatio = false;

    // Plugins defaults
    if (defaults.plugins) {
      if (defaults.plugins.legend && defaults.plugins.legend.labels) {
        defaults.plugins.legend.labels.usePointStyle = true;
        defaults.plugins.legend.labels.boxWidth = 8;
        defaults.plugins.legend.labels.color = '#475569';
      }
      if (defaults.plugins.tooltip) {
        defaults.plugins.tooltip.backgroundColor = '#1E293B';
        defaults.plugins.tooltip.titleColor = '#F8FAFC';
        defaults.plugins.tooltip.bodyColor = '#F8FAFC';
        defaults.plugins.tooltip.padding = 10;
        defaults.plugins.tooltip.cornerRadius = 6;
      }
    }

    // Grid / Scale defaults
    if (defaults.scale && defaults.scale.grid) {
      defaults.scale.grid.color = '#F1F5F9';
    }
  }

  // Apply immediately if Chart is already loaded
  if (global.Chart) {
    applyDefaults();
  }

  // Re-run on DOMContentLoaded as safety fallback
  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', applyDefaults);
    } else {
      applyDefaults();
    }
  }

  global.ChartTheme = {
    palette: palette,
    colors: colors,
    getColor: function (index) {
      return colors[Math.abs(index) % colors.length];
    },
    getColors: function (count) {
      var result = [];
      for (var i = 0; i < count; i++) {
        result.push(colors[i % colors.length]);
      }
      return result;
    },
    applyDefaults: applyDefaults,
  };
})(typeof window !== 'undefined' ? window : this);

