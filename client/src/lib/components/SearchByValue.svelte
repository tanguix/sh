
<script lang="ts">

    // onMount
    import { onMount } from 'svelte';
    import FunctionalDisplay from './FunctionalDisplay.svelte';
    import { API_ENDPOINTS, constructUrl } from '$lib/utils/api';


    // typescript interface, think of Sample as a struct in python, is a object defining a object's shape and data type
    // currently not in usually, but later could be used for "type checking", "code documentation", etc
    interface Sample {
        referenceNumber: string;
        tags: string[];
        date: string;
    }

    // option instruction for search type (general search or sampling)
    export let searchOption = '';


    // I should exclude whatever sensitive collection at the backend
    // so the searchCollection variable here for filtering is not necessary, but just keep for now
    export let searchCollection: string[] = [];
    // same here, because search method is separated with searchOption, so no need to bypass, but keep for now
    export let searchKey: string[] = [];
    // export let keysForDisplay: string[] = [];


    // backend return
    let collections: string[] = [];                 // list of collections return from backend
    let keys: string[] = [];                        // list of keys rethrn from backend
    let results: any[] = [];                        // presumably(any), array of json object matched with key search from backend
    export let deepCopiedResults = [];              // deep copy immediately after fetch from backend, pass to <FunctionalDisplay />


    // frontend
    let selectedCollectionName: string = '';        // user's selection from html select tag
    let selectedKey: string = '';                   // same as above, let declarer make it changable compared to const
    let valueToSearch: string = '';                 // user's entered for form entry



    // custom downdrop menu
    let isDropdownOpen = false;
    let selectedCollectionDisplay = 'Select Collection';

    function toggleDropdown() {
        isDropdownOpen = !isDropdownOpen;
    }

    function selectCollection(collection: string) {
        selectedCollectionName = collection;
        selectedCollectionDisplay = collection;
        isDropdownOpen = false;
        updateKeys();
    }



    // automatically fetch collections list from the backend and display in the select for user to choose
    onMount(async () => {
        try {
            // user url const to fetch
            const response = await fetch(API_ENDPOINTS.FETCH_COLLECTIONS);
            if (response.ok) {
                const data = await response.json();
                // filter collection from frontend
                collections = data.collections.filter(collection => 
                    searchCollection.length === 0 || searchCollection.includes(collection)
                );
                // console.log("Filtered collections:", collections);
            } else {
                console.error('Failed to fetch collections');
            }
        } catch (error) {
            console.error('Error fetching collections:', error);
        }
    });

    // fetch backend routes that only return keys
    async function updateKeys() {
        if (selectedCollectionName) {
            try {
                // 'http://localhost:5000/search/api/keys?collection=${encodeURIComponent(selectedCollectionName)}';
                // refer to the utils/api.ts for the API setup and constructUrl function
                const url = constructUrl(API_ENDPOINTS.FETCH_KEYS, { collection: selectedCollectionName });
                const response = await fetch(url);
                if (response.ok) {
                    const data = await response.json();
                    // filter keys here if needed
                    keys = data.keys.filter(key => 
                        searchKey.length === 0 || searchKey.includes(key)
                    );
                } else {
                    console.error('Failed to fetch keys');
                }
            } catch (error) {
                console.error('Error fetching keys:', error);
            }
        } else {
            keys = [];
        }
        selectedKey = ''; 
    }

    // actual search method
    async function search() {


        // make a check, if searchOption is passed in to this component, 
        // for example "sampling" auto-assign key to reference_no
        // and then you just need to conditionally render select or fixed form entry for search
        if (searchOption === "sampling") {
            selectedKey = "reference_no";

            try {

                // construct the search url query, "?" parameter 
                // will be append automatically by the constructUrl function
                const url = constructUrl(API_ENDPOINTS.SEARCH_RESULTS, {
                    collection: selectedCollectionName,
                    key: selectedKey,
                    value: valueToSearch
                });

                // construct url
                const response = await fetch(url);

                if (response.ok) {
                    const data = await response.json();

                    let newResults = Array.isArray(data) && data.length && Array.isArray(data[0]) ? data[0] : data;
                    results = [...results, ...newResults];
                    // deep copy immediately
                    deepCopiedResults = JSON.parse(JSON.stringify(results));
                    valueToSearch = ''; // Reset after adding

                } else {
                    const errorData = await response.json();
                    console.error('Error searching collection:', errorData.error);
                }
            } catch (error) {
                console.error('Error searching collection:', error);
            }
        }




        // normal check 
        if (!selectedCollectionName || !selectedKey || !valueToSearch) {
            return;
        }


        // if not searching method specify, do the normal search, fetch all keys
        try {
            const url = constructUrl(API_ENDPOINTS.SEARCH_RESULTS, {
                collection: selectedCollectionName,
                key: selectedKey,
                value: valueToSearch
            });

            // console.log("Search Url:", url)
            // construct
            const response = await fetch(url);


            if (response.ok) {
                const data = await response.json();
                results = data;

                // deep copy immediately
                deepCopiedResults = JSON.parse(JSON.stringify(results));

            } else {
                const errorData = await response.json();
                console.error('Error searching collection:', errorData.error);
                results = [];
            }
        } catch (error) {
            console.error('Error searching collection:', error);
            results = [];
        }
    } 
</script>





<!-- 
    design thought:  
        I want to make a tab selection here, so fuzzy search based on any key values 
        aside from fuzzy search, later you can also use unique identifier for invoice-generation search
        
        another tab for sampling search, where you can add item one by one for printing the sampling
        don't make it select tag, cause there are select tag for keys and collections already, I am tired of select tag
-->
<!-- Dropdown for selecting a collection -->



<div class="search-container">
    <h2>Search</h2>
    
    <div class="search-controls">
        <select class="custom-select" bind:value={selectedCollectionName} on:change={updateKeys}>
            <option value="">Select Collection</option>
            {#each collections as collection}
                <option value={collection}>{collection}</option>
            {/each}
        </select>

        {#if searchOption === "sampling"}
            <div class="input-group">
                <input type="text" bind:value={valueToSearch} placeholder="Enter reference number">
                <button on:click={search}>Add</button>
            </div>
        {:else}
            <div class="non-sampling-search">
                <p>Non-sampling search mode</p>
                {#if keys.length > 0}
                    <select class="custom-select" bind:value={selectedKey}>
                        <option value="">Select a key</option>
                        {#each keys as key}
                            <option value={key}>{key}</option>
                        {/each}
                    </select>
                {/if}
                {#if selectedKey}
                    <div class="input-group">
                        <input type="text" bind:value={valueToSearch} placeholder="Enter search value">
                        <button on:click={search}>Search</button>
                    </div>
                {/if}
            </div>
        {/if}
    </div>
</div>








<!-- Display the search results using DisplayResult component -->
<FunctionalDisplay {results} {deepCopiedResults}/>





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

    h2 {
        color: #333;
        margin-bottom: 20px;
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

    button {
        padding: 10px 20px;
        font-size: 16px;
        color: #fff;
        background-color: #007bff;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        transition: background-color 0.3s;
    }

    button:hover {
        background-color: #0056b3;
    }

    .non-sampling-search {
        background-color: #fff;
        padding: 15px;
        border-radius: 4px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }

    .non-sampling-search p {
        margin-bottom: 10px;
        color: #666;
    }
</style>



