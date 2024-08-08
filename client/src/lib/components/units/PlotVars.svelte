


<script lang="ts">
  import { onMount, afterUpdate } from 'svelte';
  import { API_ENDPOINTS } from '$lib/utils/api';
  import { browser } from '$app/environment';

  let plotDiv: HTMLElement;
  let identifier = 'SAM_human_4a606530';
  let isLoading = false;
  let error = '';
  let plotData: any = null;
  let viewMode: 'normalized' | 'separate' = 'normalized';
  let Plotly: any;
  let shouldCreatePlot = false;

  onMount(async () => {
    if (browser) {
      try {
        await loadPlotly();
        await fetchData();
      } catch (err) {
        error = `Error in onMount: ${err.message}`;
        console.error('Error in onMount:', err);
      }
    }
  });

  afterUpdate(() => {
    if (shouldCreatePlot && plotDiv && plotData) {
      createPlot();
      shouldCreatePlot = false;
    }
  });

  async function loadPlotly() {
    return new Promise<void>((resolve, reject) => {
      if ((window as any).Plotly) {
        Plotly = (window as any).Plotly;
        resolve();
      } else {
        const script = document.createElement('script');
        script.src = 'https://cdn.plot.ly/plotly-2.20.0.min.js';
        script.onload = () => {
          Plotly = (window as any).Plotly;
          resolve();
        };
        script.onerror = (e) => {
          console.error('Error loading Plotly from CDN:', e);
          reject(new Error('Failed to load Plotly'));
        };
        document.head.appendChild(script);
      }
    });
  }

  async function fetchData() {
    isLoading = true;
    error = '';
    try {
      const response = await fetch(`${API_ENDPOINTS.GET_PRICE_WEIGHT}?identifier=${identifier}&view_mode=${viewMode}`);
      if (response.ok) {
        plotData = await response.json();
        if (plotData && plotData.x && plotData.traces && plotData.layout) {
          shouldCreatePlot = true;
        } else {
          error = 'Invalid data format received from the server';
          console.error('Invalid plotData format:', plotData);
        }
      } else {
        error = `Server responded with status: ${response.status}`;
        console.error('Error response from server:', error);
      }
    } catch (err) {
      error = `Error fetching price and weight data: ${err.message}`;
      console.error('Error in fetchData:', err);
    } finally {
      isLoading = false;
    }
  }

  function createPlot() {
    if (!Plotly || !plotDiv || !plotData) {
      console.error('Unable to create plot. Missing:', {
        Plotly: !Plotly,
        plotDiv: !plotDiv,
        plotData: !plotData
      });
      error = 'Missing required data for plot creation';
      return;
    }

    const traces = plotData.traces.map(trace => ({
      x: plotData.x,
      y: trace.y,
      mode: 'lines+markers',
      name: trace.name,
      line: { color: trace.color },
      marker: { size: 6 },
      xaxis: trace.xaxis,
      yaxis: trace.yaxis
    }));

    try {
      Plotly.newPlot(plotDiv, traces, plotData.layout);
    } catch (err) {
      console.error('Error creating plot:', err);
      error = `Error creating plot: ${err.message}`;
    }
  }

  async function toggleView() {
    console.log(`Toggling view from ${viewMode} to ${viewMode === 'normalized' ? 'separate' : 'normalized'}`);
    viewMode = viewMode === 'normalized' ? 'separate' : 'normalized';
    await fetchData();
  }
</script>

<div>
  <button on:click={toggleView}>
    Switch to {viewMode === 'normalized' ? 'Separate' : 'Normalized'} View
  </button>
</div>

{#if isLoading}
  <p>Loading...</p>
{:else if error}
  <p>Error: {error}</p>
{:else if plotData}
  <div bind:this={plotDiv}></div>
{:else}
  <p>No data available to plot.</p>
{/if}



