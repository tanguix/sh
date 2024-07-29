



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
    let selectedInventoryCollection: string = '';

    let isAddOperation: boolean = true;

    $: isSamplingMode = searchOption === 'sampling';
    $: isInventoryMode = searchOption === 'inventory';
    $: selectedCollection = isSamplingMode ? selectedSamplingCollection : 
                            isInventoryMode ? selectedInventoryCollection : 
                            selectedCollectionName;



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
        if (searchOption === '') {
            searchOption = 'sampling';
        } else if (searchOption === 'sampling') {
            searchOption = 'inventory';
        } else {
            searchOption = '';
        }
        resetSearch();

        if (searchOption === 'inventory') {
            searchCriteria = [{ key: 'total_inventory', value: '' }];
            keys = ['total_inventory', ...allowedKeys]; // Include both total_inventory and other keys
        } else if (searchOption === '') {
            searchCriteria = searchCriteria.map(criteria => ({ ...criteria, key: '' }));
        }
    }




    function clearResults() {
        results = [];
        deepCopiedResults = [];
        console.log("Results cleared due to mode switch");
    }



    function resetSearch() {
        if (isInventoryMode) {
            searchCriteria = [{ key: 'total_inventory', value: '' }];
            keys = ['total_inventory', ...allowedKeys]; // Include both total_inventory and other keys
        } else {
            searchCriteria = [{ key: '', value: '' }];
            keys = [...allowedKeys]; // Only include allowed keys for other modes
        }
        selectedSamplingCollection = '';
        selectedCollectionName = '';
        selectedInventoryCollection = '';
    }



    function updateSelectedCollection(event: Event) {
        const value = (event.target as HTMLSelectElement).value;
        if (isSamplingMode) {
            selectedSamplingCollection = value;
        } else if (isInventoryMode) {
            selectedInventoryCollection = value;
        } else {
            selectedCollectionName = value;
        }
        updateKeys();
    }



    async function updateKeys() {
        let collectionToUse = isSamplingMode ? selectedSamplingCollection : 
                              isInventoryMode ? selectedInventoryCollection :
                              selectedCollectionName;
        if (collectionToUse) {
            try {
                const url = constructUrl(API_ENDPOINTS.FETCH_KEYS, { collection: collectionToUse });
                const response = await fetch(url);
                if (response.ok) {
                    const data = await response.json();
                    if (isInventoryMode) {
                        keys = ['total_inventory', ...data.keys.filter(key => 
                            allowedKeys.includes(key) && (searchKey.length === 0 || searchKey.includes(key))
                        )];
                    } else {
                        keys = data.keys.filter(key => 
                            allowedKeys.includes(key) && (searchKey.length === 0 || searchKey.includes(key))
                        );
                    }
                    // Don't auto-select any key in normal mode
                    if (!isSamplingMode && !isInventoryMode) {
                        searchCriteria = searchCriteria.map(criteria => ({ ...criteria, key: '' }));
                    }
                } else {
                    throw new Error('Failed to fetch keys');
                }
            } catch (error) {
                console.error('Error fetching keys:', error);
            }
        } else {
            keys = isInventoryMode ? ['total_inventory', ...allowedKeys] : [];
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
            // Date range search
            const [startDate, endDate] = value.split(',').map(s => s.trim());
            return {
                key: criteria.key,
                value: [startDate, endDate],
                operator: 'range'
            };
        } else if (value.includes('<')) {
            // Before a specific date
            const date = value.replace('<', '').trim();
            return {
                key: criteria.key,
                value: date,
                operator: '<'
            };
        } else if (value.includes('>')) {
            // After a specific date
            const date = value.replace('>', '').trim();
            return {
                key: criteria.key,
                value: date,
                operator: '>'
            };
        } else {
            // Exact date search
            return {
                key: criteria.key,
                value: value,
                operator: 'exact'
            };
        }
    }



    function processInventoryCriteria(criteria: { key: string, value: string }) {
        const value = criteria.value.trim();
        if (value.includes(',')) {
            const [firstPart, secondPart] = value.split(',').map(s => s.trim());
            if (secondPart === '>' || secondPart === '<') {
                // Special case: "90, >" or "90, <"
                return {
                    key: criteria.key,
                    value: firstPart,
                    operator: secondPart
                };
            } else {
                // Regular range search
                return {
                    key: criteria.key,
                    value: [firstPart, secondPart],
                    operator: 'range'
                };
            }
        } else if (value.includes('<')) {
            // Less than a specific inventory
            const inventoryValue = value.replace('<', '').trim();
            return {
                key: criteria.key,
                value: inventoryValue,
                operator: '<'
            };
        } else if (value.includes('>')) {
            // Greater than a specific inventory
            const inventoryValue = value.replace('>', '').trim();
            return {
                key: criteria.key,
                value: inventoryValue,
                operator: '>'
            };
        } else {
            // Exact inventory search
            return {
                key: criteria.key,
                value: value,
                operator: 'exact'
            };
        }
    }





    // result count
    let resultCount: number = 0;

    async function search() {
        let searchCollection = isSamplingMode ? selectedSamplingCollection : 
                               isInventoryMode ? selectedInventoryCollection : 
                               selectedCollectionName;

        if (!searchCollection) {
            console.error('Collection must be selected');
            return;
        }

        // Filter out any criteria with empty key or value
        const validCriteria = searchCriteria.filter(criteria => criteria.key && criteria.value.trim());

        if (validCriteria.length === 0) {
            console.error('At least one valid search criterion must be provided');
            return;
        }


        try {

            const processedCriteria = validCriteria.map(criteria => {
                if (criteria.key === 'timestamp') {
                    return processTimestampCriteria(criteria);
                }
                if (criteria.key === 'total_inventory') {
                    return processInventoryCriteria(criteria);
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
                    resultCount = results.length;
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
            if (!isSamplingMode) {
                results = [];
                deepCopiedResults = [];
                console.log("Error occurred. Cleared previous results.");
            }
            resultCount = 0;
        }
    }






    function toggleAddRemove(add: boolean) {
        isAddOperation = add;
        search();
    }
</script>




<div class="search-container">
    <div class="mode-switch">
        <button class="toggle-button {searchOption}" on:click={toggleMode}>
            <span class="slider"></span>
        </button>
        <h3><span class="mode-label">&nbsp;{searchOption === 'inventory' ? 'Inventory' : searchOption === 'sampling' ? 'Sampling' : 'Normal'} Mode</span></h3>
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

                <select class="custom-select" 
                        bind:value={criteria.key} 
                        disabled={isInventoryMode && index === 0}
                        on:change={() => {
                            if (isInventoryMode && index === 0) {
                                criteria.key = 'inventory';
                            }
                        }}>
                    <option value="" disabled selected={criteria.key === ''}>
                        {(isInventoryMode && index === 0) ? 'inventory' : (criteria.key === '' ? 'Select a key' : criteria.key)}
                    </option>
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
    .custom-select option:sampling,
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


    .toggle-button {
        position: relative;
        width: 90px;
        height: 34px;
        background-color: #ccc;
        border: none;
        border-radius: 34px;
        cursor: pointer;
        transition: background-color 0.3s;
        overflow: hidden;
        outline: none; /* Remove default focus outline */
        -webkit-tap-highlight-color: transparent; /* Remove tap highlight on mobile devices */
    }



    .toggle-button .slider {
        position: absolute;
        height: 26px;
        width: 26px;
        left: 4px;
        top: 4px;
        background-color: white;
        transition: 0.3s;
        border-radius: 50%;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
    }



    /* Remove focus styles for all browsers */
    .toggle-button:focus,
    .toggle-button:focus-visible {
        outline: none;
        box-shadow: none;
    }



    /* Ensure the button remains accessible for keyboard navigation */
    .toggle-button:focus-visible .slider {
        /* You can add a subtle effect here if desired, e.g.: */
        box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.5);
    }



    /* For Firefox */
    .toggle-button::-moz-focus-inner {
        border: 0;
    }


    .toggle-button.sampling {
        background-color: #91DDFF;
    }

    .toggle-button.inventory {
        background-color: #F9E2Af;
    }

    .toggle-button.sampling .slider {
        transform: translateX(28px);
    }

    .toggle-button.inventory .slider {
        transform: translateX(56px);
    }


    /* Remove any potential leftover styles */
    .toggle-button::before,
    .toggle-button::after,
    .toggle-button .slider::before,
    .toggle-button .slider::after {
        content: none;
        display: none;
    }



    .switch {
        position: relative;
        display: inline-block;
        width: 90px;
        height: 34px;
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

    .slider.tri-state {
        border-radius: 34px;
    }


    .slider.tri-state:before {
        border-radius: 50%;
    }

    .sampling-button {
        background-color: #6c757d;
        color: white;
    }

    .sampling-button.active {
        background-color: #007bff;
    }




    /* Ensure responsiveness */
    @media (max-width: 768px) {
        .search-container {
            max-width: 100%;
            padding: 10px;
        }

        .search-criteria {
            flex-direction: column;
        }

        .search-criteria button {
            align-self: flex-end;
        }

        .input-group {
            flex-direction: column;
        }

        .input-group button {
            width: 100%;
        }
    }
</style>


