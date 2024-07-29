

<script lang="ts">
  import { API_ENDPOINTS } from '$lib/utils/api';
  import { page } from '$app/stores';
  import { get } from 'svelte/store';
  import { writable } from 'svelte/store';
  import { unsavedChanges } from '$lib/utils/vars';
  import { generatePDF } from '$lib/utils/pdf';


  interface InventoryItem {
    putIn: number;
    takeOut: number;
    by: string;
    timestamp: number;
  }


  interface Sample {
    reference_no: string;  // Changed from referenceNumber
    tags: string[];
    date: string;
    image_url: string;
    modifiedBy: string[];
    sample_token?: string;
    total_inventory: number;
    inventory: InventoryItem[];
  }


  export let results: Sample[] = [];
  export let deepCopiedResults: Sample[] = [];
  export let searchOption: string = '';
  export let resultsChanged = false;
  export let resultCount: number = 0;

  // expanded items limit
  let expandedItems = new Set<number>();

  export let keysToExclude: string[] = ['image_url', 'file', 'inventory', 'sample_token'];
  let content: string = `
      Marks & Order Nos.(标志及订单号码)\n
      Description & Specifications (描述及规格)\n
      Unit Price (单价)\n
      Total Price (总值)\n
      H.S.CODE (商品编码)\n
      From 由\n
      To 至
  `;

  const displayedForms = writable({});
  let removeClickCounts = writable({});
  let selectedForRemoval = writable({});
  let unsavedChangesByIndex = writable({});
  let formActionClicked = writable({});
  let dropSampleClicked = writable<{[key: number]: boolean}>({});
  let pendingRemoval = writable<{[key: number]: boolean}>({});

  const errorMessage = writable('');
  const isLoading = writable(false);

  $: isEditingEnabled = searchOption === 'sampling';

  let isGridView = true;
  let expandedItemIndex: number | null = null;

  let isModalOpen = false;
  let currentInventory: InventoryItem[] = [];

  function toggleExpandItem(index: number) {
    if (isGridView) {
      if (expandedItems.has(index)) {
        expandedItems.delete(index);
      } else {
        if (expandedItems.size >= 2) {
          expandedItems.delete(expandedItems.values().next().value);
        }
        expandedItems.add(index);
      }
      expandedItems = expandedItems; // Trigger reactivity
    }
  }

  function filterDisplayedKeys(result: any) {
    return Object.fromEntries(
      Object.entries(result).filter(([key]) => !keysToExclude.includes(key))
    );
  }



  function formatPropertyValue(key: string, value: any) {
    if (key === 'modifiedBy' && Array.isArray(value) && value.length > 0) {
      const lastModifier = value[value.length - 1];
      return `${lastModifier.name} (${lastModifier.role})`;
    } else if (key === 'additional_image_path' && Array.isArray(value)) {
      return value;
    } else if (key === 'unit_price' || key === 'unit_weight') {
      return `${value.num} ${value.unit}`;
    } else if (key === 'total_inventory') {
      return value.toString();
    } else if (Array.isArray(value)) {
      return value.join(', ');
    } else if (typeof value === 'object' && value !== null) {
      return JSON.stringify(value);
    }
    return value;
  }



  async function generatePDFWrapper() {
    await generatePDF(results, content);
  }

  function addForm(index: number) {
    displayedForms.update(forms => {
      if (!forms[index]) {
        forms[index] = [];
      }
      forms[index].push({ key: '', value: '', isRemove: false, rawValue: '' });
      return forms;
    });
    setUnsavedChanges(index, true);
    formActionClicked.update(clicked => {
      clicked[index] = true;
      return clicked;
    });
    dropSampleClicked.update(clicked => {
      clicked[index] = false;
      return clicked;
    });
  }

  function removeKey(index: number) {
    displayedForms.update(forms => {
      if (!forms[index]) {
        forms[index] = [];
      }
      forms[index].push({ key: '', isRemove: true });
      return forms;
    });

    removeClickCounts.update(counts => {
      counts[index] = (counts[index] || 0) + 1;
      return counts;
    });
    setUnsavedChanges(index, true);
    formActionClicked.update(clicked => {
      clicked[index] = true;
      return clicked;
    });
    dropSampleClicked.update(clicked => {
      clicked[index] = false;
      return clicked;
    });
  }

  function confirmDropSample(index: number) {
    pendingRemoval.update(pending => {
      pending[index] = true;
      return pending;
    });
  }

  async function dropSample(index: number) {
    const sampleToDelete = results[index];
    const sampleToken = sampleToDelete.sample_token;
    const referenceNo = sampleToDelete.reference_no;

    if (!sampleToken || !referenceNo) {
      console.error("Sample token or reference number is missing");
      errorMessage.set("Unable to drop sample: Missing sample token or reference number");
      return;
    }

    isLoading.set(true);
    errorMessage.set('');

    try {
      const response = await fetch(API_ENDPOINTS.UPLOAD_SAMPLE, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify([{ 
          _remove: true, 
          sample_token: sampleToken,
          reference_no: referenceNo,
          ...sampleToDelete
        }]),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to drop sample');
      }

      const result = await response.json();
      console.log("Sample dropped:", result);

      results = results.filter((_, i) => i !== index);
      resultsChanged = true;

      displayedForms.update(forms => {
        delete forms[index];
        return forms;
      });
      unsavedChangesByIndex.update(changes => {
        delete changes[index];
        return changes;
      });
      formActionClicked.update(clicked => {
        delete clicked[index];
        return clicked;
      });
      dropSampleClicked.update(clicked => {
        delete clicked[index];
        return clicked;
      });
      pendingRemoval.update(pending => {
        delete pending[index];
        return pending;
      });

      console.log(`Sample with reference number ${referenceNo} dropped successfully`);

    } catch (error) {
      console.error("Error dropping sample:", error.message);
      errorMessage.set(error.message);
    } finally {
      isLoading.set(false);
    }
  }

  function cancelDropSample(index: number) {
    pendingRemoval.update(pending => {
      delete pending[index];
      return pending;
    });
  }

  function lessForm(index: number) {
    displayedForms.update(forms => {
      if (!forms || !forms[index] || forms[index].length === 0) {
        return forms;
      }
      forms[index].pop();
      if (forms[index].length === 0) {
        delete forms[index];
      }
      return forms;
    });

    removeClickCounts.update(counts => {
      if (counts[index] > 0) {
        counts[index]--;
      }
      return counts;
    });

    selectedForRemoval.update(selections => {
      delete selections[index];
      return selections;
    });

    if (!hasDisplayedForms(index)) {
      results[index] = { ...deepCopiedResults[index] };
      setUnsavedChanges(index, false);
      formActionClicked.update(clicked => {
        clicked[index] = false;
        return clicked;
      });
      dropSampleClicked.update(clicked => {
        delete clicked[index];
        return clicked;
      });
    }
  }

  function hasDisplayedForms(index: number): boolean {
    return $displayedForms[index] && $displayedForms[index].length > 0;
  }

  function updateForm(index: number, entryIndex: number, field: string, value: string) {
    displayedForms.update(forms => {
      if (forms[index] && forms[index][entryIndex]) {
        if (field === 'key') {
          forms[index][entryIndex][field] = value;
          forms[index][entryIndex].value = '';
          forms[index][entryIndex].rawValue = '';
        } else if (field === 'value') {
          forms[index][entryIndex].rawValue = value;
          if (forms[index][entryIndex].isDate) {
            forms[index][entryIndex].value = new Date(value).toISOString().split('T')[0];
          } else if (forms[index][entryIndex].key === 'tags' || forms[index][entryIndex].key === 'categories') {
            forms[index][entryIndex].value = value.split(',').map(item => item.trim()).filter(item => item !== '');
          } else {
            forms[index][entryIndex].value = value;
          }
        }
      }
      return forms;
    });
    setUnsavedChanges(index, true);
  }

  function toggleDateInput(index: number, entryIndex: number) {
    displayedForms.update(forms => {
      if (forms[index] && forms[index][entryIndex]) {
        forms[index][entryIndex].isDate = !forms[index][entryIndex].isDate;
        if (forms[index][entryIndex].isDate) {
          forms[index][entryIndex].key = 'delivery_date';
          forms[index][entryIndex].value = '';
          forms[index][entryIndex].rawValue = '';
        } else {
          forms[index][entryIndex].key = '';
          forms[index][entryIndex].value = '';
          forms[index][entryIndex].rawValue = '';
        }
      }
      return forms;
    });
    setUnsavedChanges(index, true);
  }

  function updateResults(index: number) {
    const user = get(page).data.user;
    if (!user) {
      console.error("User is undefined");
      return;
    }

    const formData = $displayedForms[index] || [];
    const updates = formData.reduce((acc, curr) => {
      if (curr.key && !curr.isRemove) {
        if (curr.key === 'tags' || curr.key === 'categories') {
          acc[curr.key] = curr.value;
        } else {
          acc[curr.key] = curr.value;
        }
      } else if (curr.key && curr.isRemove) {
        acc[curr.key] = null;
      }
      return acc;
    }, {});

    results[index] = { ...results[index], ...updates };
    
    Object.keys(results[index]).forEach(key => {
      if (results[index][key] === null) {
        delete results[index][key];
      }
    });

    if (results[index].modifiedBy) {
      results[index].modifiedBy = Array.isArray(results[index].modifiedBy)
        ? [...results[index].modifiedBy, user]
        : [results[index].modifiedBy, user];
    } else {
      results[index].modifiedBy = [user];
    }

    displayedForms.update(forms => {
      delete forms[index];
      return forms;
    });
    setUnsavedChanges(index, false);
    formActionClicked.update(clicked => {
      clicked[index] = false;
      return clicked;
    });
    dropSampleClicked.update(clicked => {
      delete clicked[index];
      return clicked;
    });

    console.log(`Updated result at index ${index}:`, results[index]);
    resultsChanged = true;
  }

  async function pushChangesToBackend() {
    isLoading.set(true);
    errorMessage.set('');
    
    try {
      if (JSON.stringify(deepCopiedResults) !== JSON.stringify(results) || resultsChanged) {
        console.log("Changes detected, pushing to backend...");

        const user = get(page).data.user;
        if (!user) throw new Error("User is undefined");

        const updatedResults = results.map(result => ({
          ...result,
          timestamp: Date.now(),
          modifiedBy: Array.isArray(result.modifiedBy) 
            ? [...result.modifiedBy, user]
            : result.modifiedBy 
              ? [result.modifiedBy, user]
              : [user]
        }));

        const response = await fetch(API_ENDPOINTS.UPLOAD_SAMPLE, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updatedResults),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || 'Failed to upload sample data');
        }

        const sampling_response = await response.json();
        console.log("Backend response:", sampling_response);

        if (sampling_response.sample_token) {
          results = updatedResults.map(result => ({
            ...result,
            sample_token: sampling_response.sample_token
          }));

          deepCopiedResults = JSON.parse(JSON.stringify(results));
        }

        resultsChanged = false;
        unsavedChanges.set(false);
        unsavedChangesByIndex.set({});
      } else {
        console.log("No changes to push");
      }
    } catch (error) {
      console.error("Error pushing changes to backend:", error.message);
      errorMessage.set(error.message);
    } finally {
      isLoading.set(false);
    }
  }

  function setUnsavedChanges(index: number, value: boolean) {
    unsavedChangesByIndex.update(changes => {
      changes[index] = value;
      return changes;
    });
    unsavedChanges.set(Object.values($unsavedChangesByIndex).some(Boolean));
  }

  $: canRemove = results.map((result, index) =>
    Object.keys(filterDisplayedKeys(result)).length >
    ($removeClickCounts[index] || 0)
  );

  function handleImageError(e: Event) {
    const target = e.target as HTMLImageElement;
    console.error(`Error loading image: ${target.src}`);
    target.src = '/path/to/fallback-image.jpg';
    target.alt = 'Image not available';
  }

  function displayInventoryDetails(inventory: InventoryItem[]) {
    currentInventory = inventory;
    isModalOpen = true;
  }


  function closeModal(event?: MouseEvent | KeyboardEvent) {
    if (!event || event.type === 'click' || (event as KeyboardEvent).key === 'Escape') {
      isModalOpen = false;
    }
  }




</script>




<div class="functional-display">
  <div class="view-toggle">
    <label>
      <input type="checkbox" bind:checked={isGridView}>
      Grid View
    </label>
    {#if resultCount > 0}
      <span class="result-count">({resultCount} items found)</span>
    {/if}
  </div>

  <div class="results-container" class:grid-view={isGridView}>
    {#if $isLoading}
      <div class="loading-spinner">Loading...</div>
    {/if}

    {#if $errorMessage}
      <div class="error-message">{$errorMessage}</div>
    {/if}

    {#if results.length > 0}
      {#each results as result, index}
        <div 
          class="result-card" 
          class:grid-item={isGridView} 
          class:expanded={isGridView && expandedItems.has(index)}
        >
          {#if !isGridView || (isGridView && expandedItems.has(index))}
            <h3>{result.sample_token || 'No Sample Token'}</h3>
          {/if}
          <div class="result-content" class:grid-content={isGridView && expandedItemIndex !== index}>
            <div class="image-container" role="img" aria-label="Sample image">
              {#if result.image_url}
                <div class="image-frame">
                  <img 
                    src={result.image_url} 
                    alt="sample_image" 
                    on:error={handleImageError}
                  >

                  {#if isGridView}
                    <button 
                      class="expand-collapse-btn"
                      on:click={() => toggleExpandItem(index)}
                      aria-label={expandedItems.has(index) ? "Collapse" : "Expand"}
                    >
                      <p>{expandedItems.has(index) ? '−' : '+'}</p>
                    </button>
                  {/if}
                </div>
              {:else}
                <div class="no-image">No image available</div>
              {/if}
            </div>
            {#if isGridView && !expandedItems.has(index)}
              <div class="reference-no">{result.reference_no || 'No Reference Number'}</div>
            {/if}

            {#if !isGridView || (isGridView && expandedItems.has(index))}
              <div class="properties-wrapper">


                <div class="properties-container">
                  {#each Object.entries(filterDisplayedKeys(result)) as [key, value]}
                    <div class="property-item">
                      <span class="property-key">{key}:</span>
                      {#if key === 'total_inventory'}
                        <span class="property-value">
                          {formatPropertyValue(key, value)}
                          <button on:click={() => displayInventoryDetails(result.inventory)}>
                            View Details
                          </button>
                        </span>
                      {:else}
                        <span class="property-value">{formatPropertyValue(key, value)}</span>
                      {/if}
                    </div>
                  {/each}
                </div>


              </div>
            {/if}
          </div>
          
          {#if isEditingEnabled && (!isGridView || (isGridView && expandedItemIndex === index))}
            <div class="form-controls">
              <button on:click={() => addForm(index)}>Add Field</button>
              {#if canRemove[index]}
                <button on:click={() => removeKey(index)}>Remove Field</button>
              {/if}
              {#if $pendingRemoval[index]}
                <button on:click={() => dropSample(index)} class="update-drop">Confirm Drop</button>
                <button on:click={() => cancelDropSample(index)} class="cancel-drop">Cancel Drop</button>
              {:else}
                <button on:click={() => confirmDropSample(index)} class="drop-sample">Drop Sample</button>
              {/if}
            </div>

            {#if $displayedForms[index]}
              <div class="additional-forms">
                {#each $displayedForms[index] as form, entryIndex}
                  <div class="form-entry">
                    <form on:submit|preventDefault>
                      {#if form.isRemove && form.key !== '_remove'}
                        <label for={`key-${index}-${entryIndex}`}>Select Key to Remove:</label>
                        <select id={`key-${index}-${entryIndex}`} on:change={e => updateForm(index, entryIndex, 'key', e.target.value)}>
                          <option value="">Select key</option>
                          {#each Object.keys(results[index]) as key}
                            {#if !keysToExclude.includes(key) && !($selectedForRemoval[index] || []).includes(key)}
                              <option value={key}>{key}</option>
                            {/if}
                          {/each}
                        </select>
                      {:else if !form.isRemove}
                        <div class="input-group">
                          <input 
                            id={`key-${index}-${entryIndex}`} 
                            type="text"
                            placeholder="Key" 
                            on:input={e => updateForm(index, entryIndex, 'key', e.target.value)} 
                            value={form.key} 
                            readonly={form.isDate}
                          />
                          <input 
                            id={`value-${index}-${entryIndex}`} 
                            type={form.isDate ? 'date' : 'text'} 
                            placeholder="Value" 
                            on:input={e => updateForm(index, entryIndex, 'value', e.target.value)} 
                            value={form.rawValue}
                          />
                        </div>
                        {#if form.key === 'tags' || form.key === 'categories'}
                          <small class="helper-text">Separate multiple {form.key} with commas</small>
                        {/if}
                        <label class="custom-checkbox">
                          <input type="checkbox" on:click={() => toggleDateInput(index, entryIndex)} checked={form.isDate} />
                          <span class="checkbox-text">Date Type</span>
                        </label>
                      {/if}
                    </form>
                  </div>
                {/each}
              </div>
            {/if}
            <div class="action-buttons">
              {#if $unsavedChangesByIndex[index]}
                <button 
                  on:click={() => updateResults(index)} 
                  class={$dropSampleClicked[index] ? 'update-drop' : 'update-normal'}
                >
                  Update
                </button>
              {/if}
              {#if $formActionClicked[index]}
                <button 
                  on:click={() => lessForm(index)} 
                  class={$dropSampleClicked[index] ? 'cancel-drop' : 'cancel-normal'}
                >
                  Cancel
                </button>
              {/if}
            </div>
          {/if}
        </div>
      {/each}

      {#if !isGridView}
        <div class="global-actions">
          {#if isEditingEnabled && (Object.values($unsavedChangesByIndex).some(Boolean) || resultsChanged)}
            <button on:click={pushChangesToBackend} disabled={$isLoading}>Push Changes</button>
          {/if}
          <button on:click={generatePDFWrapper}>Download PDF</button>
        </div>
      {/if}

    {:else}
      <p class="no-results">No results found</p>
    {/if}
  </div>
</div>




{#if isModalOpen}
  <!-- svelte-ignore a11y-click-events-have-key-events -->
  <!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
  <div class="modal-overlay" 
       on:click={closeModal} 
       role="dialog"
       aria-labelledby="modal-title"
       >
    <!-- svelte-ignore a11y-click-events-have-key-events -->
    <!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
    <div class="modal-content" 
         on:click|stopPropagation 
         role="document">
      <h2 id="modal-title">Inventory Details</h2>
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
          {#each currentInventory as item}
            <tr>
              <td>{item.putIn}</td>
              <td>{item.takeOut}</td>
              <td>{item.by}</td>
              <td>{new Date(item.timestamp * 1000).toLocaleString()}</td>
            </tr>
          {/each}
        </tbody>
      </table>
      <button on:click={closeModal}>Close</button>
    </div>
  </div>
{/if}




<style>
  .functional-display {
    margin: 2rem auto;
    font-family: 'Ubuntu';
  }

  .view-toggle {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    margin-bottom: 20px;
  }

  .view-toggle label {
    display: flex;
    align-items: center;
    cursor: pointer;
    font-size: 14px;
    color: #666;
  }

  .view-toggle input[type="checkbox"] {
    margin-right: 8px;
    appearance: none;
    width: 18px;
    height: 18px;
    border: 2px solid #ccc;
    border-radius: 3px;
    outline: none;
    cursor: pointer;
    position: relative;
    transition: all 0.2s ease-in-out;
  }

  .view-toggle input[type="checkbox"]::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 60%;
    height: 60%;
    background-color: transparent;
    border-radius: 2px;
    transition: all 0.2s ease-in-out;
  }

  .view-toggle input[type="checkbox"]:checked {
    border-color: #ff7a6e;
    box-shadow: 0 0 5px rgba(0, 123, 255, 0.3);
  }

  .view-toggle input[type="checkbox"]:checked::before {
    background-color: #ff7a6e;
  }

  .result-count {
    margin-left: 15px;
    font-size: 14px;
    color: #666;
  }

  .results-container {
    font-family: 'Ubuntu', sans-serif;
    max-width: 100%;
    margin: 0 auto;
    padding: 20px;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  }

  .results-container.grid-view {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 20px;
  }

  .result-card {
    background-color: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    margin-bottom: 20px;
    padding: 20px;
  }

  .result-card.grid-item {
    margin-bottom: 0;
    padding: 10px;
    display: flex;
    flex-direction: column;
  }

  .result-content.grid-content {
    height: auto;
    display: flex;
    flex-direction: column;
  }

  h3 {
    color: #333;
    margin-bottom: 15px;
  }

  .result-content {
    display: flex;
    gap: 20px;
    margin-bottom: 15px;
    height: 400px;
  }

  .image-container {
    flex: 0 0 66.67%;
    background-color: #f5f5f5;
    border-radius: 4px;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .grid-item .image-container {
    flex: 1;
    height: 180px;
  }

  .image-frame {
    position: relative;
    width: 100%;
    height: 100%;
    background-color: white;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .image-frame img {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
  }

  .expand-collapse-btn {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background-color: rgba(0, 0, 0, 0.5);
    color: white;
    border: none;
    border-radius: 50%;
    width: 30px;
    height: 30px;
    font-size: 20px;
    cursor: pointer;
    opacity: 0;
    transition: opacity 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0;
  }

  .grid-view .expand-collapse-btn {
    opacity: 0;
  }

  .grid-view .image-frame:hover .expand-collapse-btn {
    opacity: 1;
  }

  .expand-collapse-btn p {
    margin: 0;
    line-height: 1;
  }

  .expand-collapse-btn:hover {
    background-color: rgba(0, 0, 0, 0.7);
  }

  .no-image {
    color: #999;
    font-style: italic;
  }

  .reference-no {
    margin-top: 10px;
    font-size: 12px;
    color: #666;
    text-align: center;
  }

  .properties-wrapper {
    flex: 0 0 33.33%;
    display: flex;
    flex-direction: column;
  }

  .properties-container {
    background-color: #f9f9f9;
    border-radius: 4px;
    padding: 15px;
    overflow-y: auto;
    flex-grow: 1;
    scrollbar-width: thin;
    scrollbar-color: #007bff #f0f0f0;
  }

  .properties-container::-webkit-scrollbar {
    width: 8px;
  }

  .properties-container::-webkit-scrollbar-track {
    background: #f0f0f0;
  }

  .properties-container::-webkit-scrollbar-thumb {
    background-color: #007bff;
    border-radius: 4px;
    border: 2px solid #f0f0f0;
  }


  .property-item {
      margin-bottom: 10px;
      padding-bottom: 10px;
      border-bottom: 1px solid rgba(0, 0, 0, 0.05);
    }

  .property-item:last-child {
    border-bottom: none;
    margin-bottom: 0;
    padding-bottom: 0;
  }

  .property-key {
    font-weight: bold;
    color: #555;
    display: block;
    margin-bottom: 4px;
  }

  .property-value {
    display: block;
    word-break: break-word;
    color: #007bff;
  }

  .form-controls, .action-buttons {
    display: flex;
    gap: 10px;
    margin-bottom: 15px;
  }

  button {
    padding: 8px 16px;
    font-size: 14px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.3s;
  }

  .update-normal, .cancel-normal {
    background-color: #ccc;
  }

  .update-normal:hover, .cancel-normal:hover {
    background-color: #FFE6B3;
  }

  .update-drop, .drop-sample {
    background-color: #ff4136;
    color: white;
  }

  .update-drop:hover, .drop-sample:hover {
    background-color: #ff7a6e;
  }

  .cancel-drop {
    background-color: #4fd6be;
    color: #333;
  }

  .cancel-drop:hover {
    background-color: #A1EFD3;
  }

  .additional-forms {
    margin-top: 15px;
  }

  .form-entry {
    background-color: #f9f9f9;
    border-radius: 4px;
    padding: 15px;
    margin-bottom: 10px;
  }

  .input-group {
    display: flex;
    gap: 10px;
    margin-bottom: 10px;
  }

  .input-group input {
    flex: 1 1 0;
    min-width: 0;
  }

  input[type="text"], input[type="date"], select {
    padding: 8px;
    font-size: 14px;
    border: 1px solid #ccc;
    border-radius: 4px;
    width: 100%;
  }

  .custom-checkbox {
    display: flex;
    align-items: center;
    margin-top: 10px;
  }

  .checkbox-text {
    margin-left: 5px;
  }

  .global-actions {
    margin-top: 20px;
    display: flex;
    justify-content: center;
    gap: 15px;
  }

  .global-actions button {
    color: #fff;
    background: #007bff;
  }

  .no-results {
    text-align: center;
    color: #666;
    font-style: italic;
  }

  .helper-text {
    display: block;
    font-size: 12px;
    color: #666;
    margin-top: 4px;
    font-style: italic;
  }

  .loading-spinner {
    text-align: center;
    padding: 20px;
    font-style: italic;
    color: #007bff;
  }

  .error-message {
    background-color: #ffebee;
    color: #c62828;
    padding: 10px;
    border-radius: 4px;
    margin-bottom: 15px;
    text-align: center;
  }

  .result-card.grid-item.expanded {
    grid-column: 1 / -1;
    display: flex;
    flex-direction: column;
    height: auto;
    max-width: 100%;
    padding: 20px;
  }

  .result-card.grid-item.expanded .result-content {
    display: flex;
    flex-direction: row;
    gap: 20px;
    margin-bottom: 15px;
    height: 400px;
  }

  .result-card.grid-item.expanded .image-container {
    flex: 0 0 66.67%;
    height: 100%;
  }

  .result-card.grid-item.expanded .properties-wrapper {
    flex: 0 0 33.33%;
    display: flex;
    flex-direction: column;
  }

  .result-card.grid-item.expanded .properties-container {
    background-color: #f9f9f9;
    border-radius: 4px;
    padding: 15px;
    overflow-y: auto;
    flex-grow: 1;
    scrollbar-width: thin;
    scrollbar-color: #007bff #f0f0f0;
  }

  .property-item button {
    margin-left: 10px;
    padding: 2px 5px;
    font-size: 12px;
    background-color: #f0f0f0;
    border: 1px solid #ccc;
    border-radius: 3px;
    cursor: pointer;
  }

  .property-item button:hover {
    background-color: #e0e0e0;
  }

  .modal-overlay {
    font-family: Ubuntu;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
  }

  .modal-content {
    background-color: white;
    padding: 20px;
    border-radius: 5px;
    max-width: 80%;
    max-height: 80%;
    overflow-y: auto;
  }

  .modal-content h2 {
    margin-top: 0;
  }

  .modal-content table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 20px;
  }

  .modal-content th, .modal-content td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
  }

  .modal-content th {
    background-color: #f2f2f2;
  }

  .modal-content button {
    display: block;
    margin: 0 auto;
  }

  @media (max-width: 768px) {
    .result-content {
      flex-direction: column;
      height: auto;
    }

    .image-container, .properties-wrapper {
      flex: 0 0 auto;
      width: 100%;
    }

    .image-container {
      height: 300px;
    }

    .properties-container {
      max-height: 300px;
    }

    .results-container.grid-view {
      grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    }

    .grid-item .image-container {
      height: 150px;
    }

    .result-card.grid-item.expanded .result-content {
      flex-direction: column;
      height: auto;
    }

    .result-card.grid-item.expanded .image-container,
    .result-card.grid-item.expanded .properties-wrapper {
      flex: 0 0 auto;
      width: 100%;
    }

    .result-card.grid-item.expanded .image-container {
      height: 300px;
    }
  }
</style>
