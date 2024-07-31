


<script lang="ts">
  import { API_ENDPOINTS } from '$lib/utils/api';
  
  let allowedOperations: string[] = [];
  let error: string = '';
  let message: string = '';
  let file: File | null = null;
  let summary: string = '';

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

  async function handleFileUpload() {
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
      summary = data.summary;
      message = 'File successfully uploaded and processed';
      error = '';
    } catch (err) {
      console.error('Error uploading file:', err);
      error = `Failed to upload file: ${err.message}`;
      message = '';
      summary = '';
    }
  }

  function handleFileChange(event: Event) {
    const target = event.target as HTMLInputElement;
    if (target.files) {
      file = target.files[0];
    }
  }
</script>

<main>
  <h1>Excel File Processor</h1>
  
  <div>
    <input type="file" accept=".xlsx,.xls" on:change={handleFileChange} />
    <button on:click={handleFileUpload}>Upload and Process Excel</button>
  </div>

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

  {#if summary}
    <h2>Excel File Summary:</h2>
    <pre>{summary}</pre>
  {/if}
</main>

<style>
  .error {
    color: red;
  }
  .success {
    color: green;
  }
  pre {
    white-space: pre-wrap;
    word-wrap: break-word;
  }
</style>


