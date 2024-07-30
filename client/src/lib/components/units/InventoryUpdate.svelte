
<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  export let inventory: InventoryItem[];
  export let referenceNo: string;

  const dispatch = createEventDispatcher();

  let newPutIn = 0;
  let newTakeOut = 0;

  function addInventoryEntry() {
    if (newPutIn > 0 || newTakeOut > 0) {
      const newEntry = {
        putIn: newPutIn,
        takeOut: newTakeOut,
        by: "Current User", // Replace with actual user info
        timestamp: Date.now()
      };
      dispatch('update', { referenceNo, newEntry });
      newPutIn = 0;
      newTakeOut = 0;
    }
  }
</script>

<div class="inventory-update">
  <h4>Update Inventory</h4>
  <div class="input-group">
    <label>
      Put In:
      <input type="number" bind:value={newPutIn} min="0">
    </label>
    <label>
      Take Out:
      <input type="number" bind:value={newTakeOut} min="0">
    </label>
  </div>
  <button on:click={addInventoryEntry}>Add Entry</button>

  <h4>Inventory History</h4>
  <table>
    <thead>
      <tr>
        <th>Put In</th>
        <th>Take Out</th>
        <th>By</th>
        <th>Timestamp</th>
      </tr>
    </thead>
    <tbody>
      {#each inventory as item}
        <tr>
          <td>{item.putIn}</td>
          <td>{item.takeOut}</td>
          <td>{item.by}</td>
          <td>{new Date(item.timestamp).toLocaleString()}</td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>

<style>
  .inventory-update {
    margin-top: 20px;
  }
  .inventory-update button {
    color: white;
    background-color: #007bff;
  }
  .input-group {
    display: flex;
    gap: 10px;
    margin-bottom: 10px;
  }
  table {
    width: 100%;
    border-collapse: collapse;
  }
  th, td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
  }
  th {
    background-color: #f2f2f2;
  }
</style>
