




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

    let searchCriteria = [{ key: '', value: '' }];
    let resultsChanged = false;

    const allowedKeys = ['reference_no', 'tags', 'categories', 'sample_token', 'timestamp'];
    const allowedCollections = ['samples', 'samples_list'];

    let collections: string[] = [];
    let keys: string[] = [];
    let results: Sample[] = [];
    export let deepCopiedResults: Sample[] = [];

    let selectedCollectionName: string = '';
    let selectedSamplingCollection: string = '';

    let isAddOperation: boolean = true;

    $: isSamplingMode = searchOption === 'sampling';
    $: selectedCollection = isSamplingMode ? selectedSamplingCollection : selectedCollectionName;

    function updateSelectedCollection(event: Event) {
        const value = (event.target as HTMLSelectElement).value;
        if (isSamplingMode) {
            selectedSamplingCollection = value;
        } else {
            selectedCollectionName = value;
        }
        updateKeys();
    }

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
            } else {
                throw new Error('Failed to fetch collections');
            }
        } catch (error) {
            console.error('Error fetching collections:', error);
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
        searchCriteria = [{ key: '', value: '' }];
        selectedSamplingCollection = '';
        selectedCollectionName = '';
        keys = [];
    }

    async function updateKeys() {
        let collectionToUse = isSamplingMode ? selectedSamplingCollection : selectedCollectionName;
        if (collectionToUse) {
            try {
                const url = constructUrl(API_ENDPOINTS.FETCH_KEYS, { collection: collectionToUse });
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
            }
        } else {
            keys = [];
        }
    }






    function addSearchCriteria() {
        searchCriteria = [...searchCriteria, { key: '', value: '' }];
    }

    function removeSearchCriteria(index: number) {
        if (searchCriteria.length > 1) {
            searchCriteria = searchCriteria.filter((_, i) => i !== index);
        }
    }




    function processTimestampCriteria(criteria: { key: string, value: string }) {
        const value = criteria.value.trim();
        if (value.includes(',')) {
            // Range or operator search
            const [date, operator] = value.split(',').map(s => s.trim());
            if (operator === '<' || operator === '>') {
                return {
                    key: criteria.key,
                    value: date,
                    operator: operator
                };
            } else {
                // Assume it's a range search
                return {
                    key: criteria.key,
                    value: value.split(',').map(s => s.trim()),
                    operator: 'range'
                };
            }
        } else {
            // Exact date search
            return {
                key: criteria.key,
                value: value,
                operator: 'exact'
            };
        }
    }



    let resultCount: number = 0;

    async function search() {
        let searchCollection = isSamplingMode ? selectedSamplingCollection : selectedCollectionName;

        if (!searchCollection || searchCriteria.some(criteria => !criteria.key || !criteria.value)) {
            console.error('Collection and all search criteria must be provided');
            return;
        }

        try {
            const processedCriteria = searchCriteria.map(criteria => {
                if (criteria.key === 'timestamp') {
                    return processTimestampCriteria(criteria);
                }
                return criteria;
            });

            const url = constructUrl(API_ENDPOINTS.SEARCH_RESULTS, {
                collection: searchCollection,
                criteria: JSON.stringify(processedCriteria)
            });

            const response = await fetch(url);

            if (response.ok) {
                const data = await response.json();
                let newResults = data.results || [];
                resultCount = data.count || 0;

                if (isSamplingMode) {
                    // Sampling mode logic
                    const oldLength = results.length;
                    if (isAddOperation) {
                        newResults = newResults.filter(newResult => 
                            !results.some(existingResult => 
                                existingResult.reference_no === newResult.reference_no
                            )
                        );
                        results = [...results, ...newResults];
                    } else {
                        results = results.filter(result => 
                            !newResults.some(newResult => 
                                newResult.reference_no === result.reference_no
                            )
                        );
                    }
                    deepCopiedResults = JSON.parse(JSON.stringify(results));
                    searchCriteria = [{ key: '', value: '' }];
                    
                    resultsChanged = oldLength !== results.length;
                    resultCount = results.length; // Update count for sampling mode
                } else {
                    // Normal mode logic
                    if (newResults.length === 0) {
                        results = [];
                        deepCopiedResults = [];
                        console.log("No results found. Cleared previous results.");
                    } else {
                        results = newResults;
                        deepCopiedResults = JSON.parse(JSON.stringify(results));
                    }
                }
            } else {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Error searching collection');
            }
        } catch (error) {
            console.error('Error searching collection:', error);
            if (!isSamplingMode) {
                results = [];
                deepCopiedResults = [];
                console.log("Error occurred. Cleared previous results.");
            }
            resultCount = 0; // Reset count on error
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
        <select class="custom-select" bind:value={selectedCollection} on:change={updateSelectedCollection}>
            <option value="">Select Collection</option>
            {#each collections as collection}
                <option value={collection}>{collection}</option>
            {/each}
        </select>

        {#each searchCriteria as criteria, index}
            <div class="search-criteria">
                <select class="custom-select" bind:value={criteria.key}>
                    <option value="">Select a key</option>
                    {#each keys as key}
                        <option value={key}>{key}</option>
                    {/each}
                </select>
                <input type="text" bind:value={criteria.value} placeholder="Enter search value">
                {#if index > 0}
                    <button on:click={() => removeSearchCriteria(index)}>-</button>
                {/if}
            </div>
        {/each}

        <button on:click={addSearchCriteria}>+</button>

        <div class="input-group">
            {#if isSamplingMode}
                <button on:click={() => toggleAddRemove(true)} class="sampling-button" class:active={isAddOperation}>Add</button>
                <button on:click={() => toggleAddRemove(false)} class="sampling-button" class:active={!isAddOperation}>Remove</button>
            {:else}
                <button on:click={search}>Search</button>
            {/if}
        </div>
    </div>
</div>

<FunctionalDisplay 
  {results} 
  {deepCopiedResults} 
  {searchOption} 
  {resultsChanged}
  {resultCount}
/>

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

    .search-criteria {
        display: flex;
        gap: 10px;
        margin-bottom: 10px;
    }

    .search-criteria button {
        padding: 5px 10px;
        background-color: #ff4136;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
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
