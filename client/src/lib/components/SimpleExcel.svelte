


<script lang="ts">
  import { API_ENDPOINTS } from '$lib/utils/api';

  let allowedOperations: string[] = [];
  let error: string = '';
  let message: string = '';

  async function fetchAllowedOperations() {
    try {
      const response = await fetch(API_ENDPOINTS.DS_OPERATION);
      if (!response.ok) {
        throw new Error('Failed to fetch allowed operations');
      }
      const data = await response.json();
      allowedOperations = data.operations;
      message = 'Successfully fetched allowed operations';
      error = '';
    } catch (err) {
      console.error('Error fetching allowed operations:', err);
      error = `Failed to fetch allowed operations: ${err.message}`;
      message = '';
    }
  }
</script>

<main>
  <h1>Test Backend Connectivity</h1>
  <button on:click={fetchAllowedOperations}>Fetch Allowed Operations</button>
  
  {#if message}
    <p class="success">{message}</p>
  {/if}

  {#if error}
    <p class="error">{error}</p>
  {/if}

  {#if allowedOperations.length > 0}
    <h2>Allowed Operations:</h2>
    <ul>
      {#each allowedOperations as operation}
        <li>{operation}</li>
      {/each}
    </ul>
  {/if}
</main>

<style>
  .error {
    color: red;
  }
  .success {
    color: green;
  }
</style>
