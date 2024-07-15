
<script lang="ts">
    import { writable } from 'svelte/store';
    import { API_ENDPOINTS, constructUrl } from '$lib/utils/api';

    type Field = {
        id: number;
        key: string;
        value: string;
    };

    type Item = {
        id: number;
        value: string;
    };

    let fields = writable<Field[]>([]);
    let tags = writable<Item[]>([]);
    let categories = writable<Item[]>([]);
    let imageFile: File | null = null;
    let imagePath: string = '';
    let imagePreviewUrl: string = '';

    // New variables for additional images
    let additionalImages: File[] = [];
    let additionalImagePreviews: string[] = [];

    function addItem(store) {
        store.update(currentItems => [
            ...currentItems,
            { id: Date.now(), value: '' }
        ]);
    }

    function removeItem(store: any, id: number) {
        store.update(currentItems => currentItems.filter(item => item.id !== id));
    }

    function handleFileSelect(event: Event) {
        const target = event.target as HTMLInputElement;
        if (target.files && target.files.length > 0) {
            imageFile = target.files[0];
            imagePath = target.files[0].name;
            imagePreviewUrl = URL.createObjectURL(imageFile);
        }
    }

    function handleDrop(event: DragEvent) {
        event.preventDefault();
        if (event.dataTransfer && event.dataTransfer.files.length > 0) {
            imageFile = event.dataTransfer.files[0];
            imagePath = imageFile.name;
            imagePreviewUrl = URL.createObjectURL(imageFile);
        }
    }

    function handleDragOver(event: DragEvent) {
        event.preventDefault();
    }

    function handleClick() {
        const fileInput = document.getElementById('image') as HTMLInputElement;
        fileInput.click();
    }

    function handleKeyDown(event: KeyboardEvent) {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            handleClick();
        }
    }

    // New functions for additional images
    function handleAdditionalFileSelect(event: Event) {
        const target = event.target as HTMLInputElement;
        if (target.files) {
            for (let i = 0; i < target.files.length; i++) {
                if (target.files[i].type.startsWith('image/')) {
                    additionalImages = [...additionalImages, target.files[i]];
                    additionalImagePreviews = [...additionalImagePreviews, URL.createObjectURL(target.files[i])];
                }
            }
        }
    }

    function handleAdditionalDrop(event: DragEvent) {
        event.preventDefault();
        if (event.dataTransfer && event.dataTransfer.files) {
            for (let i = 0; i < event.dataTransfer.files.length; i++) {
                const file = event.dataTransfer.files[i];
                if (file.type.startsWith('image/')) {
                    additionalImages = [...additionalImages, file];
                    additionalImagePreviews = [...additionalImagePreviews, URL.createObjectURL(file)];
                }
            }
        }
    }



    function removeAdditionalImage(event: Event, index: number) {
        event.stopPropagation();
        additionalImages = additionalImages.filter((_, i) => i !== index);
        additionalImagePreviews = additionalImagePreviews.filter((_, i) => i !== index);
    }



    async function sendSampleData(combinedFormData: FormData) {
        const response = await fetch(API_ENDPOINTS.UPLOAD_DATA, {
            method: 'POST',
            body: combinedFormData, 
        });

        if (!response.ok) {
            throw new Error('Failed to upload sample data');
        }

        return await response.json();
    }



    function handleSubmit(event: Event) {
        event.preventDefault();
        const form = event.target as HTMLFormElement;
        const formData = new FormData(form);

        if (imageFile) {
            formData.append('image', imageFile);
        }

        // Append additional images
        additionalImages.forEach((image, index) => {
            formData.append(`additional_image_${index}`, image);
        });

        const additionalFields: Record<string, string> = {};
        fields.subscribe(currentFields => {
            currentFields.forEach(field => {
                if (field.key) {
                    additionalFields[field.key] = field.value;
                }
            });
        })();

        const additionalTags: string[] = [];
        tags.subscribe(currentTags => {
            currentTags.forEach(tag => {
                if (tag.value) {
                    additionalTags.push(tag.value);
                }
            });
        })();

        const additionalCategories: string[] = [];
        categories.subscribe(currentCategories => {
            currentCategories.forEach(category => {
                if (category.value) {
                    additionalCategories.push(category.value);
                }
            });
        })();

        const originalTags = formData.get('tag') ? 
            formData.get('tag').toString().split(',').map(tag => tag.trim()) : [];
        const originalCategories = formData.get('category') ? 
            formData.get('category').toString().split(',').map(category => category.trim()) : [];

        const allTags = originalTags.concat(additionalTags);
        const allCategories = originalCategories.concat(additionalCategories);

        formData.append('tags', JSON.stringify(allTags));
        formData.append('categories', JSON.stringify(allCategories));
        formData.append('additional_fields', JSON.stringify(additionalFields));



        sendSampleData(formData)
            .then(response => {
                console.log('Upload successful:', response);
            })
            .catch(error => {
                console.error('Upload failed:', error);
            });

        form.reset();
        fields.set([]);
        tags.set([]);
        categories.set([]);
        imageFile = null;
        imagePath = '';
        imagePreviewUrl = '';
        additionalImages = [];
        additionalImagePreviews = [];
    }
</script>



<form action="?/upload" method="POST" on:submit={handleSubmit} enctype="multipart/form-data">
    <div class="upload-container">
        <div class="upload-left">
            <div class="browser-file">
                <label for="image">Upload Image:</label>
                <input class="input" type="file" id="image" name="image_file" accept="image/*" on:change={handleFileSelect} required>
                <button type="button" on:click={handleClick}>Browse</button>
            </div>

            <div 
                class="drag-drop-area {imagePreviewUrl ? 'highlight' : ''}"
                role="button"
                tabindex="0"
                on:click={handleClick}
                on:keydown={handleKeyDown}
                on:drop={handleDrop} 
                on:dragover={handleDragOver} 
            >
                <div class="image-preview-container">
                    {#if imagePreviewUrl}
                        <div class="image-preview">
                            <img src={imagePreviewUrl} alt="preview file" />
                        </div>
                    {/if}
                    {#if imagePath}
                        <p>{imagePath}</p>
                    {/if}
                    {!imagePath && !imagePreviewUrl ? '< main image >' : ''}
                </div>
            </div>

            <!-- New section for additional images -->
            <div class="additional-images">
                <h3>Additional Images:</h3>
                <div class="browser-file">
                    <label for="additional-images">Upload Additional Images:</label>
                    <input class="input" type="file" id="additional-images" name="additional_images" accept="image/*" on:change={handleAdditionalFileSelect} multiple>
                    <button type="button" on:click={() => document.getElementById('additional-images').click()}>Browse</button>
                </div>

                <div 
                    class="drag-drop-area additional-images-area"
                    role="button"
                    tabindex="0"
                    on:click={() => document.getElementById('additional-images').click()}
                    on:keydown={handleKeyDown}
                    on:drop={handleAdditionalDrop} 
                    on:dragover={handleDragOver} 
                >
                    {#if additionalImagePreviews.length > 0}
                        <div class="additional-images-container">
                            <div class="additional-image-previews">
                                {#each additionalImagePreviews as preview, index}
                                    <div class="additional-image-preview">
                                        <img src={preview} alt={`Additional image ${index + 1}`} />
                                        <button type="button" on:click={(event) => removeAdditionalImage(event, index)}>remove</button>
                                    </div>
                                {/each}
                            </div>
                        </div>
                    {:else}
                        <p>Drag and drop additional images here.</p>
                    {/if}
                </div>
            </div>
        </div>

        <div class="upload-right">
            <!-- Categories -->
            <div class="input-group">
                <div class="input-button-group">
                    <input type="text" id="category" name="category" placeholder="Categories" required>
                    <button type="button" on:click={() => addItem(categories)}>add</button>
                </div>
            </div>

            {#each $categories as category (category.id)}
                <div class="input-group indent">
                    <div class="input-button-group">
                        <input type="text" id="category-{category.id}" bind:value={category.value} placeholder="New category">
                        <button type="button" on:click={() => removeItem(categories, category.id)}>Remove</button>
                    </div>
                </div>
            {/each}

            <!-- Tags -->
            <div class="input-group">
                <div class="input-button-group">
                    <input type="text" id="tag" name="tag" placeholder="Tags" required>
                    <button type="button" on:click={() => addItem(tags)}>add</button>
                </div>
            </div>

            {#each $tags as tag (tag.id)}
                <div class="input-group indent">
                    <div class="input-button-group">
                        <input type="text" id="tag-{tag.id}" bind:value={tag.value} placeholder="New tag">
                        <button type="button" on:click={() => removeItem(tags, tag.id)}>Remove</button>
                    </div>
                </div>
            {/each}

            <!-- Reference Number -->
            <div class="input-group">
                <input type="text" id="reference_no" name="reference_no" placeholder="Reference Number" required>
            </div>

            <!-- Separator -->
            <hr class="separator">

            <!-- Additional Fields -->
            {#each $fields as field (field.id)}
                <div class="input-group additional-field">
                    <div class="feature-value-group">
                        <div class="input-label-group">
                            <input type="text" id="key-{field.id}" bind:value={field.key} placeholder="Field name">
                        </div>
                        <div class="input-label-group">
                            <input type="text" id="value-{field.id}" bind:value={field.value} placeholder="Value">
                        </div>
                    </div>
                    <button type="button" on:click={() => removeItem(fields, field.id)}>Remove</button>
                </div>
            {/each}
            <button type="button" on:click={() => addItem(fields)}>Add Field</button>
        </div>
    </div>

    <!-- submission button -->
    <div class="submit-button">
      <button type="submit">Submit</button>
    </div>
</form>

<style>
    form {
        font-family: "Ubuntu";
    }

    .upload-container {
        display: flex;
        gap: 2rem;
    }

    .upload-left, .upload-right {
        flex: 1;
    }

    .upload-right {
        padding-top: 3.5rem;
    }

    .input-group {
        margin-bottom: 1rem;
    }

    .input-button-group {
        display: flex;
        gap: 1rem;
    }

    .input-button-group input {
        flex-grow: 1;
    }

    .indent {
        margin-left: 1.4rem;
    }

    .additional-field {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .feature-value-group {
        display: flex;
        gap: 1rem;
    }

    .input-label-group {
        display: flex;
        flex-direction: column;
        flex: 1;
    }

    .input {
        display: none;
    }

    .browser-file {
        margin-bottom: 1rem;
    }

    .drag-drop-area {
        border: 2px dashed #ccc;
        text-align: center;
        padding: 2rem;
        cursor: pointer;
        transition: border-color 0.3s, background-color 0.3s;
    }

    .drag-drop-area:hover {
        border-color: #007bff;
        background-color: #e7f3ff;
    }

    .image-preview {
        max-width: 100%;
        margin-top: 1rem;
    }

    .image-preview img {
        max-width: 100%;
        height: auto;
    }


    .image-preview-container p {
        padding: 10px 0 0 0;
    }

    button {
        margin-top: 0.5rem;
        white-space: nowrap;
    }

    /* Styles for additional images */
    .additional-images {
        margin-top: 2rem;
    }

    .additional-images-area {
        min-height: 100px;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    .additional-images-container {
        display: flex;
        justify-content: center;
        max-width: 100%;
    }

    .additional-image-previews {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        justify-content: center;
    }

    .additional-image-preview {
        position: relative;
        width: 100px;
        height: 100px;
        overflow: hidden;
    }

    .additional-image-preview img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    .additional-image-preview button {
        position: absolute;
        bottom: 5px;
        right: 5px;
        background: rgba(0, 0, 0, 0.5);
        color: white;
        border: none;
        border-radius: 4px;
        padding: 2px 6px;
        font-size: 12px;
        line-height: 1.5;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }

    .additional-image-preview button:hover {
        background: rgba(0, 0, 0, 0.7);
    }

    .separator {
        border: 0;
        height: 1px;
        background: #ccc;
        margin: 2.5rem 0 1rem 0;
    }

    .additional-field {
        margin-top: 2rem;
    }

    .submit-button {
        display: flex;
        align-items: left;
        justify-content: left;
        margin: 0.5rem 0;
    }
</style>

