'use client';

import dynamic from 'next/dynamic';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface PieChartProps {
  data: {
    type: string;
    capacity_tb?: number;
    value?: number;
  }[];
  title?: string;
  height?: number;
}

export default function PieChart({ data, title, height = 300 }: PieChartProps) {
  const colors = ['#2a9fd6', '#77b300', '#ff8800', '#cc0000', '#9933cc', '#00cccc'];
  
  return (
    <div className="chart-container">
      {title && <h6 className="chart-title">{title}</h6>}
      <Plot
        data={[
          {
            labels: data.map(d => d.type),
            values: data.map(d => d.capacity_tb || d.value || 0),
            type: 'pie',
            hole: 0.4,
            marker: {
              colors: colors,
            },
            textinfo: 'label+percent',
            textposition: 'outside',
            textfont: { color: '#ffffff', size: 11 },
            hovertemplate: '%{label}<br>%{value:.1f} TB<br>%{percent}<extra></extra>',
          },
        ]}
        layout={{
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          font: { color: '#ffffff' },
          margin: { t: 30, b: 30, l: 30, r: 30 },
          height: height,
          showlegend: true,
          legend: {
            orientation: 'h',
            y: -0.1,
            x: 0.5,
            xanchor: 'center',
            font: { size: 10 },
          },
        }}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: '100%' }}
      />
    </div>
  );
}
