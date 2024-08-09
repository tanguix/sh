


<script lang="ts">
  import PlotVars from "./units/PlotVars.svelte";
  import { writable } from 'svelte/store';
  
  // Input values
  let productionCost = writable('');
  let profit = writable('');
  let packCost = writable('');
  let inlandTransportCost = writable('');
  let unifiedClearancePortCost = writable('');
  let others = writable('');
  let localTransportCost = writable('');
  let importTax = writable('');
  let localVAT = writable('');
  let weight = writable('');

  // Search functionality
  let referenceNo = writable('');
  let searchResult = writable({ unitPrice: null, unitWeight: null });

  async function searchDocument() {
    // TODO: Implement actual database search
    // For now, we'll just set dummy values
    searchResult.set({ unitPrice: 10.5, unitWeight: 0.5 });
  }

  // Transportation entries
  type TransportEntry = {
    company: string;
    method: string;
    cost: string;
    insurance: string;
  };

  let transportEntries = writable<TransportEntry[]>([
    { company: '', method: '', cost: '', insurance: '0' }
  ]);

  function addTransportEntry() {
    transportEntries.update(entries => [...entries, { company: '', method: '', cost: '', insurance: '0' }]);
  }

  function removeTransportEntry(index: number) {
    transportEntries.update(entries => {
      if (entries.length > 1) {
        return entries.filter((_, i) => i !== index);
      }
      return entries;
    });
  }
  
  // Helper function to parse input or return 0 if empty
  const parseInput = (value: string): number => value === '' ? 0 : parseFloat(value);

  // Calculated values
  $: trueProductionCost = parseInput($profit) ? parseInput($productionCost) / parseInput($profit) : 0;
  $: fobPrice = trueProductionCost + parseInput($packCost) + 
                (parseInput($inlandTransportCost) * parseInput($weight)) + 
                (parseInput($unifiedClearancePortCost) * parseInput($weight)) + 
                parseInput($others);
  $: totalTransportCost = $transportEntries.reduce((sum, entry) => 
    sum + (parseInput(entry.cost) + parseInput(entry.insurance)) * parseInput($weight), 0
  );
  $: cifPrice = fobPrice + totalTransportCost;
  $: dapPrice = cifPrice + parseInput($localTransportCost);
  $: ddpPrice = dapPrice + parseInput($importTax) + parseInput($localVAT);
  $: commissionFee = fobPrice * 0.05;
</script>




<main>
  <div class="price_plot">
    <h2>Price Graph</h2>
    <PlotVars />
    
    <div class="search-section">
      <h3>Search Document</h3>
      <div class="search-input">
        <input type="text" bind:value={$referenceNo} placeholder="Enter reference number">
        <button on:click={searchDocument}>Find</button>
      </div>
    </div>

    <div class="calculator-section">
      <h3>Price Calculations</h3>
      
      <div class="price-grid">
        <div class="left-column">
          <div class="calculator-box">
            <h4>FOB Price: {fobPrice.toFixed(2)}</h4>
            <div class="input-group">
              <label>
                Production Cost:
                <input type="number" bind:value={$productionCost} min="0" step="0.01">
              </label>
              <label>
                Profit:
                <input type="number" bind:value={$profit} min="0" max="1" step="0.01" placeholder="value (0-1)">
              </label>
              <div class="equation">
                True Production Cost = Production Cost / Profit = {parseInput($productionCost).toFixed(2)} / {parseInput($profit).toFixed(2)} = {trueProductionCost.toFixed(2)}
              </div>
              <label>
                Pack Cost:
                <input type="number" bind:value={$packCost} min="0" step="0.01">
              </label>
              <label>
                Inland Transport (per kg):
                <input type="number" bind:value={$inlandTransportCost} min="0" step="0.01">
              </label>
              <label>
                Customs Clearance + Port Cost (per kg):
                <input type="number" bind:value={$unifiedClearancePortCost} min="0" step="0.01">
              </label>
              <label>
                Weight (kg):
                <input type="number" bind:value={$weight} min="0" step="0.01">
              </label>
              <label>
                Others:
                <input type="number" bind:value={$others} min="0" step="0.01">
              </label>
            </div>
            <div class="equation">
              FOB = {trueProductionCost.toFixed(2)} + {parseInput($packCost).toFixed(2)} + 
              ({parseInput($inlandTransportCost).toFixed(2)} * {parseInput($weight).toFixed(2)}) + 
              ({parseInput($unifiedClearancePortCost).toFixed(2)} * {parseInput($weight).toFixed(2)}) + 
              {parseInput($others).toFixed(2)}
            </div>
          </div>

          <div class="calculator-box">
            <h4>Commission Fee: {commissionFee.toFixed(2)}</h4>
            <div class="equation">
              Commission Fee = FOB * 5% = {fobPrice.toFixed(2)} * 0.05
            </div>
          </div>

          <div class="calculator-box">
            <div class="cif-header">
              <h4>CIF Price: {cifPrice.toFixed(2)}</h4>
              <div class="cif-buttons">
                <button on:click={addTransportEntry} class="small-button">+</button>
                <button on:click={() => removeTransportEntry($transportEntries.length - 1)} class="small-button" disabled={$transportEntries.length === 1}>-</button>
              </div>
            </div>
            <div class="input-group">
              <div class="transport-entry transport-labels">
                <span>Company</span>
                <span>Method</span>
                <span>Cost per kg</span>
                <span>Insurance per kg</span>
              </div>
              {#each $transportEntries as entry, i}
                <div class="transport-entry">
                  <input type="text" bind:value={entry.company} placeholder="Company">
                  <input type="text" bind:value={entry.method} placeholder="Method">
                  <input type="number" bind:value={entry.cost} min="0" step="0.01" placeholder="Cost per kg">
                  <input type="number" bind:value={entry.insurance} min="0" step="0.01" placeholder="Insurance per kg">
                </div>
              {/each}
            </div>
            <div class="equation">
              CIF = FOB + 
              {#each $transportEntries as entry, i}
                (({entry.cost} + {entry.insurance}) * {parseInput($weight).toFixed(2)} ({entry.company}  :  {entry.method})) 
                {#if i < $transportEntries.length - 1}+{/if}
              {/each}
              = {fobPrice.toFixed(2)} + {totalTransportCost.toFixed(2)}
            </div>
          </div>
        </div>

        <div class="right-column">
          <div class="calculator-box image-search-combined">
            <div class="image-placeholder">
              <p>Image will be displayed here</p>
            </div>
            <div class="search-result">
              <h4>Search Result</h4>
              {#if $searchResult.unitPrice !== null && $searchResult.unitWeight !== null}
                <p>Unit Price: ${$searchResult.unitPrice.toFixed(2)}</p>
                <p>Unit Weight: {$searchResult.unitWeight.toFixed(2)} kg</p>
              {:else}
                <p>No search result</p>
              {/if}
            </div>
          </div>

          <div class="calculator-box">
            <h4>DAP Price: {dapPrice.toFixed(2)}</h4>
            <div class="input-group">
              <label>
                Local Transport Cost:
                <input type="number" bind:value={$localTransportCost} min="0" step="0.01">
              </label>
            </div>
            <div class="equation">
              DAP = CIF + Local Transport = {cifPrice.toFixed(2)} + {parseInput($localTransportCost).toFixed(2)}
            </div>
          </div>

          <div class="calculator-box">
            <h4>DDP Price: {ddpPrice.toFixed(2)}</h4>
            <div class="input-group">
              <label>
                Import Tax:
                <input type="number" bind:value={$importTax} min="0" step="0.01">
              </label>
              <label>
                Local VAT:
                <input type="number" bind:value={$localVAT} min="0" step="0.01">
              </label>
            </div>
            <div class="equation">
              DDP = DAP + Import Tax + VAT = {dapPrice.toFixed(2)} + {parseInput($importTax).toFixed(2)} + {parseInput($localVAT).toFixed(2)}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</main>





<style>
  input {
    margin: 0;
    padding: 0;
    font-size: 13px;
  }

  .price_plot {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
  }

  .calculator-section {
    margin-top: 20px;
    padding: 20px;
    border: 1px solid #ccc;
    border-radius: 5px;
  }


  .price-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
  }



  .left-column, .right-column {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }


  .calculator-box {
    padding: 15px;
    border: 1px solid #ccc;
    border-radius: 5px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    background-color: #fff;
  }

  .input-group {
    display: flex;
    flex-direction: column;
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

  h3 {
    text-align: center;
  }

  .equation {
    font-family: Ubuntu;
    font-size: 13px;
    margin: 10px 0;
    font-style: italic;
    color: #555;
  }

  .cif-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .cif-buttons {
    display: flex;
    gap: 5px;
  }

  .small-button {
    padding: 2px 6px;
    font-size: 12px;
    min-width: 24px;
    background-color: #3b82f6;
    color: white;
    border: none;
    cursor: pointer;
    border-radius: 4px;
  }

  .small-button:hover {
    background-color: #2563eb;
  }

  .small-button:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
  }

  .transport-labels {
    font-weight: bold;
    margin-bottom: 2px;
  }

  .transport-labels span {
    font-family: Ubuntu;
    flex: 1;
    text-align: center;
    font-size: 12px;
  }

  .transport-entry {
    display: flex;
    gap: 10px;
    margin-bottom: 2px;
  }

  .transport-entry input {
    flex: 1;
  }



  .search-section {
    margin-bottom: 20px;
  }

  .search-input {
    display: flex;
    gap: 10px;
  }

  .search-input input {
    flex-grow: 1;
  }

  .search-input button {
    padding: 5px 10px;
    background-color: #3b82f6;
    color: white;
    border: none;
    cursor: pointer;
    border-radius: 4px;
  }

  .price-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
  }


  .image-search-combined {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .image-placeholder {
    border: 1px dashed #ccc;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 150px;
  }

  .search-result {
    padding: 10px;
    border: 1px solid #ccc;
    border-radius: 5px;
    background-color: #f9f9f9;
  }



</style>



