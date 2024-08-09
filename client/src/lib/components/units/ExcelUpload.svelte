


<script lang="ts">
  import { writable } from 'svelte/store';
  import { onMount } from 'svelte';
  import { API_ENDPOINTS } from '$lib/utils/api';


  type EntrySet = {
    id: number;
    date: string;
    voucherNumber: string;
    remarks: string;
    detailedSubject: string;
    category: string;
    quantity: string;
    specifications: string;
    accountSubject: string;
    debitAmount: string;
    creditAmount: string;
    exchangeRate: string;
    price: string;
    unit: string;
    customer: string;
    paymentStatus: string;
    status: string;
    isPreviewMode: boolean;
    entryType: 'debit' | 'credit';
  };


  type ImbalancedVoucher = {
    voucherNumber: string;
    debitAmount: number;
    creditAmount: number;
    imbalanceAmount: number;
    imbalanceType: 'Excess Debit' | 'Excess Credit';
  };


  const createInitialEntrySet = (): EntrySet => ({
    id: Date.now(),
    date: '',
    voucherNumber: '',
    remarks: '',
    detailedSubject: '',
    category: '',
    quantity: '',
    specifications: '',
    accountSubject: '',
    debitAmount: '',
    creditAmount: '0',
    exchangeRate: '',
    price: '',
    unit: 'EUR',
    customer: '',
    paymentStatus: '',
    status: '',
    isPreviewMode: false,
    entryType: 'debit',
  });

  const entrySets = writable<EntrySet[]>([createInitialEntrySet()]);

  let availableFiles: string[] = [];
  let selectedFile: string = '';
  let newFileName: string = '';
  const imbalancedVouchersStore = writable<ImbalancedVoucher[]>([]);
  let isLoading = false;

  const currencyUnits = ['USD', 'EUR', 'GBP', 'JPY', 'CNY', 'AUD', 'CAD', 'CHF', 'HKD', 'SGD'];

  function addEntrySet() {
    entrySets.update(sets => [...sets, createInitialEntrySet()]);
  }

  function removeEntrySet(id: number) {
    entrySets.update(sets => sets.filter(set => set.id !== id));
  }


  function resetForm() {
    entrySets.set([createInitialEntrySet()]);
  }

  function clearImbalancedVouchers() {
    imbalancedVouchersStore.set([]);
  }


  function togglePreview(id: number) {
    entrySets.update(sets =>
      sets.map(set =>
        set.id === id ? { ...set, isPreviewMode: !set.isPreviewMode } : set
      )
    );
  }


  function setEntryType(id: number, type: 'debit' | 'credit') {
    entrySets.update(sets =>
      sets.map(set =>
        set.id === id
          ? {
              ...set,
              entryType: type,
              debitAmount: type === 'debit' ? set.debitAmount : '0',
              creditAmount: type === 'credit' ? set.creditAmount : '0',
            }
          : set
      )
    );
  }


  function handleAmountChange(id: number, field: 'debitAmount' | 'creditAmount', value: string) {
    const numericValue = parseFloat(value);
    const validValue = isNaN(numericValue) ? '0' : numericValue.toString();

    entrySets.update(sets =>
      sets.map(set =>
        set.id === id
          ? { ...set, [field]: validValue }
          : set
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
        alert('Failed to fetch available Excel files. Please try again.');
      }
    } catch (error) {
      console.error('Error fetching Excel files:', error);
      alert('An error occurred while fetching Excel files. Please try again.');
    }
  });

  function checkRequiredFields(set: EntrySet): string[] {
    const requiredFields = ['voucherNumber', 'accountSubject', 'customer'];
    return requiredFields.filter(field => !set[field as keyof EntrySet]);
  }

  async function handleSubmit() {
    if (selectedFile === 'new' && !newFileName.trim()) {
      alert('Please enter a name for the new Excel file.');
      return;
    }

    let missingFields: string[] = [];
    $entrySets.forEach((set, index) => {
      const emptyRequiredFields = checkRequiredFields(set);
      if (emptyRequiredFields.length > 0) {
        missingFields.push(`Entry ${index + 1}: ${emptyRequiredFields.join(', ')}`);
      }
    });

    if (missingFields.length > 0) {
      alert(`Please fill in all required fields:\n${missingFields.join('\n')}`);
      return;
    }

    const formData = new FormData();
    let filename = selectedFile === 'new' ? newFileName.trim() : selectedFile;
    
    if (!filename.toLowerCase().endsWith('.xlsx')) {
      filename += '.xlsx';
    }
    
    formData.append('filename', filename);
    formData.append('data', JSON.stringify($entrySets.map(({ isPreviewMode, ...rest }) => rest)));
    formData.append('is_new_file', selectedFile === 'new' ? 'true' : 'false');




    isLoading = true;

    try {
      const response = await fetch(API_ENDPOINTS.APPEND_EXCEL, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Response from server:', result);
        alert('Data appended successfully!');
        
        imbalancedVouchersStore.set(result.imbalancedVouchers || []);
        console.log('Imbalanced vouchers:', result.imbalancedVouchers);

        if (selectedFile === 'new') {
          availableFiles = [...availableFiles, filename];
          newFileName = '';
        }
        
        // Reset the form after a short delay
        setTimeout(() => {
          resetForm();
        }, 100);

        // Set a timer to clear imbalanced vouchers after 20 seconds
        setTimeout(() => {
          clearImbalancedVouchers();
        }, 20000);
      } else {
        const errorData = await response.json();
        alert(`Failed to append data: ${errorData.error}`);
      }
    } catch (error) {
      console.error('Error appending data:', error);
      alert('An error occurred. Please try again.');
    } finally {
      isLoading = false;
    }



}



</script>

<div class="excel-upload-entries">
  <h2>Accounting (Temporarily Abort!)</h2>

  <div class="file-selection-container">
    <div class="input-wrapper">
      <div class="file-selection">
        <label for="excel-file-select">Select Excel File to Append Data:</label>
        <div class="select-wrapper">
          <select id="excel-file-select" bind:value={selectedFile}>
            <option value="">Select a file</option>
            <option value="new">[ Create New Sheet ]</option>
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
        <div class="entry-type-selection">
          <label>
            <input type="checkbox" checked={set.entryType === 'debit'} on:change={() => setEntryType(set.id, 'debit')}>
            Debit
          </label>
          <label>
            <input type="checkbox" checked={set.entryType === 'credit'} on:change={() => setEntryType(set.id, 'credit')}>
            Credit
          </label>
        </div>
        <div class="entry-fields">
          <div class="row">
            <div class="input-group">
              <label for="date-{set.id}">日期</label>
              <input type="date" id="date-{set.id}" bind:value={set.date}>
            </div>
            <div class="input-group">
              <label for="voucherNumber-{set.id}">凭证号</label>
              <input type="text" id="voucherNumber-{set.id}" bind:value={set.voucherNumber} placeholder="凭证号" required>
            </div>
            <div class="input-group">
              <label for="remarks-{set.id}">摘要</label>
              <input type="text" id="remarks-{set.id}" bind:value={set.remarks} placeholder="摘要">
            </div>
            <div class="input-group">
              <label for="detailedSubject-{set.id}">明细科目</label>
              <input type="text" id="detailedSubject-{set.id}" bind:value={set.detailedSubject} placeholder="明细科目">
            </div>
            <div class="input-group">
              <label for="category-{set.id}">类别</label>
              <input type="text" id="category-{set.id}" bind:value={set.category} placeholder="类别">
            </div>
          </div>
          <div class="row">
            <div class="input-group">
              <label for="quantity-{set.id}">数量</label>
              <input type="number" id="quantity-{set.id}" bind:value={set.quantity} placeholder="数量">
            </div>
            <div class="input-group">
              <label for="specifications-{set.id}">规格</label>
              <input type="text" id="specifications-{set.id}" bind:value={set.specifications} placeholder="规格">
            </div>
            <div class="input-group">
              <label for="accountSubject-{set.id}">会计科目</label>
              <input type="text" id="accountSubject-{set.id}" bind:value={set.accountSubject} placeholder="会计科目" required>
            </div>
            <div class="input-group">
              <label for="debitAmount-{set.id}">借方金额</label>
              <input 
                type="number" 
                id="debitAmount-{set.id}" 
                bind:value={set.debitAmount} 
                on:input={(e) => handleAmountChange(set.id, 'debitAmount', e.target.value)}
                placeholder="借方金额" 
                disabled={set.entryType === 'credit'}
              >
            </div>
            <div class="input-group">
              <label for="creditAmount-{set.id}">贷方金额</label>
              <input 
                type="number" 
                id="creditAmount-{set.id}" 
                bind:value={set.creditAmount} 
                on:input={(e) => handleAmountChange(set.id, 'creditAmount', e.target.value)}
                placeholder="贷方金额" 
                disabled={set.entryType === 'debit'}
              >
            </div>
          </div>
          <div class="row">
            <div class="input-group">
              <label for="exchangeRate-{set.id}">汇率</label>
              <input type="number" id="exchangeRate-{set.id}" bind:value={set.exchangeRate} placeholder="汇率" step="0.0001">
            </div>
            <div class="input-group price-group">
              <label for="price-{set.id}">价格</label>
              <div class="price-input">
                <input type="number" id="price-{set.id}" bind:value={set.price} placeholder="价格" step="0.01">
                <select bind:value={set.unit}>
                  {#each currencyUnits as unit}
                    <option value={unit}>{unit}</option>
                  {/each}
                </select>
              </div>
            </div>
            <div class="input-group">
              <label for="customer-{set.id}">客户</label>
              <input type="text" id="customer-{set.id}" bind:value={set.customer} placeholder="客户" required>
            </div>
            <div class="input-group">
              <label for="paymentStatus-{set.id}">收款情况</label>
              <input type="text" id="paymentStatus-{set.id}" bind:value={set.paymentStatus} placeholder="收款情况">
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
            {#if key !== 'id' && key !== 'isPreviewMode' && key !== 'entryType'}
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
            <span>{set.isPreviewMode ? 'Edit' : 'Preview'}</span>
          </button>
          {#if $entrySets.length > 1 && !set.isPreviewMode}
            <button type="button" class="action-button remove-entry-set" on:click={() => removeEntrySet(set.id)}>
              <span>-</span>
            </button>
          {/if}
        </div>
      </div>
    </div>
  {/each}

  {#if $entrySets.every(set => !set.isPreviewMode)}
    <div class="button-container">
      <button type="button" on:click={addEntrySet} class="action-button add-entry-set">
        <span>+</span>
      </button>
    </div>
  {/if}

  <div class="submit-container">
    <button type="button" on:click={handleSubmit} class="action-button submit-entries" disabled={isLoading}>
      <span>{isLoading ? 'Submitting...' : 'Submit Entries'}</span>
    </button>
  </div>


{#if $imbalancedVouchersStore.length > 0}
  <div class="imbalanced-vouchers">
    <h3>Imbalanced Vouchers:</h3>
    <table>
      <thead>
        <tr>
          <th>Voucher Number</th>
          <th>Debit Amount</th>
          <th>Credit Amount</th>
          <th>Imbalance Amount</th>
          <th>Imbalance Type</th>
        </tr>
      </thead>
      <tbody>
        {#each $imbalancedVouchersStore as voucher}
          <tr>
            <td>{voucher.voucherNumber}</td>
            <td>{voucher.debitAmount.toFixed(2)}</td>
            <td>{voucher.creditAmount.toFixed(2)}</td>
            <td>{voucher.imbalanceAmount.toFixed(2)}</td>
            <td>{voucher.imbalanceType}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{/if}


</div>

<style>
  input {
    margin: 0;
    padding: 0;
  }

  .excel-upload-entries {
    font-family: "Zen Maru Gothic", sans-serif;
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
  }

  h2 {
    text-align: center;
    margin-bottom: 20px;
  }

  .file-selection-container {
    display: flex;
    gap: 1rem;
    align-items: flex-start;
    margin-bottom: 20px;
  }

  .input-wrapper {
    flex: 1;
    display: flex;
    flex-direction: column;
  }

  .file-selection, .new-file-input {
    display: flex;
    flex-direction: column;
  }

  .file-selection label, .new-file-input label {
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
  }

  .select-wrapper,
  .new-file-input,
  .input-group {
    position: relative;
  }

  .select-wrapper select,
  .new-file-input input,
  .input-group input,
  .input-group select {
    width: 100%;
    height: 38px;
    padding: 0.5rem;
    font-size: 0.875rem;
    border: 1px solid #ccc;
    border-radius: 0.25rem;
    box-sizing: border-box;
    line-height: normal;
    font-family: "Ubuntu", sans-serif;
    background-color: #fff;
  }

  .select-wrapper select {
    appearance: none;
    -webkit-appearance: none;
    -moz-appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23333' d='M10.293 3.293L6 7.586 1.707 3.293A1 1 0 00.293 4.707l5 5a1 1 0 001.414 0l5-5a1 1 0 10-1.414-1.414z'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 0.7em top 50%;
    background-size: 0.65em auto;
    padding-right: 1.5em;
  }

  .entry-set {
    border: 1px solid #ccc;
    padding: 1rem;
    border-radius: 0.25rem;
    margin-bottom: 1rem;
    background-color: #f9f9f9;
  }

  .entry-type-selection {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .entry-type-selection label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
  }

  .entry-fields {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .entry-fields .row {
    display: flex;
    flex-wrap: nowrap;
    gap: 1rem;
  }

  .entry-fields .row .input-group {
    flex: 1;
    min-width: 0;
  }

  .input-group {
    display: flex;
    flex-direction: column;
  }

  .input-group label {
    font-size: 0.75rem;
    margin-bottom: 0.25rem;
    color: #555;
  }

  .input-group input,
  .input-group select,
  .price-input {
    width: 100%;
  }

  .price-input {
    display: flex;
  }

  .price-input input {
    flex: 2;
    margin-right: 5px;
  }

  .price-input select {
    flex: 1;
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
    font-family: Ubuntu, sans-serif;
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

  .action-button::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, rgba(255,255,255,0.4) 0%, rgba(255,255,255,0.1) 100%);
    z-index: 1;
  }

  .action-button::after {
    content: '';
    position: absolute;
    top: 1px;
    left: 1px;
    right: 1px;
    bottom: 1px;
    background: linear-gradient(135deg, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0.05) 100%);
    z-index: 2;
    border-radius: 3px;
  }

  .add-entry-set,
  .remove-entry-set {
    font-family: 'Ubuntu', sans-serif;
    font-size: 16px;
    font-weight: bold;
    color: #333;
    position: relative;
    overflow: hidden;
    text-shadow: 0 1px 1px rgba(0,0,0,0.1);
    box-shadow: 
      0 2px 5px rgba(0,0,0,0.2),
      0 3px 8px rgba(0,0,0,0.1),
      0 1px 1px rgba(255,255,255,0.5) inset;
  }

  .add-entry-set::before,
  .remove-entry-set::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, rgba(255,255,255,0.4) 0%, rgba(255,255,255,0.1) 100%);
    z-index: 1;
  }

  .add-entry-set::after,
  .remove-entry-set::after {
    content: '';
    position: absolute;
    top: 1px;
    left: 1px;
    right: 1px;
    bottom: 1px;
    background: linear-gradient(135deg, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0.05) 100%);
    z-index: 2;
    border-radius: 3px;
  }

  .add-entry-set {
    background-color: rgba(40, 167, 69, 0.8);
  }

  .add-entry-set:hover {
    background-color: rgba(40, 167, 69, 0.9);
    box-shadow: 
      0 4px 8px rgba(0,0,0,0.3),
      0 6px 12px rgba(0,0,0,0.2),
      0 1px 1px rgba(255,255,255,0.7) inset;
  }

  .remove-entry-set {
    background-color: rgba(220, 53, 69, 0.8);
  }

  .remove-entry-set:hover {
    background-color: rgba(220, 53, 69, 0.9);
    box-shadow: 
      0 4px 8px rgba(0,0,0,0.3),
      0 6px 12px rgba(0,0,0,0.2),
      0 1px 1px rgba(255,255,255,0.7) inset;
  }

  .add-entry-set span,
  .remove-entry-set span {
    position: relative;
    z-index: 3;
  }

  .preview-button {
    background-color: rgba(0, 123, 255, 0.8);
  }

  .preview-button:hover {
    background-color: rgba(0, 123, 255, 0.9);
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
    background-color: rgba(0, 123, 255, 0.8);
    padding: 0.5rem 1rem;
    font-size: 1rem;
  }

  .submit-entries:hover {
    background-color: rgba(0, 123, 255, 0.9);
    box-shadow: 
      0 4px 8px rgba(0,0,0,0.3),
      0 6px 12px rgba(0,0,0,0.2),
      0 1px 1px rgba(255,255,255,0.7) inset;
  }

  .submit-entries:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
  }

  .preview-content {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 1rem;
    background-color: #fff;
    padding: 1rem;
    border-radius: 0.25rem;
  }

  .preview-item {
    display: flex;
    flex-direction: column;
  }

  .preview-label {
    font-size: 0.75rem;
    font-weight: bold;
    color: #555;
  }

  .preview-value {
    font-size: 0.875rem;
    color: blue;
  }

  .imbalanced-vouchers {
    margin-top: 1rem;
    padding: 1rem;
    background-color: #fff3cd;
    border: 1px solid #ffeeba;
    border-radius: 0.25rem;
  }

  .imbalanced-vouchers h3 {
    margin-top: 0;
    color: #856404;
    font-size: 1rem;
    margin-bottom: 0.5rem;
  }

  .imbalanced-vouchers table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 1rem;
  }

  .imbalanced-vouchers th,
  .imbalanced-vouchers td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
  }

  .imbalanced-vouchers th {
    background-color: #f2f2f2;
    font-weight: bold;
  }

  .imbalanced-vouchers tr:nth-child(even) {
    background-color: #f9f9f9;
  }

  .imbalanced-vouchers tr:hover {
    background-color: #f5f5f5;
  }

  input[type="date"] {
    position: relative;
  }

  input[type="date"]::-webkit-calendar-picker-indicator {
    position: absolute;
    top: 0;
    right: 0;
    bottom: 0;
    width: 2em;
    height: auto;
    opacity: 0;
    cursor: pointer;
  }

  input[type="date"]::after {
    content: "\25BC";
    position: absolute;
    top: 50%;
    right: 0.7em;
    transform: translateY(-50%);
    color: #333;
    font-size: 0.7em;
    pointer-events: none;
  }

  input:disabled,
  select:disabled {
    background-color: #f0f0f0;
    cursor: not-allowed;
  }

  .select-wrapper select:focus,
  .new-file-input input:focus,
  .input-group input:focus,
  .input-group select:focus {
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 0 2px rgba(0,123,255,0.25);
  }

  @media (max-width: 768px) {
    .file-selection-container {
      flex-direction: column;
    }

    .entry-fields .row {
      flex-direction: column;
    }

    .entry-fields .row .input-group {
      flex: 1 1 100%;
    }

    .entry-set-actions {
      flex-direction: column;
      align-items: flex-start;
    }

    .left-actions {
      margin-bottom: 0.5rem;
    }
  }
</style>

