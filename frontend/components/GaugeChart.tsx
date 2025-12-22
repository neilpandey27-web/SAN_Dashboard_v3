'use client';

import dynamic from 'next/dynamic';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface GaugeChartProps {
  value: number;
  title?: string;
  height?: number;
}

export default function GaugeChart({ value, title = 'Overall Utilization', height = 250 }: GaugeChartProps) {
  const getColor = (val: number) => {
    if (val >= 90) return '#cc0000';
    if (val >= 70) return '#ff8800';
    return '#77b300';
  };

  return (
    <div className="chart-container">
      {title && <h6 className="chart-title">{title}</h6>}
      <Plot
        data={[
          {
            type: 'indicator',
            mode: 'gauge+number',
            value: value,
            number: { suffix: '%', font: { size: 36, color: '#ffffff' } },
            gauge: {
              axis: {
                range: [0, 100],
                tickwidth: 1,
                tickcolor: '#ffffff',
                tickfont: { color: '#ffffff' },
              },
              bar: { color: getColor(value), thickness: 0.8 },
              bgcolor: '#1a1a1a',
              borderwidth: 0,
              steps: [
                { range: [0, 50], color: 'rgba(119, 179, 0, 0.2)' },
                { range: [50, 70], color: 'rgba(119, 179, 0, 0.3)' },
                { range: [70, 85], color: 'rgba(255, 136, 0, 0.3)' },
                { range: [85, 95], color: 'rgba(255, 136, 0, 0.4)' },
                { range: [95, 100], color: 'rgba(204, 0, 0, 0.4)' },
              ],
              threshold: {
                line: { color: '#ff0000', width: 4 },
                thickness: 0.75,
                value: 90,
              },
            },
          },
        ]}
        layout={{
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          font: { color: '#ffffff' },
          margin: { t: 20, b: 20, l: 30, r: 30 },
          height: height,
        }}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: '100%' }}
      />
    </div>
  );
}
