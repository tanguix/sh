
<script lang="ts">
    import { writable } from 'svelte/store';    // reactive method by default
    import { API_ENDPOINTS, constructUrl } from '$lib/utils/api'; // api helper function


    // user-defined type for additional field (key: value) in json
    type Field = {
        id: number;
        key: string;
        value: string;
    };

    // declare Universial Type that could have array of attributes 
    // Category and Tag
    type Item = {
        id: number;
        value: string;
    };

    // create writtable array object for storing, an array of certain type
    let fields = writable<Field[]>([]);             // Field array
    let tags = writable<Item[]>([]);                // Tag array
    let categories = writable<Item[]>([]);          // Category array
    let imageFile: File | null = null;              // File API Interface, either be File or null, and it's null initially
    let imagePath: string = '';                     // save image path (just filename)
    let imagePreviewUrl: string = '';               // store the image preview URL object



    // ---------------------------------------------- Add/Remove Function ----------------------------------------------
    // store is svelte class, allows both reading and updating its value, for managing states across svelte page 
    // writable store is one type of store
    function addItem(store) {                       // takes in store object 
        store.update(currentItems => [              // update is a writable store method, takes function as parameter
            ...currentItems,                        // ...currentItems: a shallow copy of the store array from currentItems
            { id: Date.now(), value: '' }           // ensure existing/original array is immutate
        ]);
    }

    // function takes in an id for locating the object (key: value)
    // filter() method remove items in the array if condition evaluate to false
    // click "remove" button activate evaluation(for field, tag, category)
    function removeItem(store: any, id: number) {
        store.update(currentItems => currentItems.filter(item => item.id !== id));
    }


    // ---------------------------------------- Image Drag-Drop Area (event) ----------------------------------------
    // 1) event is an object, which is automatically passed to event-handler function when occurs
    // 2) event.target refers to the element that triggered the event, it's a property of the event object
    // 3) Default HTML events: dragover, drop, keydown, click, etc 
    // 4) e.g. the 'dragover' event is fired when a dragged element is being dragged over a valid drop target(div tag)
    // 5) e.g. the 'keydown' event is fired when a key is pressed down.
    function handleFileSelect(event: Event) {               // event handle function, takes in event, cast to a specific type
        const target = event.target as HTMLInputElement;    // "HTMLInputElement" type for safety check, event.target is
                                                            // expected to be ('<input type="file"') = "browse file" button
        if (target.files && target.files.length > 0) {          // check file existence
            imageFile = target.files[0];                        // assign image value to imageFile
            imagePath = target.files[0].name;                   // assign image name
            imagePreviewUrl = URL.createObjectURL(imageFile);   // create image preview object
        }
    }

    // Function to handle file drop
    function handleDrop(event: DragEvent) {                     // drag event handler
        event.preventDefault();                                 // browser by default doesn't not allow drag behavior, 
                                                                // so prevent default
        if (event.dataTransfer && event.dataTransfer.files.length > 0) {    // event.dataTransfer == <on:drop>
            imageFile = event.dataTransfer.files[0];
            imagePath = imageFile.name;
            imagePreviewUrl = URL.createObjectURL(imageFile);
        }
    }

    // allow dragging
    function handleDragOver(event: DragEvent) {
        event.preventDefault();
    }

    // Function to handle click event for file input, above is for handling select
    function handleClick() {
        const fileInput = document.getElementById('image') as HTMLInputElement;
        fileInput.click();
    }

    // Function to handle key down event
    function handleKeyDown(event: KeyboardEvent) {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            handleClick();
        }
    }

    // ---------------------------------------------- API request ----------------------------------------------
    // Function to send sample data to the backend
    async function sendSampleData(combinedFormData: FormData) {
        // create api endpoint
        const response = await fetch(API_ENDPOINTS.UPLOAD_DATA, {
            method: 'POST',
            body: combinedFormData, 
        });

        if (!response.ok) {
            throw new Error('Failed to upload sample data');
        }

        return await response.json();
    }

    // Form Submission handling function
    function handleSubmit(event: Event) {
        event.preventDefault();                         // prevent default reload after submitted form
        const form = event.target as HTMLFormElement;
        const formData = new FormData(form);

        // check if imageFile exist, this is a "File" type Web API Interface object 
        // "File" type can be sent over the network as part of multipart/form-data, not directly as json (json is text)
        if (imageFile) {
            formData.append('image', imageFile);
        }

        // Record is a default type
        const additionalFields: Record<string, string> = {};
        fields.subscribe(currentFields => {             // subscribe: writable method allow you to listen to change
            currentFields.forEach(field => {            // for loop in python: "for field in currentFields:"
                if (field.key) {                        // if exist a new key, add it to the array for appending
                    additionalFields[field.key] = field.value;
                }
            });
        })();

        // for Tags, array of string
        const additionalTags: string[] = [];
        tags.subscribe(currentTags => {
            currentTags.forEach(tag => {
                if (tag.value) {
                    additionalTags.push(tag.value);
                }
            });
        })();

        // For Category, array of string
        const additionalCategories: string[] = [];
        categories.subscribe(currentCategories => {
            currentCategories.forEach(category => {
                if (category.value) {
                    additionalCategories.push(category.value);
                }
            });
        })();

        // retrieve original Tags, and trims(remove) whitespace (first entered Tag)
        const originalTags = formData.get('tag') ? 
            formData.get('tag').toString().split(',').map(tag => tag.trim()) : [];
        // retrieve original category (first entered category)
        const originalCategories = formData.get('category') ? 
            formData.get('category').toString().split(',').map(category => category.trim()) : [];

        // conact them in a unified array
        const allTags = originalTags.concat(additionalTags);
        const allCategories = originalCategories.concat(additionalCategories);

        // append them into multipart/formdata
        formData.append('tags', JSON.stringify(allTags));
        formData.append('categories', JSON.stringify(allCategories));
        formData.append('additional_fields', JSON.stringify(additionalFields));

        // send formData
        sendSampleData(formData)
            .then(response => {
                console.log('Upload successful:', response);
            })
            .catch(error => {
                console.error('Upload failed:', error);
            });

        // reset all the field entered, by default page will refresh after form sbumission, but we had prevent that
        // so mannully reset all entries
        form.reset();
        fields.set([]);
        tags.set([]);
        categories.set([]);
        imageFile = null;
        imagePath = '';
        imagePreviewUrl = '';
    }
</script>


<!----------------------------------------------------- HTML ----------------------------------------------------->


<!-- the big form to submit -->
<form action="?/upload" method="POST" on:submit={handleSubmit} enctype="multipart/form-data">

    <!-- file browsing div -->
    <div class="browser-file">
        <label for="image">Upload Image:</label>
        <input class="input" type="file" id="image" name="image_file" accept="image/*" on:change={handleFileSelect} required>
        <button type="button" on:click={handleClick}>Browse</button>
    </div>

    <!-- drag and drop area div -->
    <div 
        class="drag-drop-area {imagePreviewUrl ? 'highlight' : ''}"
        role="button"
        tabindex="0"
        on:click={handleClick}
        on:keydown={handleKeyDown}
        on:drop={handleDrop} 
        on:dragover={handleDragOver} 
    >
        <div>
            {#if imagePreviewUrl}
                <div class="image-preview">
                    <img src={imagePreviewUrl} alt="preview file" />
                </div>
            {/if}
            {#if imagePath}
                <p>{imagePath}</p>
            {/if}
            {!imagePath && !imagePreviewUrl ? 'Drag and drop an image here or click to select.' : ''}
        </div>
    </div>

    <!-- category entry div -->
    <div>
        <label for="category">Categories:</label>
        <input type="text" id="category" name="category" required>
        <button type="button" on:click={() => addItem(categories)}>add</button>
    </div>

    {#each $categories as category (category.id)}
        <div class="indent">
            <label for="category-{category.id}">new cat:</label>
            <input type="text" id="category-{category.id}" bind:value={category.value} placeholder="Category">

            <button type="button" on:click={() => removeItem(categories, category.id)}>Remove</button>
        </div>
    {/each}

    <!-- Tag entry div -->
    <div>
        <label for="tag">Tags:</label>
        <input type="text" id="tag" name="tag" required>
        <button type="button" on:click={() => addItem(tags)}>add</button>
    </div>

    {#each $tags as tag (tag.id)}
        <div class="indent">
            <label for="tag-{tag.id}">new tag:</label>
            <input type="text" id="tag-{tag.id}" bind:value={tag.value} placeholder="Tag">

            <button type="button" on:click={() => removeItem(tags, tag.id)}>Remove</button>
        </div>
    {/each}

    <!-- all other single entry div -->
    <div>
        <label for="reference_no">Reference Number:</label>
        <input type="text" id="reference_no" name="reference_no" required>
    </div>
    <!-- <div> -->
    <!--     <label for="quantity">Quantity:</label> -->
    <!--     <input type="text" id="quantity" name="quantity" required> -->
    <!-- </div> -->


    <!-- additional field div -->
    {#each $fields as field (field.id)}
        <div>
            <label for="key-{field.id}">Feature:</label>
            <input type="text" id="key-{field.id}" bind:value={field.key} placeholder="Field name">

            <label for="value-{field.id}">Value:</label>
            <input type="text" id="value-{field.id}" bind:value={field.value} placeholder="Value">

            <button type="button" on:click={() => removeItem(fields, field.id)}>Remove</button>
        </div>
    {/each}
    <button type="button" on:click={() => addItem(fields)}>Add Field</button>

    <!-- submission button -->
    <button type="submit">Submit</button>
</form>

<style>

    form {
        font-family: "Ubuntu";
    }

    div {
        padding: 5px;
    }

    .indent {
        margin: 0 0 0 1.4rem;
    }

    .input {
        display: none; /* by default input tag will come with Choose button, disable it */
    }

    .browser-file {
        /* border: solid; */
    }


    .drag-drop-area {
        border: 2px dashed #ccc;
        text-align: center;
        margin-bottom: 10px;
        position: relative;
        cursor: pointer;
        transition: border-color 0.3s, background-color 0.3s;
        width: 30rem;
        height: auto;
        display: flex;
        align-items: center; /* Center items vertically */
        justify-content: center; /* Center items horizontally */
    }


    .drag-drop-area:hover {
        border-color: #007bff;
        background-color: #e7f3ff;
    }

    .image-preview {
        display: flex;
        align-items: center;
        justify-content: center;
        max-width: 80%;
        max-height: 80%;
    }
    


</style>
