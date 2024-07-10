


<script lang="ts">

  import { API_ENDPOINTS, constructUrl } from '../utils/api.ts'; // api helper function
  import { page } from '$app/stores'  // this is the function to import if you want to use locals' value
  import { get } from 'svelte/store'; // the correct way to retrieve locals values in .ts file

  import { writable } from 'svelte/store';
  import { unsavedChanges } from '$lib/utils/vars';
  import { loadBase64Font, addImageToPDF, generatePDF } from '$lib/utils/pdf.ts';

  export let results: any[] = [];
  export let deepCopiedResults: any[] = [];

  export let keysToExclude: string[] = ['image_url', 'categories', 'tags'];
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
    let removeClickCounts = writable({}); // To track remove button clicks
    let selectedForRemoval = writable({}); // To track selected keys for removal

    function filterDisplayedKeys(result) {
        const filteredResult = {};
        for (const key in result) {
            if (!keysToExclude.includes(key)) {
                filteredResult[key] = result[key];
            }
        }
        return filteredResult;
    }

    async function generatePDFWrapper() {
        await generatePDF(results, content);
    }

    function addForm(index: number) {
        displayedForms.update(forms => {
            if (!forms[index]) {
                forms[index] = [];
            }
            forms[index].push({ key: '', value: '', isRemove: false });
            return forms;
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
    }

    function lessForm(index: number) {
        displayedForms.update(forms => {
            if (!forms || !forms[index] || forms[index].length === 0) {
                console.error("Attempt to remove a form from an uninitialized index or empty forms array.");
                return forms;
            }
            const lastForm = forms[index].pop();
            if (lastForm && lastForm.isRemove) {
                removeClickCounts.update(counts => {
                    counts[index] = (counts[index] || 1) - 1;
                    return counts;
                });
            }
            if (forms[index].length === 0) {
                delete forms[index];
            }
            return forms;
        });

        selectedForRemoval.update(selections => {
            delete selections[index];
            return selections;
        });
    }

    function clearForms(index: number) {
        displayedForms.update(forms => {
            if (forms[index]) {
                forms[index] = [];
            }
            return forms;
        });

        removeClickCounts.update(counts => {
            counts[index] = 0;
            return counts;
        });

        selectedForRemoval.update(selections => {
            selections[index] = [];
            return selections;
        });
    }




    function updateForm(index: number, entryIndex: number, field: string, value: string) {
        displayedForms.update(forms => {
            if (forms[index] && forms[index][entryIndex]) {
                if (field === 'value' && forms[index][entryIndex].isDate) {
                    // Convert the date value to a suitable format if necessary
                    const dateValue = new Date(value).toISOString().split('T')[0];
                    forms[index][entryIndex][field] = dateValue;
                } else {
                    forms[index][entryIndex][field] = value;
                }
            }
            return forms;
        });
    }




    function toggleDateInput(index: number, entryIndex: number) {
        displayedForms.update(forms => {
            if (forms[index] && forms[index][entryIndex]) {
                forms[index][entryIndex].isDate = !forms[index][entryIndex].isDate;
                if (forms[index][entryIndex].isDate) {
                    forms[index][entryIndex].key = 'delivery_date';
                    forms[index][entryIndex].value = ''; // Clear the value when toggling to date
                } else {
                    forms[index][entryIndex].key = '';
                    forms[index][entryIndex].value = ''; // Clear the value when toggling to text
                }
            }
            return forms;
        });
    }



    function updateResults(index: number) {
        const user = get(page).data.user;

        if (user) {
            const formData = $displayedForms[index] || [];
            const updates = formData.reduce((acc, curr) => {
                if (curr.key && curr.value && !curr.isRemove) {
                    acc[curr.key] = curr.value;
                } else if (curr.key && curr.isRemove) {
                    delete results[index][curr.key];
                }
                return acc;
            }, {});

            console.log("Original deepCopiedResults:", deepCopiedResults);

            results[index] = { ...results[index], ...updates };

            // Handle modifiedBy field
            if (results[index].modifiedBy) {
                if (Array.isArray(results[index].modifiedBy)) {
                    results[index].modifiedBy.push(user);
                } else {
                    results[index].modifiedBy = [results[index].modifiedBy, user];
                }
            } else {
                results[index].modifiedBy = [user];
            }

            console.log("Updated results:", results);

            clearForms(index);
            unsavedChanges.set(true);
        } else {
            console.log("undefined user");
        }
    }



    function arraysEqual(a, b) {
        a = JSON.stringify(a);
        b = JSON.stringify(b);

        return a === b;
    }


    function countRemovableKeys(result) {
        return Object.keys(result).filter(key => !keysToExclude.includes(key)).length;
    }

    function canRemoveKeys(index) {
        const result = results[index];
        const removableKeysCount = countRemovableKeys(result);
        const formData = $displayedForms[index] || [];
        const existingRemoves = formData.filter(form => form.isRemove).length;
        return removableKeysCount > existingRemoves;
    }

    $: canRemove = results.map((result, index) => {
        const formData = $displayedForms[index] || [];
        const existingRemoves = formData.filter(form => form.isRemove).length;
        const removableKeysCount = countRemovableKeys(result);
        return removableKeysCount > existingRemoves;
    });




    // after push to the database, remmeber to make a blinking realtime effect showing the unique identifier for a side tab 
    // mostly they don't need to use that immediately so user windows' update could use traditional way: fetch responds 
    // but if they want to use that immediately, they can copy from the blinking tab


    async function pushChangesToBackend() {
        try{
            if (!arraysEqual(deepCopiedResults, results)) {
                console.log("Pushing changes to the database:", results);

                // results is an array, need to convert into JSON object for sending, but still backend will receive array
                // create api endpoint: original url ('http://localhost:5000/upload/api/upload_sample')
                const response = await fetch(API_ENDPOINTS.UPLOAD_SAMPLE, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(results), // convert the result to a JSON object
                });

                if (!response.ok) {
                    throw new Error('Failed to upload sample data');
                }

                unsavedChanges.set(false);
                const sampling_response = await response.json();
                console.log(sampling_response.message, ":", sampling_response.sample_token)

            } else {
                console.log("No changes to push");
            }
        } catch (error) {
            console.error("Caught unexpected error:", error.message)
        }
    }






</script>

<div id="result">
    {#if results.length > 0}
        {#each results as result, index}
            <h3>{content}</h3>
            <div class="result-container">
                <pre>{JSON.stringify(filterDisplayedKeys(result), null, 2)}</pre>
                {#if result.image_url}
                    <img src={result.image_url} alt="searched_image" onerror="this.onerror=null;this.src='fallback-image-url';">
                {/if}
            </div>
            <button class="btn" on:click={() => addForm(index)}>Add</button>
            {#if canRemove[index]}
                <button class="btn" on:click={() => removeKey(index)}>Remove</button>
            {/if}
            {#if $displayedForms[index]}
                {#each $displayedForms[index] as form, entryIndex}
                    <div>
                        <form>

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
                                <label for={`key-${index}-${entryIndex}`}>Key:</label>
                                <input id={`key-${index}-${entryIndex}`} type="text" on:input={e => updateForm(index, entryIndex, 'key', e.target.value)} value={form.key} readonly={form.isDate} />
                                <label for={`value-${index}-${entryIndex}`}>Value:</label>
                                <input id={`value-${index}-${entryIndex}`} type={form.isDate ? 'date' : 'text'} on:input={e => updateForm(index, entryIndex, 'value', e.target.value)} value={form.value} />

                                <label class="custom-checkbox">
                                    <input type="checkbox" on:click={() => toggleDateInput(index, entryIndex)} checked={form.isDate} />
                                    <span class="outer-circle">
                                        <span class="inner-circle"></span>
                                    </span>
                                    Date Type
                                </label>
                            {/if}

                        </form>
                    </div>
                {/each}
            {/if}
            <button class="btn" on:click={() => updateResults(index)}>Update</button>
            <button class="btn" on:click={() => lessForm(index)}>Cancel</button>
        {/each}
        <div>
            <br>
            <hr>
            <button class="btn" on:click={pushChangesToBackend}>Push Changes</button>
            <button class="btn" on:click={generatePDFWrapper}>Download PDF</button>
        </div>
    {:else}
        <p>No results found</p>
    {/if}
</div>





<style>
    .result-container {
        margin-top: 10px;
        width: 100%;
    }
    img {
        max-width: 70%;
        height: auto;
        display: block;
        margin-top: 10px;
    }
    .btn {
        margin-top: 20px;
    }

    .custom-checkbox {
        display: inline-block;
        position: relative;
        padding-left: 35px;
        margin-top: 20px;
        cursor: pointer;
        font-size: 16px;
        user-select: none;
    }

    .custom-checkbox input {
        position: absolute;
        opacity: 0;
        cursor: pointer;
        height: 0;
        width: 0;
    }

    .outer-circle {
        position: absolute;
        top: 0;
        left: 0;
        height: 20px;
        width: 20px;
        background-color: transparent;
        border: 2px solid #ccc;
        border-radius: 50%;
        box-shadow: 0 0 3px rgba(0, 0, 0, 0.2);
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .inner-circle {
        height: 12px;
        width: 12px;
        border: 2px solid #ccc;
        background-color: transparent;
        border-radius: 50%;
        transition: background-color 0.3s;
    }

    .custom-checkbox input:checked ~ .outer-circle .inner-circle {
        background-color: #2196F3;
    }
</style>





<!-- <script lang="ts"> -->

<!--     // !!!!!!!!!!!!!!!! later make the adding image and PDF generation function into a function, method not component for importing, so you only need to pass the size variable value to the function, this component could be a collection of different drawing function, like for tables, and for images, etc !!!!!!!!!!!!!!!! -->
<!--     // and maybe rename this component to where you can modify the display content, something like that -->
<!--     import jsPDF from "jspdf"; -->
<!--     // import html2canvas from "html2canvas"; -->
<!--     import { Base64Font } from "$lib/components/data/font.ts"; -->

<!--     // results variable prop  -->
<!--     // 1) creating a deep copy where the copy will serve as a static reference point for things like before-and-after comparisons  -->
<!--     //    and isn’t expected to be reassigned, const should be used -->
<!--     // 2) In scenarios where reassignment might be necessary,  -->
<!--     //    such as updating the reference to point to new data, let would be the correct choice. -->
<!--     export let results: any[] = []; -->
<!--     export let deepCopiedResults: any[] = []; -->
<!--     // deep copy of the results variable passed in, deep copy use different address reference compared to shallow copy  -->
<!--     // so make sure modifying the shallow copy of original results doesn't affect the copy itself -->
<!--     // choice of let and const:  -->
<!--      -->

<!--     // keys to exclude for displaying -->
<!--     export let keysToExclude: string[] = [ 'image_url', 'categories', 'tags', 'delivery_date' ]; -->

<!--     // text content for the printed PDF -->
<!--     let content: string = ` -->
<!--         Marks & Order Nos.(标志及订单号码)\n -->
<!--         Description & Specifications (描述及规格)\n -->
<!--         Unit Price (单价)\n -->
<!--         Total Price (总值)\n -->
<!--         H.S.CODE (商品编码)\n -->
<!--         From 由\n -->
<!--         To 至 -->
<!--     `; -->


<!--     function filterDisplayedKeys(result) { -->
<!--         const filteredResult = {}; -->
<!--         // Iterate over each key in the result object -->
<!--         for (const key in result) { -->
<!--             // Exclude keys that are in the keysToExclude list -->
<!--             if (!keysToExclude.includes(key)) { -->
<!--                 filteredResult[key] = result[key]; -->
<!--             } -->
<!--         } -->
<!--         return filteredResult; -->
<!--     } -->


<!--     function loadBase64Font(doc: jsPDF) { -->
<!--         doc.addFileToVFS("NotoSerifSC-Light.ttf", Base64Font); -->
<!--         doc.addFont("NotoSerifSC-Light.ttf", "NotoSerifSC", "normal"); -->
<!--         doc.setFont("NotoSerifSC"); -->
<!--     } -->



<!--     async function addImageToPDF(doc: jsPDF, imageUrl: string, x: number, y: number, maxWidth: number, maxHeight: number) { -->
<!--         return new Promise((resolve, reject) => { -->
<!--             const img = new Image(); -->
<!--             img.crossOrigin = "Anonymous";  // This may be necessary depending on CORS policy -->
<!--             img.onload = function() { -->
<!--                 // Calculate the best fit aspect ratio -->
<!--                 const ratio = Math.min(maxWidth / img.naturalWidth, maxHeight / img.naturalHeight); -->
<!--                 const newWidth = img.naturalWidth * ratio; -->
<!--                 const newHeight = img.naturalHeight * ratio; -->

<!--                 // Create a canvas that matches the image's natural size for high-quality scaling -->
<!--                 const canvas = document.createElement('canvas'); -->
<!--                 canvas.width = img.naturalWidth; -->
<!--                 canvas.height = img.naturalHeight; -->
<!--                 const ctx = canvas.getContext('2d'); -->
<!--                 ctx.drawImage(img, 0, 0, img.naturalWidth, img.naturalHeight); -->

<!--                 // Convert to data URL at the natural resolution -->
<!--                 const imgData = canvas.toDataURL('image/jpeg'); -->

<!--                 // Add to PDF at scaled dimensions -->
<!--                 doc.addImage(imgData, 'JPEG', x, y, newWidth, newHeight); -->
<!--                 resolve(); -->
<!--             }; -->
<!--             img.onerror = function() { -->
<!--                 reject(new Error('Image could not be loaded')); -->
<!--             }; -->
<!--             img.src = imageUrl; -->
<!--         }); -->
<!--     } -->



<!--     async function generatePDF() { -->
<!--         const doc = new jsPDF('p', 'mm', 'a4'); -->
<!--         loadBase64Font(doc); -->
<!--         doc.setFontSize(7);  // Adjust font size as necessary -->

<!--         let currentY = 10;  // Start Y position for the first item -->
<!--         const margin = 10; -->
<!--         const imgMaxWidth = 70;  // Image width -->
<!--         const imgMaxHeight = imgMaxWidth * 3/4;  // Image height, maintaining a 4:3 aspect ratio -->
<!--         const textWidth = 80;  // Text block width -->

<!--         for (const result of results) { -->
<!--             // Ensure the image_url exists before trying to add it -->
<!--             if (result.image_url) { -->
<!--                 // Load and add the image to the PDF -->
<!--                 await addImageToPDF(doc, result.image_url, margin + textWidth + margin, currentY, imgMaxWidth, imgMaxHeight); -->
<!--             } -->

<!--             // Add text directly aligned with the top of the image -->
<!--             doc.text(content, margin, currentY);  // Set the y-coordinate exactly equal to currentY -->

<!--             // Determine the block height, which is the space the text and image take up -->
<!--             let blockHeight = imgMaxHeight + margin;  // Usually the image height plus some margin -->
<!--             currentY += blockHeight;  // Update currentY to move to the next block -->

<!--             // Check if the next block would overflow the current page -->
<!--             if (currentY + blockHeight > doc.internal.pageSize.getHeight() - margin) { -->
<!--                 doc.addPage(); -->
<!--                 currentY = 10;  // Reset Y position for the new page -->
<!--             } -->
<!--         } -->

<!--         doc.save("results.pdf");  // Save the generated PDF -->
<!--     } -->



<!--     // handling the adding and removing on specific json item -->
<!--     import { writable } from 'svelte/store'; -->
<!--     import { get } from 'svelte/store'; -->

<!--     let displayedForms = writable({}); // Uses an object to store form data by index -->

<!--     function addForm(index: number) { -->
<!--         displayedForms.update(forms => { -->
<!--             if (!forms[index]) { -->
<!--                 forms[index] = []; // Initialize an array if it doesn't exist -->
<!--             } -->
<!--             forms[index].push({ key: '', value: '' }); // Adds a new form entry to the stack -->
<!--             return forms; -->
<!--         }); -->
<!--     } -->



<!--     // map the selected result (key) from the select tag -->
<!--     let selectedKeys = {}; -->


<!--     function removeKey(index: number) { -->
<!--         if (selectedKeys[index] && results[index][selectedKeys[index]]) { -->
<!--             delete results[index][selectedKeys[index]];     // Remove the key-value pair, direcly modify the results array -->
<!--             results = results.slice();                      // Reassign results to trigger reactivity -->
<!--             selectedKeys[index] = '';                       // Reset the selected key after removal -->
<!--         } -->
<!--     } -->


<!--     function lessForm(index: number) { -->
<!--         displayedForms.update(forms => { -->
<!--             // Check if 'forms' is initialized and has entries at the specified index -->
<!--             // make sure this removeForm function specifically work if there are existing form created by addForm button -->
<!--             // because all form entries will be clear up after update button,  -->
<!--             // force it to only work with situation when there have existing forms -->
<!--             if (!forms || !forms[index] || forms[index].length === 0) { -->
<!--                 console.error("Attempt to remove a form from an uninitialized index or empty forms array."); -->
<!--                 return forms;  // Return the unchanged forms object if there's an error -->
<!--             } -->
<!--              -->
<!--             // If the conditions are met, remove the last form entry -->
<!--             // stack: first in last out -->
<!--             forms[index].pop(); -->
<!--              -->
<!--             // Clean up if no forms are left at the index -->
<!--             if (forms[index].length === 0) { -->
<!--                 delete forms[index]; -->
<!--             } -->
<!--              -->
<!--             return forms; -->
<!--         }); -->
<!--     } -->


<!--     function clearForms(index: number) { -->
<!--         displayedForms.update(forms => { -->
<!--             if (forms[index]) { -->
<!--                 forms[index] = []; // Clear all form entries for this index -->
<!--             } -->
<!--             return forms; -->
<!--         }); -->
<!--     } -->


<!--     function updateForm(index: number, entryIndex: number, field: string, value: string) { -->
<!--         displayedForms.update(forms => { -->
<!--             if (forms[index] && forms[index][entryIndex]) { -->
<!--                 forms[index][entryIndex][field] = value; // Updates the specific field -->
<!--             } -->
<!--             return forms; -->
<!--         }); -->
<!--     } -->


<!--     function updateResults(index: number) { -->

<!--         const formData = $displayedForms[index] || []; -->
<!--         const updates = formData.reduce((acc, curr) => { -->
<!--             if (curr.key && curr.value) acc[curr.key] = curr.value; -->
<!--             return acc; -->
<!--         }, {}); -->
<!--          -->
<!--         // when you console log the results (array or object) in async or reactive contexts  -->
<!--         // this logging can be understood as a snapshot, but when you expand the snapshot in the console  -->
<!--         // it automatically update, so if you want to see the logging(snapshot) at certain step  -->
<!--         // don't access the whole object or array, instead accessing to index or stringify -->
<!--         // console.log("before:", JSON.stringify(results)); -->
<!--         // console.log("before:", results[index]) -->

<!--         console.log("Original deepCopiedResults:", deepCopiedResults); -->

<!--         results[index] = {...results[index], ...updates}; -->
<!--         // console.log("after:", results[index]) -->
<!--         console.log("Updated results:", results); -->

<!--         // Clear all form entries after updating the result -->
<!--         clearForms(index); -->
<!--     } -->

<!--     // compare result reminding user to push to the database  -->
<!--     function arraysEqual(a, b) { -->
<!--         // you have to stringify them, otherwise considered differently because snapshot time different -->
<!--         a = JSON.stringify(a) -->
<!--         b = JSON.stringify(b) -->

<!--         if (a === b) return true;                   // strictly equal, check if two arrays refer to the same reference, if not false -->
<!--         if (a == null || b == null) return false;   // if null then definitely false -->
<!--         if (a.length !== b.length) return false;    // check length -->

<!--         for (let i = 0; i < a.length; ++i) {        // sometime, array could have different reference but still be the same -->
<!--             if (a[i] !== b[i]) return false;        // so double check each value -->
<!--         } -->
<!--         return true; -->
<!--     } -->



<!--     function addBeforeUnloadListener() { -->
<!--       // Check if the window object is defined  -->
<!--         if (typeof window !== 'undefined') { -->
<!--             let unsavedChanges = false; -->

<!--         // Add an event listener for the beforeunload event -->
<!--         window.addEventListener('beforeunload', (e) => { -->
<!--             if (unsavedChanges) { -->
<!--                 e.preventDefault(); // If you prevent default behavior in Mozilla browsers, the dialog box will always be displayed -->
<!--                 e.returnValue = ''; // Firefox requires returnValue to be set -->
<!--             } -->
<!--         }); -->

<!--         // Function to update the unsavedChanges flag when changes are made -->
<!--         function updateUnsavedChanges() { -->
<!--             unsavedChanges = !arraysEqual(deepCopiedResults, results); -->
<!--         } -->

<!--         // Call updateUnsavedChanges whenever results are modified -->
<!--         $: updateUnsavedChanges(); -->
<!--       } -->
<!--     } -->

<!--     // Call the addBeforeUnloadListener function -->
<!--     addBeforeUnloadListener(); -->




<!--     // when you push changes: -->
<!--     // also when you update, add unique identifier to each json document within this sampling step  -->
<!--     // because every sampling document as a whole will be store into a separate collections for record -->
<!--     // oh, maybe give a key to the json document array and another key for unique identifier will be better, you don't need to insert to  -->
<!--     // each json document everytime. Is just when you do the search later you have to match item inside the nested json array -->
<!--     // if you already have that kind of search, that's fine -->
<!--     // also, you need to notify users, or maybe store the unique identifier into their user data for later search  -->
<!--     // design this unique identifier carefully, I think it needs attentions if better for search -->
<!--     // this make the other security check necessary like a delivery_date, because when user data break/lost, delivery_date help find sampling list -->
<!--     function pushChangesToDatabase() { -->
<!--         if (!arraysEqual(deepCopiedResults, results)) { -->
<!--         // Push the changes to the backend database -->
<!--         console.log("Pushing changes to the database:", results); -->
<!--         // Replace the console.log with your actual API call -->
<!--       } else { -->
<!--         console.log("No changes to push"); -->
<!--       } -->
<!--     } -->


<!--     // dollar sign $, make the condition reactive state, constantly track the function after collon:  -->
<!--     // which is "if (!arraysEqual(oldResults, results))" -->
<!--     // if yes, execute what's inside; right now it's not so smart for the checking -->
<!--     // $: if (!arraysEqual(deepCopiedResults, results)) { -->
<!--     //     console.log("Results have changed. Updating database..."); -->
<!--     // } -->

<!-- </script> -->


<!-- <div id="result"> -->
<!--     {#if results.length > 0} -->
<!--         {#each results as result, index} -->
<!--             <h3>{content}</h3> -->
<!--             <div class="result-container"> -->
<!--                 <pre>{JSON.stringify(filterDisplayedKeys(result), null, 2)}</pre> -->
<!--                 <!-- <pre>{JSON.stringify(result, null, 2)}</pre> --> 
<!--                 {#if result.image_url} -->
<!--                     <img src={result.image_url} alt="searched_image" onerror="this.onerror=null;this.src='fallback-image-url';"> -->
<!--                 {/if} -->
<!--             </div> -->
<!--             <button class="btn" on:click={() => addForm(index)}>add</button> -->
<!--             <!-- <input type="date" id="delivery_date" name="delivery_date" required>  --> 
<!--             <!-- think of this, whether you need to add delivery date selection, or just let them type --> 
<!--             <select bind:value={selectedKeys[index]}> -->
<!--                 <option value="">Remove a Key</option> -->
<!--                 {#each Object.keys(result) as key} -->
<!--                     {#if !keysToExclude.includes(key)} -->
<!--                         <option value={key}>{key}</option> -->
<!--                     {/if} -->
<!--                 {/each}             -->
<!--             </select> -->
<!--             <button class="btn" on:click={() => removeKey(index)}>Remove</button> -->
<!--             {#if $displayedForms[index]} -->
<!--                 {#each $displayedForms[index] as form, entryIndex} -->
<!--                     <div> -->
<!--                         <form> -->
<!--                             <label for={`key-${index}-${entryIndex}`}>Key:</label> -->
<!--                             <input id={`key-${index}-${entryIndex}`} type="text" on:input={e => updateForm(index, entryIndex, 'key', e.target.value)} value={form.key}> -->
<!--                             <label for={`value-${index}-${entryIndex}`}>Value:</label> -->
<!--                             <input id={`value-${index}-${entryIndex}`} type="text" on:input={e => updateForm(index, entryIndex, 'value', e.target.value)} value={form.value}> -->
<!--                         </form> -->
<!--                     </div> -->
<!--                 {/each} -->
<!--             {/if} -->
<!--             <button class="btn" on:click={() => updateResults(index)}>Update</button> -->
<!--             <button class="btn" on:click={() => lessForm(index)}>Cancel</button> -->
<!--         {/each} -->
<!--         <div> -->
<!--             <br> -->
<!--             <hr> -->
<!--             <button class="btn" on:click={pushChangesToDatabase}>Push Changes</button> -->
<!--             <button class="btn" on:click={generatePDF}>Download PDF</button> -->
<!--         </div> -->
<!--     {:else} -->
<!--         <p>No results found</p> -->
<!--     {/if} -->
<!-- </div> -->



<!-- <style> -->
<!--     .result-container { -->
<!--         margin-top: 10px; -->
<!--         width: 100%; -->
<!--     } -->
<!--     img { -->
<!--         max-width: 70%; -->
<!--         height: auto; -->
<!--         display: block; -->
<!--         margin-top: 10px; -->
<!--     } -->
<!--     .btn { -->
<!--         margin-top: 20px; -->
<!--     } -->
<!-- </style> -->

