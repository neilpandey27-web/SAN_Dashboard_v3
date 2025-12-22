'use client';

import dynamic from 'next/dynamic';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface BarChartProps {
  data: {
    name: string;
    used_tb?: number;
    available_tb?: number;
    total_tb?: number;
    value?: number;
    capacity_tb?: number;
    savings_tb?: number;
    count?: number;
  }[];
  title?: string;
  type?: 'stacked' | 'horizontal' | 'vertical' | 'histogram';
  height?: number;
  colors?: string[];
}

export default function BarChart({ 
  data, 
  title, 
  type = 'stacked', 
  height = 300,
  colors = ['#2a9fd6', '#77b300']
}: BarChartProps) {
  const getTraces = () => {
    switch (type) {
      case 'stacked':
        return [
          {
            x: data.map(d => d.name),
            y: data.map(d => d.used_tb || 0),
            name: 'Used (TB)',
            type: 'bar',
            marker: { color: colors[0] },
          },
          {
            x: data.map(d => d.name),
            y: data.map(d => d.available_tb || 0),
            name: 'Available (TB)',
            type: 'bar',
            marker: { color: colors[1] },
          },
        ];
      
      case 'horizontal':
        return [
          {
            y: data.map(d => d.name),
            x: data.map(d => d.value || d.used_tb || d.capacity_tb || 0),
            type: 'bar',
            orientation: 'h',
            marker: { color: colors[0] },
          },
        ];
      
      case 'vertical':
        return [
          {
            x: data.map(d => d.name),
            y: data.map(d => d.value || d.savings_tb || 0),
            type: 'bar',
            marker: { color: colors[1] },
          },
        ];
      
      case 'histogram':
        return [
          {
            x: data.map(d => d.name),
            y: data.map(d => d.count || d.value || 0),
            type: 'bar',
            marker: { color: colors[0] },
          },
        ];
      
      default:
        return [];
    }
  };

  const getLayout = () => {
    const baseLayout = {
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      font: { color: '#ffffff', size: 11 },
      margin: { t: 30, b: 80, l: 60, r: 20 },
      height: height,
      showlegend: type === 'stacked',
      legend: {
        orientation: 'h' as const,
        y: -0.2,
        x: 0.5,
        xanchor: 'center' as const,
      },
      xaxis: {
        gridcolor: '#333',
        tickangle: -45,
      },
      yaxis: {
        gridcolor: '#333',
        title: type === 'stacked' || type === 'vertical' ? 'TB' : undefined,
      },
    };

    if (type === 'stacked') {
      return { ...baseLayout, barmode: 'stack' as const };
    }
    
    if (type === 'horizontal') {
      return {
        ...baseLayout,
        margin: { t: 30, b: 40, l: 150, r: 20 },
        xaxis: { gridcolor: '#333', title: 'TB' },
        yaxis: { gridcolor: '#333' },
      };
    }

    return baseLayout;
  };

  return (
    <div className="chart-container">
      {title && <h6 className="chart-title">{title}</h6>}
      <Plot
        data={getTraces() as any}
        layout={getLayout() as any}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: '100%' }}
      />
    </div>
  );
}
