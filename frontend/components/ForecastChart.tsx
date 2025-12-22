'use client';

import dynamic from 'next/dynamic';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface ForecastChartProps {
  data: {
    name: string;
    utilization_pct: number;
    days_until_full: number;
    storage_system?: string;
  }[];
  title?: string;
  height?: number;
}

export default function ForecastChart({ data, title = 'Capacity Forecast', height = 350 }: ForecastChartProps) {
  return (
    <div className="chart-container">
      {title && <h6 className="chart-title">{title}</h6>}
      <Plot
        data={[
          {
            x: data.map(d => d.name),
            y: data.map(d => d.utilization_pct),
            name: 'Utilization %',
            type: 'bar',
            marker: { 
              color: data.map(d => 
                d.utilization_pct >= 90 ? '#cc0000' : 
                d.utilization_pct >= 70 ? '#ff8800' : 
                '#77b300'
              ),
            },
            yaxis: 'y',
            hovertemplate: '%{x}<br>Utilization: %{y:.1f}%<extra></extra>',
          },
          {
            x: data.map(d => d.name),
            y: data.map(d => d.days_until_full),
            name: 'Days Until Full',
            type: 'scatter',
            mode: 'lines+markers',
            marker: { color: '#2a9fd6', size: 10 },
            line: { color: '#2a9fd6', width: 2 },
            yaxis: 'y2',
            hovertemplate: '%{x}<br>Days: %{y}<extra></extra>',
          },
        ]}
        layout={{
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          font: { color: '#ffffff', size: 11 },
          margin: { t: 30, b: 100, l: 60, r: 60 },
          height: height,
          showlegend: true,
          legend: {
            orientation: 'h',
            y: -0.3,
            x: 0.5,
            xanchor: 'center',
          },
          xaxis: {
            gridcolor: '#333',
            tickangle: -45,
          },
          yaxis: {
            title: 'Utilization %',
            gridcolor: '#333',
            titlefont: { color: '#ff8800' },
            tickfont: { color: '#ff8800' },
            range: [0, 100],
          },
          yaxis2: {
            title: 'Days Until Full',
            overlaying: 'y',
            side: 'right',
            titlefont: { color: '#2a9fd6' },
            tickfont: { color: '#2a9fd6' },
            gridcolor: 'transparent',
          },
        }}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: '100%' }}
      />
    </div>
  );
}
