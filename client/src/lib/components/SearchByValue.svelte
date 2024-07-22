


<script lang="ts">
    import { onMount } from 'svelte';
    import FunctionalDisplay from './FunctionalDisplay.svelte';
    import { API_ENDPOINTS, constructUrl } from '$lib/utils/api';

    interface Sample {
        referenceNumber: string;
        tags: string[];
        date: string;
        sample_token?: string;
    }

    export let searchOption = '';
    export let searchCollection: string[] = [];
    export let searchKey: string[] = [];

    let resultsChanged = false;

    // Define the list of allowed keys and collections
    const allowedKeys = ['reference_no', 'tags', 'categories', 'sample_token', 'timestamp'];
    const allowedCollections = ['samples', 'samples_list'];

    let collections: string[] = [];
    let keys: string[] = [];
    let results: Sample[] = [];
    export let deepCopiedResults: Sample[] = [];

    let selectedCollectionName: string = '';
    let selectedKey: string = '';
    let valueToSearch: string = '';

    let selectedSamplingKey: string = 'reference_no';
    let defaultSamplingCollection: string = 'samples';
    let selectedSamplingCollection: string = defaultSamplingCollection;

    let isAddOperation: boolean = true;

    $: isSamplingMode = searchOption === 'sampling';

    onMount(async () => {
        await fetchCollections();
    });

    async function fetchCollections() {
        try {
            const response = await fetch(API_ENDPOINTS.FETCH_COLLECTIONS);
            if (response.ok) {
                const data = await response.json();
                collections = data.collections.filter(collection => 
                    allowedCollections.includes(collection) &&
                    (searchCollection.length === 0 || searchCollection.includes(collection))
                );
                if (collections.includes(defaultSamplingCollection)) {
                    selectedSamplingCollection = defaultSamplingCollection;
                } else if (collections.length > 0) {
                    selectedSamplingCollection = collections[0];
                }
            } else {
                throw new Error('Failed to fetch collections');
            }
        } catch (error) {
            console.error('Error fetching collections:', error);
            // Consider adding user-friendly error handling here
        }
    }

    function toggleMode() {
        clearResults();
        searchOption = isSamplingMode ? '' : 'sampling';
        resetSearch();
    }

    function clearResults() {
        results = [];
        deepCopiedResults = [];
        console.log("Results cleared due to mode switch");
    }

    function resetSearch() {
        selectedKey = '';
        valueToSearch = '';
        if (isSamplingMode) {
            selectedSamplingCollection = collections.includes(defaultSamplingCollection) 
                ? defaultSamplingCollection 
                : (collections.length > 0 ? collections[0] : '');
        } else {
            selectedCollectionName = '';
        }
    }

    async function updateKeys() {
        if (selectedCollectionName) {
            try {
                const url = constructUrl(API_ENDPOINTS.FETCH_KEYS, { collection: selectedCollectionName });
                const response = await fetch(url);
                if (response.ok) {
                    const data = await response.json();
                    keys = data.keys.filter(key => 
                        allowedKeys.includes(key) && (searchKey.length === 0 || searchKey.includes(key))
                    );
                } else {
                    throw new Error('Failed to fetch keys');
                }
            } catch (error) {
                console.error('Error fetching keys:', error);
                // Consider adding user-friendly error handling here
            }
        } else {
            keys = [];
        }
        selectedKey = ''; 
    }

    async function search() {
        let searchCollection = isSamplingMode ? selectedSamplingCollection : selectedCollectionName;
        let searchKey = isSamplingMode ? selectedSamplingKey : selectedKey;

        if (!searchCollection || !searchKey || !valueToSearch) {
            console.error('Collection, key, and value must be provided');
            // Consider adding user-friendly error message here
            return;
        }

        try {
            const url = constructUrl(API_ENDPOINTS.SEARCH_RESULTS, {
                collection: searchCollection,
                key: searchKey,
                value: valueToSearch
            });

            const response = await fetch(url);

            if (response.ok) {
                const data = await response.json();
                let newResults = Array.isArray(data) && data.length && Array.isArray(data[0]) ? data[0] : data;
                
                if (isSamplingMode) {
                    // original length 
                    const oldLength = results.length;
                    if (isAddOperation) {
                        // Filter out duplicates based on reference_no
                        newResults = newResults.filter(newResult => 
                            !results.some(existingResult => 
                                existingResult.reference_no === newResult.reference_no
                            )
                        );
                        results = [...results, ...newResults];
                    } else {
                        // Remove samples based on the search criteria
                        results = results.filter(result => 
                            !(result[searchKey] === valueToSearch)
                        );
                    }
                    deepCopiedResults = JSON.parse(JSON.stringify(results));
                    valueToSearch = '';
                    
                    // Set the flag if the length has changed
                    resultsChanged = oldLength !== results.length;
                } else {
                    results = newResults;
                    deepCopiedResults = JSON.parse(JSON.stringify(results));
                }
            } else {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Error searching collection');
            }
        } catch (error) {
            console.error('Error searching collection:', error);
            // Consider adding user-friendly error handling here
        }
    }

    function toggleAddRemove(add: boolean) {
        isAddOperation = add;
        search();
    }



</script>

<div class="search-container">

    <div class="mode-switch">
        <label class="switch">
            <input type="checkbox" checked={isSamplingMode} on:change={toggleMode}>
            <span class="slider round"></span>
        </label>
        <h3><span class="mode-label">&nbsp;{isSamplingMode ? 'Sampling' : 'Normal'} Mode</span></h3>
    </div>

    <div class="search-controls">
        {#if isSamplingMode}
            <select class="custom-select" bind:value={selectedSamplingCollection}>
                <option value="">Select Collection</option>
                {#each collections as collection}
                    <option value={collection}>{collection}</option>
                {/each}
            </select>
            <select class="custom-select" bind:value={selectedSamplingKey}>
                {#each allowedKeys as key}
                    <option value={key}>{key}</option>
                {/each}
            </select>
        {:else}
            <select class="custom-select" bind:value={selectedCollectionName} on:change={updateKeys}>
                <option value="">Select Collection</option>
                {#each collections as collection}
                    <option value={collection}>{collection}</option>
                {/each}
            </select>
            {#if keys.length > 0}
                <select class="custom-select" bind:value={selectedKey}>
                    <option value="">Select a key</option>
                    {#each keys as key}
                        <option value={key}>{key}</option>
                    {/each}
                </select>
            {/if}
        {/if}

        <div class="input-group">
            <input type="text" bind:value={valueToSearch} placeholder="Enter search value">

            {#if isSamplingMode}
                <button on:click={() => toggleAddRemove(true)} class="sampling-button" class:active={isAddOperation}>Add</button>
                <button on:click={() => toggleAddRemove(false)} class="sampling-button" class:active={!isAddOperation}>Remove</button>
            {:else}

                <button on:click={search}>Search</button>
            {/if}
        </div>
    </div>
</div>

<FunctionalDisplay {results} {deepCopiedResults} {searchOption} {resultsChanged} />

<style>
    .search-container {
        font-family: 'Ubuntu', sans-serif;
        max-width: 600px;
        margin: 0 auto;
        padding: 20px;
        background-color: #f5f5f5;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }


    .search-controls {
        display: flex;
        flex-direction: column;
        gap: 15px;
    }

    .custom-select {
        font-family: "Ubuntu";
        appearance: none;
        background-color: #fff;
        border: 1px solid #ccc;
        padding: 10px;
        font-size: 16px;
        border-radius: 4px;
        width: 100%;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' fill='%23333' viewBox='0 0 16 16'%3E%3Cpath d='M7.247 11.14L2.451 5.658C1.885 5.013 2.345 4 3.204 4h9.592a1 1 0 0 1 .753 1.659l-4.796 5.48a1 1 0 0 1-1.506 0z'/%3E%3C/svg%3E");
        background-repeat: no-repeat;
        background-position: right 10px center;
    }

    .custom-select option {
        padding: 10px;
        background-color: #fff;
        color: #333;
    }

    .custom-select option:hover,
    .custom-select option:focus,
    .custom-select option:active {
        background-color: #007bff;
        color: #fff;
    }

    .input-group {
        display: flex;
        gap: 10px;
    }

    input[type="text"] {
        flex-grow: 1;
        padding: 10px;
        font-size: 16px;
        border: 1px solid #ccc;
        border-radius: 4px;
    }




  .input-group button {
      padding: 10px 20px;
      font-size: 16px;
      color: #fff;
      background-color: #007bff;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      transition: background-color 0.3s;
  }

  .input-group button:hover {
      background-color: #0056b3;
  }

  .input-group button.sampling-button {
      /* color: #040c24; */
      /* background-color: #A1EFD3; */
      background-color: #007bff;
  }

  .input-group button.sampling-button:hover {
      background-color: #4fd6be;
  }

  .input-group button.sampling-button.active {
      /* color: #040c24; */
      /* background-color: #A1EFD3; */
      background-color: #007bff;
  }

  /* New rule to ensure hover effect works on active buttons */
  .input-group button.sampling-button.active:hover {
      background-color: #4fd6be;
  }





    .mode-switch {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
    }

    .mode-label {
        margin-left: 0.5rem;
    }

    .switch {
        position: relative;
        display: inline-block;
        width: 60px;
        height: 34px;
    }

    .switch input {
        opacity: 0;
        width: 0;
        height: 0;
    }

    .slider {
        position: absolute;
        cursor: pointer;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: #ccc;
        transition: .4s;
    }

    .slider:before {
        position: absolute;
        content: "";
        height: 26px;
        width: 26px;
        left: 4px;
        bottom: 4px;
        background-color: white;
        transition: .4s;
    }


    input:checked + .slider {
        background-color: #4fd6be;
    }

    input:focus + .slider {
        box-shadow: 0 0 1px #4fd6be;
    }

    input:checked + .slider:before {
        transform: translateX(26px);
    }

    .slider.round {
        border-radius: 34px;
    }

    .slider.round:before {
        border-radius: 50%;
    }
</style>
