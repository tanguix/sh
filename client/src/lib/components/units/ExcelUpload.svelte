

<script lang="ts">
  import { writable } from 'svelte/store';
  import { onMount } from 'svelte';
  import { API_ENDPOINTS } from '$lib/utils/api';

  type EntrySet = {
    id: number;
    date: string;
    detailedSubject: string;
    quantity: string;
    specifications: string;
    category: string;
    voucherNumber: string;
    customer: string;
    remarks: string;
    paymentStatus: string;
    accountSubject: string;
    debitAmount: string;
    creditAmount: string;
    exchangeRate: string;
    usdAmount: string;
    status: string;
    isPreviewMode: boolean;
  };

  const createInitialEntrySet = (): EntrySet => ({
    id: Date.now(),
    date: '',
    detailedSubject: '',
    quantity: '',
    specifications: '',
    category: '',
    voucherNumber: '',
    customer: '',
    remarks: '',
    paymentStatus: '',
    accountSubject: '',
    debitAmount: '',
    creditAmount: '',
    exchangeRate: '',
    usdAmount: '',
    status: '',
    isPreviewMode: false
  });

  const entrySets = writable<EntrySet[]>([createInitialEntrySet()]);

  let availableFiles: string[] = [];
  let selectedFile: string = '';
  let newFileName: string = '';

  function addEntrySet() {
    entrySets.update(sets => [
      ...sets,
      createInitialEntrySet()
    ]);
  }

  function removeEntrySet(id: number) {
    entrySets.update(sets => sets.filter(set => set.id !== id));
  }

  function resetForm() {
    entrySets.set([createInitialEntrySet()]);
  }

  function togglePreview(id: number) {
    entrySets.update(sets =>
      sets.map(set =>
        set.id === id ? { ...set, isPreviewMode: !set.isPreviewMode } : set
      )
    );
  }


  onMount(async () => {
    try {
      const response = await fetch(API_ENDPOINTS.LIST_EXCEL);
      if (response.ok) {
        availableFiles = await response.json();
      } else {
        console.error('Failed to fetch available Excel files');
      }
    } catch (error) {
      console.error('Error fetching Excel files:', error);
    }
  });

  async function handleSubmit() {
    if (selectedFile === 'new' && !newFileName.trim()) {
      alert('Please enter a name for the new Excel file.');
      return;
    }

    const formData = new FormData();
    formData.append('filename', selectedFile === 'new' ? newFileName.trim() : selectedFile);
    formData.append('data', JSON.stringify($entrySets.map(({ isPreviewMode, ...rest }) => rest)));
    formData.append('is_new_file', selectedFile === 'new' ? 'true' : 'false');

    try {
      const response = await fetch(API_ENDPOINTS.APPEND_EXCEL, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        alert('Data appended successfully!');

        if (selectedFile === 'new') {
          availableFiles = [...availableFiles, newFileName.trim()];
          newFileName = '';
        }
        
        resetForm();
      } else {
        const errorData = await response.json();
        alert(`Failed to append data: ${errorData.error}`);
      }
    } catch (error) {
      console.error('Error appending data:', error);
      alert('An error occurred. Please try again.');
    }
  }
</script>

<div class="excel-upload-entries">
  <h2>Accounting</h2>

  <div class="file-selection-container">
    <div class="input-wrapper">
      <div class="file-selection">
        <label for="excel-file-select">Select Excel File to Append Data:</label>
        <div class="select-wrapper">
          <select id="excel-file-select" bind:value={selectedFile}>
            <option value="">Select a file</option>
            <option value="new">Create New Sheet</option>
            {#each availableFiles as file}
              <option value={file}>{file}</option>
            {/each}
          </select>
        </div>
      </div>
    </div>

    <div class="input-wrapper">
      <div class="new-file-input">
        <label for="new-file-name">New File Name:</label>
        <input type="text" id="new-file-name" bind:value={newFileName} placeholder="Enter new file name" disabled={selectedFile !== 'new'}>
      </div>
    </div>
  </div>

  {#each $entrySets as set (set.id)}
    <div class="entry-set">
      {#if !set.isPreviewMode}
        <div class="entry-fields">
          <div class="row">
            <div class="input-group">
              <label for="date-{set.id}">日期</label>
              <input type="date" id="date-{set.id}" bind:value={set.date}>
            </div>
            <div class="input-group">
              <label for="detailedSubject-{set.id}">明细科目</label>
              <input type="text" id="detailedSubject-{set.id}" bind:value={set.detailedSubject} placeholder="明细科目">
            </div>
            <div class="input-group">
              <label for="quantity-{set.id}">数量</label>
              <input type="number" id="quantity-{set.id}" bind:value={set.quantity} placeholder="数量">
            </div>
            <div class="input-group">
              <label for="specifications-{set.id}">规格</label>
              <input type="text" id="specifications-{set.id}" bind:value={set.specifications} placeholder="规格">
            </div>
            <div class="input-group">
              <label for="category-{set.id}">类别</label>
              <input type="text" id="category-{set.id}" bind:value={set.category} placeholder="类别">
            </div>
            <div class="input-group">
              <label for="voucherNumber-{set.id}">凭证号</label>
              <input type="text" id="voucherNumber-{set.id}" bind:value={set.voucherNumber} placeholder="凭证号" required>
            </div>
            <div class="input-group">
              <label for="customer-{set.id}">客户</label>
              <input type="text" id="customer-{set.id}" bind:value={set.customer} placeholder="客户" required>
            </div>
            <div class="input-group">
              <label for="remarks-{set.id}">备注</label>
              <input type="text" id="remarks-{set.id}" bind:value={set.remarks} placeholder="备注">
            </div>
            <div class="input-group">
              <label for="paymentStatus-{set.id}">收款情况</label>
              <input type="text" id="paymentStatus-{set.id}" bind:value={set.paymentStatus} placeholder="收款情况">
            </div>
          </div>
          <div class="row">
            <div class="input-group">
              <label for="accountSubject-{set.id}">会计科目</label>
              <input type="text" id="accountSubject-{set.id}" bind:value={set.accountSubject} placeholder="会计科目" required>
            </div>
            <div class="input-group">
              <label for="debitAmount-{set.id}">借方金额</label>
              <input type="number" id="debitAmount-{set.id}" bind:value={set.debitAmount} placeholder="借方金额" required>
            </div>
            <div class="input-group">
              <label for="creditAmount-{set.id}">贷方金额</label>
              <input type="number" id="creditAmount-{set.id}" bind:value={set.creditAmount} placeholder="贷方金额" required>
            </div>
            <div class="input-group">
              <label for="exchangeRate-{set.id}">汇率</label>
              <input type="number" id="exchangeRate-{set.id}" bind:value={set.exchangeRate} placeholder="汇率" step="0.0001">
            </div>
            <div class="input-group">
              <label for="usdAmount-{set.id}">美元</label>
              <input type="number" id="usdAmount-{set.id}" bind:value={set.usdAmount} placeholder="美元" step="0.01">
            </div>
            <div class="input-group">
              <label for="status-{set.id}">状态</label>
              <input type="text" id="status-{set.id}" bind:value={set.status} placeholder="状态">
            </div>
          </div>
        </div>
      {:else}
        <div class="preview-content">
          {#each Object.entries(set) as [key, value]}
            {#if key !== 'id' && key !== 'isPreviewMode'}
              <div class="preview-item">
                <span class="preview-label">{key}:</span>
                <span class="preview-value">{value || 'N/A'}</span>
              </div>
            {/if}
          {/each}
        </div>
      {/if}

      <div class="entry-set-actions">
        <div class="left-actions">
          <button type="button" class="action-button preview-button" on:click={() => togglePreview(set.id)}>
            {set.isPreviewMode ? 'Edit' : 'Preview'}
          </button>
          {#if $entrySets.length > 1 && !set.isPreviewMode}
            <button type="button" class="action-button remove-entry-set" on:click={() => removeEntrySet(set.id)}>-</button>
          {/if}
        </div>
      </div>
    </div>
  {/each}

  {#if $entrySets.every(set => !set.isPreviewMode)}
    <div class="button-container">
      <button type="button" on:click={addEntrySet} class="action-button add-entry-set">+</button>
    </div>
  {/if}

  <div class="submit-container">
    <button type="button" on:click={handleSubmit} class="action-button submit-entries">Submit Entries</button>
  </div>
</div>

<style>
  .file-selection-container {
    display: flex;
    gap: 1rem;
    align-items: flex-start;
    font-family: "Ubuntu";
  }

  .input-wrapper {
    flex: 1;
    display: flex;
    flex-direction: column;
    font-family: "Ubuntu";
  }

  .file-selection, .new-file-input {
    display: flex;
    flex-direction: column;
  }

  .file-selection label, .new-file-input label {
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
  }

  .select-wrapper, .new-file-input input {
    height: 38px;
  }

  .select-wrapper select, .new-file-input input {
    width: 100%;
    height: 100%;
    padding: 0.5rem;
    font-size: 0.875rem;
    border: 1px solid #ccc;
    border-radius: 0.25rem;
    box-sizing: border-box;
    line-height: normal;
    font-family: "Ubuntu";
  }

  .select-wrapper select {
    appearance: none;
    -webkit-appearance: none;
    -moz-appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='8' height='8' viewBox='0 0 8 8'%3E%3Cpath fill='%23333' d='M0 2l4 4 4-4z'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 0.7em top 50%;
    background-size: 0.65em auto;
    padding-right: 1.5em;
  }

  .select-wrapper select::-ms-expand {
    display: none;
  }

  .entry-set {
    font-family: "Zen Maru Gothic";
    border: 1px solid #ccc;
    padding: 1rem;
    border-radius: 0.25rem;
    position: relative;
    margin-bottom: 1rem;
  }

  .entry-fields {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .entry-fields .row {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
  }

  .entry-fields .row .input-group {
    flex: 1 1 calc(11.11% - 1rem);
    min-width: 100px;
  }

  .input-group, .preview-item {
    display: flex;
    flex-direction: column;
  }

  .input-group label, .preview-label {
    font-size: 0.75rem;
    margin-bottom: 0.25rem;
    text-align: left;
  }

  .input-group input {
    font-size: 0.875rem;
    border: 1px solid #ccc;
    border-radius: 0.25rem;
    width: 100%;
    box-sizing: border-box;
    padding: 0.5rem;
    margin: 0;
  }

  .preview-value {
    color: #007bff;
    font-size: 0.875rem;
  }

  .entry-set-actions {
    display: flex;
    justify-content: flex-start;
    margin-top: 1rem;
  }

  .left-actions {
    display: flex;
    gap: 1rem;
  }

  .action-button {
    padding: 0.25rem 0.5rem;
    font-family: Ubuntu;
    font-size: 14px;
    color: white;
    border: none;
    border-radius: 0.25rem;
    cursor: pointer;
    transition: background-color 0.3s;
    height: 30px;
    min-width: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .add-entry-set {
    background-color: #ff7a6e;
  }

  .add-entry-set:hover {
    background-color: #ff4136;
  }

  .preview-button {
    background-color: #007bff;
  }

  .preview-button:hover {
    background-color: #0056b3;
  }

  .remove-entry-set {
    background-color: #dc3545;
  }

  .remove-entry-set:hover {
    background-color: #c82333;
  }

  .button-container {
    display: flex;
    justify-content: center;
    margin-top: 1rem;
  }

  .submit-container {
    display: flex;
    justify-content: center;
    margin-top: 1rem;
  }

  .submit-entries {
    background-color: #007bff;
  }

  .submit-entries:hover {
    background-color: #0056b3;
  }

  .preview-content {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
  }

  .preview-item {
    min-width: 150px;
    flex: 1 1 150px;
  }
</style>






