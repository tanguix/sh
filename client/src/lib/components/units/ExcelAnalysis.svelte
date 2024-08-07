



<script lang="ts">
  import { onMount, tick } from 'svelte';
  import { API_ENDPOINTS } from '$lib/utils/api';
  import { browser } from '$app/environment';

  type PlotlyModule = typeof import('plotly.js-dist-min');
  type AnalysisResult = {
    basic_info?: { plot: string };
    column_distribution?: Array<{ name: string; plot: string }>;
    aggregation?: string;
  };

  let Plotly: PlotlyModule;
  let availableFiles: string[] = [];
  let selectedFile: string = '';
  let analysisOptions: string[] = [];
  let selectedAnalysis: string[] = [];
  let analysisResults: AnalysisResult = {};
  let isLoading: boolean = false;
  let columns: string[] = [];
  let selectedColumns: string[] = [];
  let uploadedFile: File | null = null;
  let uploadError: string = '';
  let aggregationData: {[key: string]: {[key: string]: number}} = {};
  let groupByColumn: string = '';
  let groupByValues: string = '';
  let aggregateColumn: string = '';

  onMount(async () => {
    if (browser) {
      Plotly = await import('plotly.js-dist-min');
    }

    try {
      const filesResponse = await fetch(API_ENDPOINTS.LIST_EXCEL);
      if (filesResponse.ok) {
        availableFiles = await filesResponse.json();
      } else {
        console.error('Failed to fetch available Excel files');
      }

      const operationsResponse = await fetch(API_ENDPOINTS.DS_OPERATIONS);
      if (operationsResponse.ok) {
        const data = await operationsResponse.json();
        analysisOptions = data.operations;
      } else {
        console.error('Failed to fetch allowed operations');
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  });

  async function handleFileUpload(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      uploadedFile = input.files[0];
      uploadError = '';

      const formData = new FormData();
      formData.append('file', uploadedFile);

      try {
        const response = await fetch(API_ENDPOINTS.UPLOAD_EXCEL, {
          method: 'POST',
          body: formData,
        });

        if (response.ok) {
          const data = await response.json();
          selectedFile = data.filepath;
          await handleFileSelection();
        } else {
          const errorData = await response.json();
          uploadError = errorData.error || 'Failed to upload file';
        }
      } catch (error) {
        console.error('Error uploading file:', error);
        uploadError = 'An error occurred while uploading the file';
      }
    }
  }

  async function handleFileSelection() {
    if (selectedFile) {
      isLoading = true;
      try {
        const response = await fetch(`${API_ENDPOINTS.GET_COLUMNS}?filepath=${encodeURIComponent(selectedFile)}`);
        if (response.ok) {
          const data = await response.json();
          columns = data.columns.filter(column => column.toLowerCase() !== 'id');
          selectedColumns = [];
        } else {
          console.error('Failed to fetch columns');
          alert('Failed to fetch columns from the selected file.');
        }
      } catch (error) {
        console.error('Error fetching columns:', error);
        alert('An error occurred while fetching columns. Please try again.');
      } finally {
        isLoading = false;
      }
    } else {
      columns = [];
      selectedColumns = [];
    }
    analysisResults = {};
    aggregationData = {};
  }

  async function handleAnalysis() {
    if (!selectedFile || selectedAnalysis.length === 0) {
      alert('Please select a file and at least one analysis option.');
      return;
    }

    if (selectedAnalysis.includes('column_distribution') && selectedColumns.length === 0) {
      alert('Please select at least one column for distribution analysis.');
      return;
    }

    if (selectedAnalysis.includes('aggregation') && (!groupByColumn || !aggregateColumn)) {
      alert('Please select both a group by column and an aggregate column for aggregation analysis.');
      return;
    }

    isLoading = true;
    analysisResults = {};
    aggregationData = {};

    if (browser && Plotly) {
      document.querySelectorAll('[id^="distribution-plot-"]').forEach(el => {
        Plotly.purge(el as HTMLElement);
      });
    }

    try {
      const queryParams = new URLSearchParams({
        filepath: selectedFile,
        operations: selectedAnalysis.join(','),
        columns: selectedColumns.join(','),
        groupByColumn: groupByColumn,
        groupByValues: groupByValues,
        aggregateColumn: aggregateColumn
      });

      const response = await fetch(`${API_ENDPOINTS.PROCESS_EXCEL}?${queryParams}`);
      
      if (response.ok) {
        analysisResults = await response.json();
        if (analysisResults.aggregation) {
          aggregationData = JSON.parse(analysisResults.aggregation);
        }
        await tick();
        renderPlots();
      } else {
        const errorData = await response.json();
        alert(`Failed to process Excel file: ${errorData.error}`);
      }
    } catch (error) {
      console.error('Error processing Excel file:', error);
      alert('An error occurred. Please try again.');
    } finally {
      isLoading = false;
    }
  }





  async function renderPlots() {
    if (!browser || !Plotly) return;

    await tick();

    const plotConfig = {
      responsive: true,
      displayModeBar: false
    };



    const plotLayout = {
      autosize: true,
      margin: { l: 50, r: 50, t: 100, b: 50 }
    };

    if (analysisResults.basic_info && selectedAnalysis.includes('basic_info')) {
      const el = document.getElementById('basic-info-plot');
      if (el) {
        const plotData = JSON.parse(analysisResults.basic_info.plot);
        Plotly.newPlot(el, plotData.data, {...plotData.layout, ...plotLayout}, plotConfig);
        
        // Make the plot responsive
        window.addEventListener('resize', () => {
          Plotly.Plots.resize(el);
        });
      }
    }




    if (analysisResults.column_distribution && selectedAnalysis.includes('column_distribution')) {
      analysisResults.column_distribution.forEach((plot, index) => {
        const el = document.getElementById(`distribution-plot-${index}`);
        if (el) {
          Plotly.newPlot(el, JSON.parse(plot.plot), {}, plotConfig);
        }
      });
    }
  }






  $: if (analysisResults && Object.keys(analysisResults).length > 0) {
    tick().then(() => {
      renderPlots();
    });
  }
</script>

<div class="excel-analysis">
  <h2>Excel File Analysis</h2>

  <div class="file-selection">
    <label for="excel-file-select">Select Existing Excel File to Analyze:</label>
    <select id="excel-file-select" bind:value={selectedFile} on:change={handleFileSelection}>
      <option value="">Select a file</option>
      {#each availableFiles as file}
        <option value={file}>{file}</option>
      {/each}
    </select>
  </div>

  <div class="file-upload">
    <label for="excel-file-upload">Or Upload a New Excel File:</label>
    <input type="file" id="excel-file-upload" accept=".xlsx,.xls" on:change={handleFileUpload}>
    {#if uploadError}
      <p class="error">{uploadError}</p>
    {/if}
  </div>

  {#if selectedFile}
    <div class="analysis-options">
      <h3>Select Analysis Options:</h3>
      {#each analysisOptions as option}
        <label>
          <input type="checkbox" bind:group={selectedAnalysis} value={option}>
          {option.replace('_', ' ')}
        </label>
      {/each}
    </div>

    {#if selectedAnalysis.includes('column_distribution')}
      <div class="column-selection">
        <h3>Select Columns for Distribution Analysis:</h3>
        <div class="column-list">
          {#each columns as column}
            <label class="column-checkbox">
              <input type="checkbox" bind:group={selectedColumns} value={column}>
              {column}
            </label>
          {/each}
        </div>
      </div>
    {/if}

    {#if selectedAnalysis.includes('aggregation')}
      <div class="aggregation-options">
        <h3>Aggregation Options:</h3>
        <label for="groupByColumn">Group By Column:</label>
        <select id="groupByColumn" bind:value={groupByColumn}>
          <option value="">Select a column</option>
          {#each columns as column}
            <option value={column}>{column}</option>
          {/each}
        </select>

        <label for="groupByValues">Group By Values (comma-separated):</label>
        <input type="text" id="groupByValues" bind:value={groupByValues} placeholder="e.g. clothes, books">

        <label for="aggregateColumn">Aggregate Column:</label>
        <select id="aggregateColumn" bind:value={aggregateColumn}>
          <option value="">Select a column</option>
          {#each columns as column}
            <option value={column}>{column}</option>
          {/each}
        </select>
      </div>
    {/if}

    <button on:click={handleAnalysis} disabled={isLoading}>
      {isLoading ? 'Processing...' : 'Analyze Excel File'}
    </button>
  {/if}

  {#if isLoading}
    <p>Loading analysis results...</p>
  {:else if Object.keys(analysisResults).length > 0}
    <div class="analysis-results">
      <h3>Analysis Results:</h3>
      {#if analysisResults.basic_info && selectedAnalysis.includes('basic_info')}
        <div class="result-section">
          <h4>Basic Info:</h4>
          <div id="basic-info-plot" class="plot-container"></div>
        </div>
      {/if}
      {#if analysisResults.column_distribution && selectedAnalysis.includes('column_distribution')}
        <div class="result-section">
          <h4>Column Distribution:</h4>
          {#each analysisResults.column_distribution as plot, index}
            <div id="distribution-plot-{index}" class="plot-container"></div>
          {/each}
        </div>
      {/if}
      {#if Object.keys(aggregationData).length > 0 && selectedAnalysis.includes('aggregation')}
        <div class="result-section">
          <h4>Aggregation:</h4>
          <p>Group By: {groupByColumn}, Aggregate: {aggregateColumn}</p>
          <div class="aggregation-grid">
            {#each Object.entries(aggregationData) as [group, stats]}
              <div class="stat-box">
                <h5>{group}</h5>
                <table>
                  <tr><td>Sum:</td><td>{stats.sum}</td></tr>
                  <tr><td>Mean:</td><td>{stats.mean}</td></tr>
                  <tr><td>Median:</td><td>{stats.median}</td></tr>
                  <tr><td>Min:</td><td>{stats.min}</td></tr>
                  <tr><td>Max:</td><td>{stats.max}</td></tr>
                </table>
              </div>
            {/each}
          </div>
        </div>
      {/if}
    </div>
  {:else if selectedFile && selectedAnalysis.length > 0}
    <p>Click "Analyze Excel File" to view results.</p>
  {/if}
</div>




<style>
  .excel-analysis {
    font-family: Arial, sans-serif;
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
  }

  .file-selection, .column-selection, .analysis-options {
    margin-bottom: 20px;
  }

  .file-selection select {
    width: 300px;
    padding: 8px 12px;
    font-size: 16px;
    border: 1px solid #ccc;
    border-radius: 4px;
    background-color: #f8f8f8;
    appearance: none;
    -webkit-appearance: none;
    -moz-appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' fill='%23333' viewBox='0 0 16 16'%3E%3Cpath d='M7.247 11.14 2.451 5.658C1.885 5.013 2.345 4 3.204 4h9.592a1 1 0 0 1 .753 1.659l-4.796 5.48a1 1 0 0 1-1.506 0z'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: calc(100% - 12px) center;
  }

  .file-selection select:hover {
    border-color: #888;
  }

  .file-selection select:focus {
    outline: none;
    border-color: #4CAF50;
    box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
  }

  .file-upload {
    margin-top: 20px;
    margin-bottom: 20px;
  }

  button {
    background-color: #4CAF50;
    color: white;
    border: none;
    padding: 10px 15px;
    font-size: 16px;
    cursor: pointer;
    transition: background-color 0.3s;
  }

  button:hover {
    background-color: #45a049;
  }

  button:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
  }

  .column-list {
    max-height: 200px;
    overflow-y: auto;
    border: 1px solid #ccc;
    padding: 10px;
  }

  .column-list label {
    display: block;
    margin-bottom: 5px;
  }

  .analysis-options label {
    display: block;
    margin-bottom: 5px;
  }

  .analysis-results {
    margin-top: 20px;
  }

  .result-section {
    margin-bottom: 20px;
  }

  .result-section h4 {
    margin-bottom: 10px;
  }


  .plot-container {
    width: 100%;
    height: 400px;
    margin-bottom: 20px;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    padding: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    overflow: hidden;  /* This will prevent content from spilling out */
  }




  .aggregation-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    justify-content: flex-start;
  }

  .stat-box {
    border: 1px solid #ccc;
    border-radius: 8px;
    padding: 15px;
    width: calc(25% - 15px);
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    background-color: #f9f9f9;
  }

  .stat-box h5 {
    margin-top: 0;
    margin-bottom: 10px;
    font-size: 1em;
    text-align: center;
  }

  .stat-box table {
    width: 100%;
    border-collapse: collapse;
  }

  .stat-box td {
    padding: 3px 0;
  }

  .stat-box td:first-child {
    font-weight: bold;
    padding-right: 10px;
  }

  .error {
    color: red;
    margin-top: 5px;
  }


  :global(.table) {
    border-collapse: collapse;
    width: 100%;
    margin-bottom: 1em;
  }

  :global(.table th, .table td) {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
  }

  :global(.table th) {
    background-color: #f2f2f2;
  }

  @media (max-width: 1200px) {
    .stat-box {
      width: calc(33.33% - 13.33px); /* 3 boxes per row */
    }
  }

  @media (max-width: 900px) {
    .stat-box {
      width: calc(50% - 10px); /* 2 boxes per row */
    }
  }

  @media (max-width: 600px) {
    .stat-box {
      width: 100%; /* 1 box per row */
    }

    .file-selection select {
      width: 100%;
    }
  }
</style>
