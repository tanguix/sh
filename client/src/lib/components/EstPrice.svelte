


<script lang="ts">
  import PlotVars from "./units/PlotVars.svelte";
  import { writable } from 'svelte/store';
  
  // Input values
  let productionCost = writable('');
  let profit = writable('');
  let packCost = writable('');
  let inlandTransportCost = writable('');
  let customsClearance = writable('');
  let portCost = writable('');
  let others = writable('');
  let shippingCost = writable('');
  let insuranceCost = writable('');
  let localTransportCost = writable('');
  let importTax = writable('');
  let localVAT = writable('');
  
  // Helper function to parse input or return 0 if empty
  const parseInput = (value: string): number => value === '' ? 0 : parseFloat(value);

  // Calculated values
  $: newProductionCost = parseInput($profit) ? parseInput($productionCost) / parseInput($profit) : 0;
  $: fobPrice = newProductionCost + parseInput($packCost) + parseInput($inlandTransportCost) + 
                parseInput($customsClearance) + parseInput($portCost) + parseInput($others);
  $: cifPrice = fobPrice + parseInput($shippingCost) + parseInput($insuranceCost);
  $: dapPrice = cifPrice + parseInput($localTransportCost);
  $: ddpPrice = dapPrice + parseInput($importTax) + parseInput($localVAT);
  $: commissionFee = fobPrice * 0.05;
</script>

<main>
  <div class="price_plot">
    <h2>Price Graph</h2>
    <PlotVars />
    
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
              <label>
                Pack Cost:
                <input type="number" bind:value={$packCost} min="0" step="0.01">
              </label>
              <label>
                Inland Transport:
                <input type="number" bind:value={$inlandTransportCost} min="0" step="0.01">
              </label>
              <label>
                Customs Clearance:
                <input type="number" bind:value={$customsClearance} min="0" step="0.01">
              </label>
              <label>
                Port Cost:
                <input type="number" bind:value={$portCost} min="0" step="0.01">
              </label>
              <label>
                Others:
                <input type="number" bind:value={$others} min="0" step="0.01">
              </label>
            </div>
            <div class="equation">
              FOB = {newProductionCost.toFixed(2)} + {parseInput($packCost).toFixed(2)} + {parseInput($inlandTransportCost).toFixed(2)} + 
              {parseInput($customsClearance).toFixed(2)} + {parseInput($portCost).toFixed(2)} + {parseInput($others).toFixed(2)}
            </div>
          </div>
          <div class="calculator-box">
            <h4>Commission Fee: {commissionFee.toFixed(2)}</h4>
            <div class="equation">
              Commission Fee = FOB * 5% = {fobPrice.toFixed(2)} * 0.05
            </div>
          </div>
        </div>
        <div class="right-column">
          <div class="calculator-box">
            <h4>CIF Price: {cifPrice.toFixed(2)}</h4>
            <div class="input-group">
              <label>
                Shipping Cost:
                <input type="number" bind:value={$shippingCost} min="0" step="0.01">
              </label>
              <label>
                Insurance Cost:
                <input type="number" bind:value={$insuranceCost} min="0" step="0.01">
              </label>
            </div>
            <div class="equation">
              CIF = FOB + Shipping + Insurance = {fobPrice.toFixed(2)} + {parseInput($shippingCost).toFixed(2)} + {parseInput($insuranceCost).toFixed(2)}
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
            <div>
              <span>VAT (Value Added Tax 增值税)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</main>

<style>

  span {
    font-family: Ubuntu;
    font-size: 13.5px;
    font-style: italic;
    color: #555;
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
    display: flex;
    gap: 20px;
  }

  .left-column, .right-column {
    flex: 1;
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
</style>



