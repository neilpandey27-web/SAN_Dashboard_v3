declare module 'react-plotly.js' {
  import { Component } from 'react';
  import { PlotParams } from 'plotly.js';

  export interface PlotProps extends Partial<PlotParams> {
    data: Partial<PlotParams['data']>;
    layout?: Partial<PlotParams['layout']>;
    config?: Partial<PlotParams['config']>;
    frames?: Partial<PlotParams['frames']>;
    onInitialized?: (figure: Readonly<PlotParams>, graphDiv: Readonly<HTMLElement>) => void;
    onUpdate?: (figure: Readonly<PlotParams>, graphDiv: Readonly<HTMLElement>) => void;
    onPurge?: (figure: Readonly<PlotParams>, graphDiv: Readonly<HTMLElement>) => void;
    onError?: (err: Readonly<Error>) => void;
    divId?: string;
    className?: string;
    style?: React.CSSProperties;
    useResizeHandler?: boolean;
    debug?: boolean;
    onAfterExport?: () => void;
    onAfterPlot?: () => void;
    onAnimated?: () => void;
    onAnimatingFrame?: (event: Readonly<PlotAnimationEvent>) => void;
    onAnimationInterrupted?: () => void;
    onAutoSize?: () => void;
    onBeforeExport?: () => void;
    onBeforeHover?: (event: Readonly<PlotMouseEvent>) => void;
    onButtonClicked?: (event: Readonly<PlotButtonClickEvent>) => void;
    onClick?: (event: Readonly<PlotMouseEvent>) => void;
    onClickAnnotation?: (event: Readonly<PlotAnnotationClickEvent>) => void;
    onDeselect?: () => void;
    onDoubleClick?: () => void;
    onFramework?: () => void;
    onHover?: (event: Readonly<PlotHoverEvent>) => void;
    onLegendClick?: (event: Readonly<PlotLegendClickEvent>) => boolean;
    onLegendDoubleClick?: (event: Readonly<PlotLegendClickEvent>) => boolean;
    onRelayout?: (event: Readonly<PlotRelayoutEvent>) => void;
    onRelayouting?: (event: Readonly<PlotRelayoutEvent>) => void;
    onRestyle?: (event: Readonly<PlotRestyleEvent>) => void;
    onRedraw?: () => void;
    onSelected?: (event: Readonly<PlotSelectionEvent>) => void;
    onSelecting?: (event: Readonly<PlotSelectionEvent>) => void;
    onSliderChange?: (event: Readonly<PlotSliderChangeEvent>) => void;
    onSliderEnd?: (event: Readonly<PlotSliderEndEvent>) => void;
    onSliderStart?: (event: Readonly<PlotSliderStartEvent>) => void;
    onSunburstClick?: (event: Readonly<PlotSunburstClickEvent>) => void;
    onTransitioning?: () => void;
    onTransitionInterrupted?: () => void;
    onUnhover?: (event: Readonly<PlotMouseEvent>) => void;
    onWebGlContextLost?: () => void;
  }

  export interface PlotAnimationEvent {
    name: string;
    frame: object;
    animation: object;
  }

  export interface PlotMouseEvent {
    points: PlotDatum[];
    event: MouseEvent;
  }

  export interface PlotDatum {
    curveNumber: number;
    pointNumber: number;
    pointIndex: number;
    x: number | string;
    y: number | string;
    z?: number | string;
    data: object;
    fullData: object;
  }

  export interface PlotButtonClickEvent {
    menu: object;
    button: object;
    active: number;
  }

  export interface PlotAnnotationClickEvent {
    index: number;
    annotation: object;
    fullAnnotation: object;
  }

  export interface PlotHoverEvent {
    points: PlotDatum[];
    event: MouseEvent;
    xaxes: object[];
    yaxes: object[];
    xvals: number[];
    yvals: number[];
  }

  export interface PlotLegendClickEvent {
    curveNumber: number;
    expandedIndex: number;
    data: object[];
    fullData: object[];
    event: MouseEvent;
  }

  export interface PlotRelayoutEvent {
    [key: string]: any;
  }

  export interface PlotRestyleEvent {
    [key: string]: any;
  }

  export interface PlotSelectionEvent {
    points: PlotDatum[];
    range?: {
      x: [number, number];
      y: [number, number];
    };
    lassoPoints?: {
      x: number[];
      y: number[];
    };
  }

  export interface PlotSliderChangeEvent {
    slider: object;
    step: object;
    interaction: boolean;
    previousActive: number;
  }

  export interface PlotSliderEndEvent {
    slider: object;
    step: object;
  }

  export interface PlotSliderStartEvent {
    slider: object;
  }

  export interface PlotSunburstClickEvent {
    points: PlotDatum[];
    event: MouseEvent;
    nextLevel: string;
  }

  export default class Plot extends Component<PlotProps> {}
}
