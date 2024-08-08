

<script lang="ts">
  import { onMount, afterUpdate } from 'svelte';
  import { API_ENDPOINTS } from '$lib/utils/api';
  import { browser } from '$app/environment';

  let plotDiv: HTMLElement;
  let identifier = '';
  let isLoading = false;
  let error = '';
  let plotData: any = null;
  let viewMode: 'normalized' | 'separate' = 'normalized';
  let Plotly: any;
  let shouldCreatePlot = false;
  let showPlot = false;

  onMount(async () => {
    if (browser) {
      try {
        await loadPlotly();
      } catch (err) {
        error = `Error loading Plotly: ${err.message}`;
        console.error('Error loading Plotly:', err);
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
          throw new Error('Invalid data format received from the server');
        }
      } else {
        throw new Error(`Server responded with status: ${response.status}`);
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
      Plotly.newPlot(plotDiv, traces, plotData.layout, {responsive: true});
    } catch (err) {
      console.error('Error creating plot:', err);
      error = `Error creating plot: ${err.message}`;
    }
  }




  async function toggleView() {
    viewMode = viewMode === 'normalized' ? 'separate' : 'normalized';
    await fetchData();
  }

  async function togglePlot() {
    if (!showPlot) {
      await fetchData();
    }
    showPlot = !showPlot;
  }

  function handleIdentifierChange() {
    if (showPlot) {
      fetchData();
    }
  }


</script>





<div class="outer-container">
  <div class="input-group">
    <label for="identifier">Identifier:</label>
    <div class="input-button-wrapper">
      <input
        id="identifier"
        type="text"
        bind:value={identifier}
        on:change={handleIdentifierChange}
        placeholder="Enter identifier"
      />
      <button on:click={togglePlot} class="btn">
        {showPlot ? 'Hide' : 'Show'} Plot
      </button>
    </div>
  </div>

  {#if showPlot}
    <div class="plot-controls">
      <button on:click={toggleView} class="btn btn-small">
        Switch to {viewMode === 'normalized' ? 'Separate' : 'Normalized'} View
      </button>
    </div>

    <div class="plot-wrapper">
      {#if isLoading}
        <p class="loading">Loading...</p>
      {:else if error}
        <div class="error">{error}</div>
      {:else if plotData}
        <div bind:this={plotDiv} class="plot-container"></div>
      {:else}
        <p class="loading">No data available to plot.</p>
      {/if}
    </div>
  {/if}
</div>

<style>

  label {
    font-family: Ubuntu;
  }

  .outer-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 100%;
    max-width: 100%;
    margin: 0 auto;
    padding: 1rem;
    box-sizing: border-box;
  }
  .input-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    width: 100%;
    margin-bottom: 1rem;
    align-items: center;
    justify-content: center
  }
  .input-group label {
    font-weight: bold;
  }
  .input-button-wrapper {
    display: flex;
    gap: 0.5rem;
    width: 40%;
    align-items: center;
    justify-content: center;
  }
  .input-group input {
    flex-grow: 1;
    padding: 0.5rem;
    border: 1px solid #d1d5db;
    border-radius: 0.25rem;
    font-size: 1rem;
  }
  .btn {
    padding: 0.5rem 1rem;
    font-size: 1rem;
    font-weight: bold;
    color: white;
    background-color: #3b82f6;
    border: none;
    border-radius: 0.25rem;
    cursor: pointer;
    transition: background-color 0.3s ease;
    white-space: nowrap;
  }
  .btn:hover {
    background-color: #2563eb;
  }
  .btn-small {
    padding: 0.25rem 0.5rem;
    font-size: 0.875rem;
  }
  .plot-controls {
    width: 100%;
    display: flex;
    justify-content: flex-start;
    margin-bottom: 1rem;
  }
  .plot-wrapper {
    width: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 400px;
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    overflow-x: auto;
    overflow-y: hidden;
  }
  .plot-container {
    width: 100%;
    min-width: 600px;
    height: 100%;
    min-height: 400px;
  }
  @media (max-width: 600px) {
    .plot-container {
      min-width: 100%;
    }
  }
</style>






