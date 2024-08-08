


<script lang="ts">
  import { onMount } from 'svelte';
  import { API_ENDPOINTS } from '$lib/utils/api';
  import { browser } from '$app/environment';

  type PlotlyModule = typeof import('plotly.js-dist-min');
  
  let Plotly: PlotlyModule;
  let plotDiv: HTMLElement;
  let identifier = 'SAM_animal_47e47476'; // You can make this dynamic if needed
  let isLoading = false;
  let error = '';

  onMount(async () => {
    if (browser) {
      Plotly = await import('plotly.js-dist-min');
    }
    await fetchDataAndPlot();
  });

  async function fetchDataAndPlot() {
    isLoading = true;
    error = '';
    try {
      const response = await fetch(`${API_ENDPOINTS.GET_PRICE_WEIGHT}?identifier=${identifier}`);
      if (response.ok) {
        const data = await response.json();
        createPlot(data);
      } else {
        error = 'Failed to fetch price and weight data';
        console.error(error);
      }
    } catch (err) {
      error = 'Error fetching price and weight data';
      console.error(error, err);
    } finally {
      isLoading = false;
    }
  }

  function createPlot(data: { timestamps: number[], unit_prices: number[], unit_weights: number[] }) {
    if (!Plotly || !plotDiv) return;

    const trace1 = {
      x: data.timestamps,
      y: data.unit_prices,
      mode: 'lines+markers',
      name: 'Unit Price',
      line: {color: '#1f77b4'},
      marker: {size: 8}
    };

    const trace2 = {
      x: data.timestamps,
      y: data.unit_weights,
      mode: 'lines+markers',
      name: 'Unit Weight',
      line: {color: '#ff7f0e'},
      marker: {size: 8},
      yaxis: 'y2'
    };

    const layout = {
      title: 'Unit Price and Weight Over Time',
      xaxis: {title: 'Timestamp'},
      yaxis: {title: 'Unit Price', side: 'left'},
      yaxis2: {
        title: 'Unit Weight',
        overlaying: 'y',
        side: 'right'
      },
      legend: {x: 0, y: 1.2},
      margin: {t: 60, b: 100, l: 60, r: 60},
      height: 500,
      width: 800
    };

    Plotly.newPlot(plotDiv, [trace1, trace2], layout);
  }
</script>

{#if isLoading}
  <p>Loading...</p>
{:else if error}
  <p>Error: {error}</p>
{:else}
  <div bind:this={plotDiv}></div>
{/if}



