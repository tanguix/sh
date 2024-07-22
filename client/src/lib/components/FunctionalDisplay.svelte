

<script lang="ts">
  import { BASE_URL, API_ENDPOINTS } from '../utils/api';
  import { page } from '$app/stores';
  import { get } from 'svelte/store';
  import { writable } from 'svelte/store';
  import { unsavedChanges } from '$lib/utils/vars';
  import { loadBase64Font, addImageToPDF, generatePDF } from '$lib/utils/pdf';

  export let results: any[] = [];
  export let deepCopiedResults: any[] = [];
  export let searchOption: string = '';

  export let resultsChanged = false;

  export let keysToExclude: string[] = ['image_url', 'file'];
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
  let selectedKeys = {};
  let selectedDates = writable({});
  let removeClickCounts = writable({});
  let selectedForRemoval = writable({});
  let unsavedChangesByIndex = writable({});
  let formActionClicked = writable({});

  $: isEditingEnabled = searchOption === 'sampling';

  function filterDisplayedKeys(results) {
    return Object.fromEntries(
      Object.entries(results).filter(([key]) => !keysToExclude.includes(key))
    );
  }

  function formatPropertyValue(key: string, value: any) {
    if (key === 'modifiedBy' && Array.isArray(value) && value.length > 0) {
      const lastModifier = value[value.length - 1];
      return `${lastModifier.name} (${lastModifier.role})`;
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
          acc[curr.key] = curr.value; // value is already an array for tags and categories
        } else {
          acc[curr.key] = curr.value;
        }
      } else if (curr.key && curr.isRemove) {
        acc[curr.key] = undefined;  // Set to undefined for removal
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

    console.log(`Updated result at index ${index}:`, results[index]);
  }

  async function pushChangesToBackend() {
    try {
      if (JSON.stringify(deepCopiedResults) !== JSON.stringify(results) || resultsChanged) {
        console.log("Changes detected, pushing to backend...");
        
        const resultsWithTimestamp = results.map(result => ({
          ...result,
          timestamp: Date.now()
        }));

        console.log("Pushing results to backend:", resultsWithTimestamp);

        const response = await fetch(API_ENDPOINTS.UPLOAD_SAMPLE, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(resultsWithTimestamp),
        });

        if (!response.ok) throw new Error('Failed to upload sample data');

        const sampling_response = await response.json();
        console.log("Backend response:", sampling_response);

        if (sampling_response.sample_token) {
          results = results.map(result => ({
            ...result,
            sample_token: sampling_response.sample_token
          }));

          if (sampling_response.kept_ids && sampling_response.kept_ids.length > 0) {
            console.log("Some original items were kept:", sampling_response.kept_ids);
          }

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
</script>

<div class="results-container">
  {#if results.length > 0}
    {#each results as result, index}
      <div class="result-card">
        <h3>{result.sample_token || 'No Sample Token'}</h3>
        <div class="result-content-wrapper">
          <div class="result-content">
            <div class="image-container">
              {#if result.image_url}
                <div class="image-frame">
                  <img 
                    src={result.image_url} 
                    alt="sample_image" 
                    on:error={handleImageError}
                  >
                </div>
              {:else}
                <div class="no-image">No image available</div>
              {/if}
            </div>

            <div class="properties-container">
              {#each Object.entries(filterDisplayedKeys(result)) as [key, value]}
                <div class="property-item">
                  <span class="property-key">{key}:</span>
                  <span class="property-value">{formatPropertyValue(key, value)}</span>
                </div>
              {/each}
            </div>
          </div>
        </div>
        {#if isEditingEnabled}
          <div class="form-controls">
            <button on:click={() => addForm(index)}>Add Field</button>
            {#if canRemove[index]}
              <button on:click={() => removeKey(index)}>Remove Field</button>
            {/if}
          </div>
          {#if $displayedForms[index]}
            <div class="additional-forms">
              {#each $displayedForms[index] as form, entryIndex}
                <div class="form-entry">
                  <form on:submit|preventDefault>
                    {#if form.isRemove}
                      <label for={`key-${index}-${entryIndex}`}>Select Key to Remove:</label>
                      <select id={`key-${index}-${entryIndex}`} on:change={e => updateForm(index, entryIndex, 'key', e.target.value)}>
                        <option value="">Select key</option>
                        {#each Object.keys(results[index]) as key}
                          {#if !keysToExclude.includes(key) && !($selectedForRemoval[index] || []).includes(key)}
                            <option value={key}>{key}</option>
                          {/if}
                        {/each}
                      </select>
                    {:else}
                      <div class="input-group">
                        <input id={`key-${index}-${entryIndex}`} type="text" placeholder="Key" on:input={e => updateForm(index, entryIndex, 'key', e.target.value)} value={form.key} readonly={form.isDate} />
                        <input id={`value-${index}-${entryIndex}`} type={form.isDate ? 'date' : 'text'} placeholder="Value" on:input={e => updateForm(index, entryIndex, 'value', e.target.value)} value={form.rawValue} />
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
              <button on:click={() => updateResults(index)}>Update</button>
            {/if}
            {#if $formActionClicked[index]}
              <button on:click={() => lessForm(index)} class="secondary">Cancel</button>
            {/if}
          </div>
        {/if}
      </div>
    {/each}

    <div class="global-actions">
      {#if isEditingEnabled && (Object.values($unsavedChangesByIndex).some(Boolean) || resultsChanged)}
        <button on:click={pushChangesToBackend}>Push Changes</button>
      {/if}
      <button on:click={generatePDFWrapper}>Download PDF</button>
    </div>

  {:else}
    <p class="no-results">No results found</p>
  {/if}
</div>



<style>
  .results-container {
    font-family: 'Ubuntu', sans-serif;
    max-width: 1000px;
    margin: 0 auto;
    padding: 20px;
  }

  .result-card {
    background-color: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    margin-bottom: 20px;
    padding: 20px;
  }

  h3 {
    color: #333;
    margin-bottom: 15px;
  }

  .result-content-wrapper {
    overflow: hidden;
  }

  .result-content {
    display: flex;
    gap: 20px;
    margin-bottom: 15px;
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

  .image-frame {
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

  .no-image {
    color: #999;
    font-style: italic;
  }

  .properties-container {
    flex: 0 0 33.33%;
    background-color: #f9f9f9;
    border-radius: 4px;
    padding: 15px;
    overflow-y: auto;
    max-height: 400px;
  }

  .property-item {
    width: 100%;
    margin-bottom: 10px;
    padding-bottom: 10px;
    line-height: 1.4;
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
    background-color: #ccc;
  }

  button:hover {
    background-color: #FFE6B3;
  }

  button.secondary {
    background-color: #ccc;
  }

  button.secondary:hover {
    background-color: #FFE6B3;
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

  input[type="text"], input[type="date"], select {
    flex-grow: 1;
    padding: 8px;
    font-size: 14px;
    border: 1px solid #ccc;
    border-radius: 4px;
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

  @media (max-width: 768px) {
    .result-content {
      flex-direction: column;
    }

    .image-container, .properties-container {
      flex: 0 0 auto;
      width: 100%;
    }

    .image-container {
      height: 300px;
    }

    .properties-container {
      max-height: none;
    }
  }
</style>



