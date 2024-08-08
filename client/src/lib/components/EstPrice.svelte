


<script lang="ts">
  import PlotVars from "./units/PlotVars.svelte";
  import { writable } from 'svelte/store';
  
  // Input values initialized as empty strings
  let productionCost = writable('');
  let profit = writable('');
  let packCost = writable('');
  let inlandTransportCost = writable('');
  let customsClearance = writable('');
  let portCost = writable('');
  let others = writable('');
  
  // Helper function to parse input or return 0 if empty
  const parseInput = (value: string): number => value === '' ? 0 : parseFloat(value);

  // Calculated values
  $: newProductionCost = parseInput($profit) ? parseInput($productionCost) / parseInput($profit) : 0;
  $: fobPrice = newProductionCost + parseInput($packCost) + parseInput($inlandTransportCost) + 
                parseInput($customsClearance) + parseInput($portCost) + parseInput($others);
</script>

<main>
  <div class="price_plot">
    <h2>Price Graph</h2>
    <PlotVars />
    <div class="fob-calculator">
      <h3>FOB Price Calculator</h3>
      
      <div class="cost-section">
        <h4>New Production Cost with Profit</h4>
        <div class="input-group">
          <label>
            Production Cost:
            <input type="number" bind:value={$productionCost} min="0" step="0.01" placeholder="Enter value">
          </label>
          <label>
            Profit:
            <input type="number" bind:value={$profit} min="0" max="1" step="0.01" placeholder="Enter value (0-1)">
          </label>
        </div>
        {#if $productionCost && $profit}
          <div class="equation">
            New Production Cost: {parseInput($productionCost).toFixed(2)} / {parseInput($profit).toFixed(2)} = {newProductionCost.toFixed(2)}
          </div>
        {/if}
      </div>

      <div class="cost-section">
        <h4>Additional Costs</h4>
        <div class="input-group">
          <label>
            Pack Cost:
            <input type="number" bind:value={$packCost} min="0" step="0.01" placeholder="Enter value">
          </label>
          <label>
            Inland Transport:
            <input type="number" bind:value={$inlandTransportCost} min="0" step="0.01" placeholder="Enter value">
          </label>
        </div>
        <div class="input-group">
          <label>
            Customs Clearance:
            <input type="number" bind:value={$customsClearance} min="0" step="0.01" placeholder="Enter value">
          </label>
          <label>
            Port Cost:
            <input type="number" bind:value={$portCost} min="0" step="0.01" placeholder="Enter value">
          </label>
        </div>
        <div class="input-group">
          <label>
            Others:
            <input type="number" bind:value={$others} min="0" step="0.01" placeholder="Enter value">
          </label>
        </div>
      </div>

      <div class="result-section">
        <h4>FOB Price: {fobPrice.toFixed(2)}</h4>
        <div class="equation">
          FOB = {newProductionCost.toFixed(2)} + {parseInput($packCost).toFixed(2)} + {parseInput($inlandTransportCost).toFixed(2)} + 
          {parseInput($customsClearance).toFixed(2)} + {parseInput($portCost).toFixed(2)} + {parseInput($others).toFixed(2)}
        </div>
      </div>
    </div>
  </div>
</main>

<style>
  .price_plot {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
  }

  .fob-calculator {
    margin-top: 20px;
    padding: 20px;
    border: 1px solid #ccc;
    border-radius: 5px;
  }

  .cost-section {
    margin-bottom: 20px;
  }

  .input-group {
    display: flex;
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 10px;
  }

  label {
    font-family: Ubuntu;
    font-size: 13px;
    display: block;
    width: 100%;
  }

  input {
    width: 100%;
    padding: 5px;
    box-sizing: border-box;
  }

  h3, h4 {
    margin-top: 0;
    margin-bottom: 10px;
  }

  .result-section {
    margin-top: 20px;
    font-weight: bold;
  }

  .equation {
    font-family: Ubuntu;
    font-size: 13px;
    margin: 10px 0;
    font-style: italic;
    color: #555;
  }
</style>




