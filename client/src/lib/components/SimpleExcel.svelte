

<script lang="ts">
  import { onMount } from 'svelte';
  import { API_ENDPOINTS } from '$lib/utils/api';

  let allowedOperations: string[] = [];
  let selectedOperations: string[] = [];
  let error: string = '';
  let message: string = '';
  let file: File | null = null;
  let summary: {[key: string]: string} = {};
  let uploadedFilePath: string = '';
  let noOperationsSelected: boolean = false;

  onMount(() => {
    const style = document.createElement('style');
    style.textContent = `
      .table {
        border-collapse: collapse;
        width: 100%;
        margin-bottom: 1rem;
      }
      .table th, .table td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
      }
      .table th {
        background-color: #f2f2f2;
        font-weight: bold;
      }
      .table tr:nth-child(even) {
        background-color: #f9f9f9;
      }
      .table tr:hover {
        background-color: #f5f5f5;
      }
    `;
    document.head.appendChild(style);
  });

  async function uploadFile(): Promise<void> {
    if (!file) {
      error = 'Please select a file first';
      return;
    }
    const formData = new FormData();
    formData.append('file', file);
    try {
      const response = await fetch(API_ENDPOINTS.UPLOAD_EXCEL, {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) {
        throw new Error('Failed to upload file');
      }
      const data = await response.json();
      uploadedFilePath = data.filepath;
      message = 'File successfully uploaded';
      error = '';
      await fetchAllowedOperations();
    } catch (err) {
      console.error('Error uploading file:', err);
      error = `Failed to upload file: ${err instanceof Error ? err.message : 'Unknown error'}`;
      message = '';
      uploadedFilePath = '';
    }
  }

  async function fetchAllowedOperations(): Promise<void> {
    try {
      const response = await fetch(API_ENDPOINTS.DS_OPERATION);
      if (!response.ok) {
        throw new Error('Failed to fetch allowed operations');
      }
      const data = await response.json();
      allowedOperations = data.operations;
      message += '\nAvailable operations fetched successfully';
      error = '';
    } catch (err) {
      console.error('Error fetching allowed operations:', err);
      error = `Failed to fetch allowed operations: ${err instanceof Error ? err.message : 'Unknown error'}`;
    }
  }

  async function processExcel(): Promise<void> {
    if (!uploadedFilePath) {
      error = 'Please upload a file first';
      return;
    }
    if (selectedOperations.length === 0) {
      noOperationsSelected = true;
      error = '';
      message = '';
      summary = {};
      return;
    }
    noOperationsSelected = false;
    try {
      let operationsToProcess = selectedOperations.includes('full_summary') 
        ? ['full_summary'] 
        : selectedOperations;
      const operationsParam = operationsToProcess.join(',');
      const response = await fetch(`${API_ENDPOINTS.PROCESS_EXCEL}?filepath=${encodeURIComponent(uploadedFilePath)}&operations=${operationsParam}`, {
        method: 'GET',
      });
      if (!response.ok) {
        throw new Error('Failed to process file');
      }
      const data = await response.json();
      summary = data;
      message = 'File successfully processed';
      error = '';
    } catch (err) {
      console.error('Error processing file:', err);
      error = `Failed to process file: ${err instanceof Error ? err.message : 'Unknown error'}`;
      message = '';
      summary = {};
    }
  }

  function handleOperationToggle(operation: string): void {
    if (operation === 'full_summary') {
      if (selectedOperations.includes('full_summary')) {
        selectedOperations = selectedOperations.filter(op => op !== 'full_summary');
      } else {
        selectedOperations = ['full_summary'];
      }
    } else {
      const index = selectedOperations.indexOf(operation);
      if (index > -1) {
        selectedOperations = selectedOperations.filter(op => op !== operation && op !== 'full_summary');
      } else {
        selectedOperations = selectedOperations.filter(op => op !== 'full_summary');
        selectedOperations = [...selectedOperations, operation];
      }
    }
    noOperationsSelected = selectedOperations.length === 0;
  }

  function handleFileChange(event: Event): void {
    const target = event.target as HTMLInputElement;
    if (target.files) {
      file = target.files[0];
      uploadedFilePath = '';
      allowedOperations = [];
      selectedOperations = [];
      summary = {};
    }
  }
</script>

<main>
  <h1>Excel File Processor</h1>
  
  <div>
    <input type="file" accept=".xlsx,.xls" on:change={handleFileChange} />
    <button on:click={uploadFile}>Upload Excel File</button>
  </div>
  
  {#if message}
    <p class="success">{message}</p>
  {/if}
  {#if error}
    <p class="error">{error}</p>
  {/if}
  
  {#if allowedOperations.length > 0}
    <h2>Select Operations:</h2>
    {#each allowedOperations as operation}
      <label>
        <input 
          type="checkbox" 
          checked={selectedOperations.includes(operation)} 
          on:change={() => handleOperationToggle(operation)}
        />
        {operation}
      </label>
    {/each}
    <button on:click={processExcel}>Process Excel</button>
  {/if}

  {#if noOperationsSelected}
    <p class="info">No operations selected. Please select at least one operation to process the Excel file.</p>
  {/if}

  {#if Object.keys(summary).length > 0}
    {#if summary.full_summary}
      <div>
        {@html summary.full_summary}
      </div>
    {:else}
      {#each Object.entries(summary) as [operation, result]}
        <h3>{operation}</h3>
        <div>
          {@html result}
        </div>
      {/each}
    {/if}
  {/if}
</main>

<style>

  :global(.table) {
    font-size: 0.9em;
    max-width: 100%;
    overflow-x: auto;
  }

  .error {
    color: red;
  }

  .success {
    color: green;
  }

  .info {
    color: blue;
  }

  label {
    display: block;
    margin-bottom: 5px;
  }

</style>



