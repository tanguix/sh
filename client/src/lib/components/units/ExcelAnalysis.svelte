



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
      displayModeBar: true
    };


    if (analysisResults.basic_info && selectedAnalysis.includes('basic_info')) {
      const el = document.getElementById('basic-info-plot');
      if (el) {
        const plotData = JSON.parse(analysisResults.basic_info.plot);
        
        // Adjust the plot size to fit the container
        const containerWidth = el.offsetWidth;
        const containerHeight = el.offsetHeight;
        
        plotData.layout.width = containerWidth - 20; // Subtract padding
        plotData.layout.height = containerHeight - 20; // Subtract padding
        
        // Ensure the title is centered and has enough space
        plotData.layout.title.y = 0.95;
        plotData.layout.margin.t = 60;  // Increase top margin for more space below title
        
        Plotly.newPlot(el, plotData.data, plotData.layout, plotConfig);
        
        const resizeHandler = () => {
          const newWidth = el.offsetWidth - 20;
          const newHeight = el.offsetHeight - 20;
          Plotly.relayout(el, {
            width: newWidth,
            height: newHeight
          });
        };

        window.addEventListener('resize', resizeHandler);
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


  let allColumnsSelected = false;

  function toggleAllColumns() {
    allColumnsSelected = !allColumnsSelected;
    selectedColumns = allColumnsSelected ? [...columns] : [];
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
      <div class="options-list">
        {#each analysisOptions as option}
          <label class="checkbox-container">
            <input type="checkbox" bind:group={selectedAnalysis} value={option}>
            <span class="checkmark"></span>
            <span class="option-text">{option.replace('_', ' ')}</span>
          </label>
        {/each}
      </div>
    </div>

    {#if selectedAnalysis.includes('column_distribution')}
      <div class="column-selection">
        <h3>Select Columns for Distribution Analysis:</h3>

        <div class="column-list">
          {#each columns as column}
            <label class="checkbox-container">
              <input type="checkbox" bind:group={selectedColumns} value={column}>
              <span class="checkmark"></span>
              <span class="option-text">{column}</span>
            </label>
          {/each}
        </div>
        <button on:click={toggleAllColumns} class="toggle-all-btn">
          {allColumnsSelected ? 'Deselect All' : 'Select All'}
        </button>

      </div>
    {/if}

    {#if selectedAnalysis.includes('aggregation')}
      <div class="aggregation-options">
        <h3>Aggregation Options:</h3>
        <div class="aggregation-grid">
          <div class="aggregation-item">
            <label for="groupByColumn">Group By Column:</label>
            <select id="groupByColumn" bind:value={groupByColumn}>
              <option value="">Select a column</option>
              {#each columns as column}
                <option value={column}>{column}</option>
              {/each}
            </select>
          </div>
          <div class="aggregation-item">
            <label for="groupByValues">Values (comma-separated):</label>
            <input type="text" id="groupByValues" bind:value={groupByValues} placeholder="e.g. clothes, books">
          </div>
          <div class="aggregation-item">
            <label for="aggregateColumn">Aggregate Column:</label>
            <select id="aggregateColumn" bind:value={aggregateColumn}>
              <option value="">Select a column</option>
              {#each columns as column}
                <option value={column}>{column}</option>
              {/each}
            </select>
          </div>
        </div>
      </div>
    {/if}

    <button on:click={handleAnalysis} disabled={isLoading} class="analyze-btn">
      {isLoading ? 'Processing...' : 'Analyze Excel File'}
    </button>
  {/if}

  {#if isLoading}
    <p class="loading-message">Loading analysis results...</p>
  {:else if Object.keys(analysisResults).length > 0}
    <div class="analysis-results">
      <h3>Analysis Results:</h3>


      {#if analysisResults.basic_info && selectedAnalysis.includes('basic_info')}
        <div class="result-section">
          <h4>[ Basic Info ]</h4>
          <div class="plot-container">
            <div id="basic-info-plot" class="plot-inner"></div>
          </div>
        </div>
      {/if}



      {#if analysisResults.column_distribution && selectedAnalysis.includes('column_distribution')}
        <div class="result-section">
          <h4>[ Column Distribution ]</h4>
          {#each analysisResults.column_distribution as plot, index}
            <div id="distribution-plot-{index}" class="plot-container"></div>
          {/each}
        </div>
      {/if}
      {#if Object.keys(aggregationData).length > 0 && selectedAnalysis.includes('aggregation')}
        <div class="result-section">
          <h4>[ Aggregation ]</h4>
          <p>Group By: {groupByColumn}, Aggregate: {aggregateColumn}</p>
          <div class="aggregation-results-grid">
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
    <p class="info-message">Click "Analyze Excel File" to view results.</p>
  {/if}
</div>

<style>

  input {
    margin: 0;
    padding: 0;
  }


  .excel-analysis {
    font-family: Arial, sans-serif;
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
  }


  h2 {
    font-size: 24px;
    margin-bottom: 20px;
  }

  h3 {
    font-size: 20px;
    margin-top: 20px;
    margin-bottom: 10px;
  }

  h4 {
    font-size: 18px;
    margin-top: 15px;
    margin-bottom: 10px;
    text-align: center;
  }

  .file-selection, .file-upload, .analysis-options, .column-selection, .aggregation-options {
    margin-bottom: 20px;
  }

  label {
    font-family: Ubuntu;
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
  }

  select, input[type="text"], input[type="file"] {
    font-family: Ubuntu;
    width: 100%;
    padding: 8px;
    margin-bottom: 10px;
    border: 1px solid #ccc;
    border-radius: 4px;
    box-sizing: border-box;
  }

  .options-list, .column-list {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 10px;
  }



  .checkbox-container {
    display: flex;
    align-items: center;
    position: relative;
    padding-left: 20px;
    margin-bottom: 12px;
    cursor: pointer;
    font-size: 14px;
    user-select: none;
  }

  .checkbox-container input {
    position: absolute;
    opacity: 0;
    cursor: pointer;
    height: 0;
    width: 0;
  }

  .checkmark {
    position: absolute;
    top: 50%;
    left: 0;
    transform: translateY(-50%);
    height: 18px;
    width: 18px;
    background-color: #f0f0f0;
    border: 1px solid #ccc;
    border-radius: 3px;
  }

  .checkbox-container:hover input ~ .checkmark {
    background-color: #e0e0e0;
  }

  .checkbox-container input:checked ~ .checkmark {
    background-color: #2196F3;
    border-color: #2196F3;
  }

  .checkmark:after {
    content: "";
    position: absolute;
    display: none;
  }

  .checkbox-container input:checked ~ .checkmark:after {
    display: block;
  }

  .checkbox-container .checkmark:after {
    left: 6px;
    top: 2px;
    width: 3px;
    height: 8px;
    border: solid white;
    border-width: 0 2px 2px 0;
    transform: rotate(45deg);
  }

  .option-text {
    margin-left: 8px;
    line-height: 18px;
  }





  .toggle-all-btn, .analyze-btn {
    background-color: #4CAF50;
    color: white;
    border: none;
    padding: 10px 15px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 16px;
    margin: 4px 2px;
    cursor: pointer;
    border-radius: 4px;
  }

  .toggle-all-btn {
    background-color: #008CBA;
  }

  .analyze-btn:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
  }

  .error {
    color: red;
    margin-top: 5px;
  }

  .loading-message {
    color: #008CBA;
    font-weight: bold;
  }

  .info-message {
    color: #555;
    font-style: italic;
  }



  .plot-container {
    width: 100%;
    max-width: 600px;
    height: 450px;  /* Increased height to accommodate title */
    margin: 0 auto 20px;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    padding: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    box-sizing: border-box;
    overflow: hidden;
  }


  .plot-inner {
    width: 100%;
    height: 100%;
  }


  .aggregation-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
  }

  .aggregation-item {
    display: flex;
    flex-direction: column;
  }



  .aggregation-results-grid {
    margin-top: 20px;
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
  }

  .stat-box {
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 10px;
    background-color: #f9f9f9;
    min-width: 0; /* Allows the box to shrink below its content size */
  }

  .stat-box h5 {
    margin-top: 0;
    margin-bottom: 10px;
    font-size: 16px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    text-align: center;
  }

  .stat-box table {
    width: 100%;
    table-layout: fixed;
  }

  .stat-box td {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .stat-box td:first-child {
    font-weight: bold;
    padding-right: 10px;
    width: 40%;
    text-align: left; /* Keep labels left-aligned */
  }

  .stat-box td:last-child {
    text-align: center; /* Center-align only the value cells */
  }

  @media (max-width: 1200px) {
    .aggregation-results-grid {
      grid-template-columns: repeat(3, 1fr);
    }
  }

  @media (max-width: 900px) {
    .aggregation-results-grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  @media (max-width: 600px) {
    .aggregation-results-grid {
      grid-template-columns: 1fr;
    }
  }



</style>




